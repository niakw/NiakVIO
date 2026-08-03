#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from apply_provider_overrides import apply_overrides
from deep_repair_loop import persist_runtime_profiles
from runtime_repair import (
    compare_results,
    create_repair_candidate,
    matching_profiles,
    runtime_trigger_matches,
)


def metadata_only_result() -> dict:
    return {
        "key": "source:sample",
        "status": "provider_unreachable",
        "score": 0,
        "evidence": {
            "streams_playable": 0,
            "provider_server_accessible": False,
            "provider_server_successful_response": False,
            "fixture_status_counts": {"provider_unreachable": 1, "runtime_error": 0},
        },
        "tests": [
            {
                "status": "provider_unreachable",
                "stream_count": 0,
                "streams_returned": 0,
                "streams_playable": 0,
                "network_observations": [
                    {
                        "host": "metadata.example",
                        "status": 200,
                        "infrastructure": True,
                        "stage": "content_lookup",
                    }
                ],
            }
        ],
    }


def obsolete_fallback_result() -> dict:
    return {
        "key": "source:sample",
        "status": "no_streams",
        "score": 10,
        "evidence": {
            "streams_playable": 0,
            "provider_server_accessible": True,
            "provider_server_successful_response": True,
            "fixture_status_counts": {"no_streams": 1, "runtime_error": 0},
        },
        "tests": [
            {
                "status": "no_streams",
                "stream_count": 0,
                "streams_returned": 0,
                "streams_playable": 0,
                "provider_server_accessible": True,
                "provider_server_successful_response": True,
                "network_observations": [
                    {"host": "provider.example", "status": 200, "infrastructure": False, "stage": "search"},
                    {"host": "provider.example", "status": 404, "infrastructure": False, "stage": "content_lookup"},
                    {"host": "provider.example", "status": 404, "infrastructure": False, "stage": "content_lookup"},
                ],
            }
        ],
    }


def provider_forbidden_result() -> dict:
    return {
        "status": "blocked",
        "score": 0,
        "evidence": {"streams_playable": 0},
        "tests": [{
            "status": "blocked",
            "stream_count": 0,
            "network_observations": [
                {"host": "provider.example", "status": 403, "infrastructure": False, "stage": "content_lookup"}
            ],
        }],
    }


def stream_forbidden_result() -> dict:
    return {
        "status": "degraded",
        "score": 60,
        "evidence": {"streams_playable": 1},
        "tests": [{
            "status": "degraded",
            "stream_count": 1,
            "streams_returned": 1,
            "streams_playable": 1,
            "network_observations": [
                {"host": "media.example", "status": 403, "infrastructure": False, "stage": "player"}
            ],
        }],
    }


def healthy_result() -> dict:
    return {
        "status": "healthy",
        "score": 100,
        "evidence": {"streams_playable": 1, "fixture_status_counts": {"healthy": 1, "runtime_error": 0}},
        "tests": [{
            "status": "healthy",
            "stream_count": 1,
            "streams_returned": 1,
            "streams_playable": 1,
            "network_observations": [
                {"host": "provider.example", "status": 200, "infrastructure": False, "stage": "player"}
            ],
        }],
    }


def metadata_bundle() -> bytes:
    return b'''function G(a,b,c){return c()}function W(t,n){return function(A,D,T,x){return G(this,arguments,function*(f,g,h,_,m={}){let $=null,s=1,M="x";let P=yield zw(n(f,g,h,_,{signal:$}),s,M);return P})}}function zw(v){return v}function P(c,f,g,h){return G(this,arguments,function*(t,n,i,s,a={}){let D=yield X2(t,n,{season:i});if(!D||D.length===0)return[];return D})}function X2(){return Promise.resolve([])}module.exports={getStreams:async()=>[]}'''


def html_bundle() -> bytes:
    return b'''var Ko={default:{load:function(){return function(){return {each:function(){},first:function(){return this},find:function(){return this},attr:function(){return ""},text:function(){return ""}}}}}};function G(a,b,c){return c()}function tx(v){return v}function ZE(){return "1"}function QE(){return false}function rx(t){return t||[]}function ex(t,n){let i=Ko.default.load(t);return []}function ix(t,n){return Promise.resolve("<html></html>").then(h=>ex(h,t))}function cs(){return Promise.resolve([])}function mi(){return Promise.resolve([])}function gx(t,n,i){return G(this,null,function*(){let s=rx(n);for(let c of s){let f=yield ix(c,"movie");if(f.length){let h=yield cs("1",t,i);return yield mi(h)}}return[]})}function sg(t,n,i){return G(this,null,function*(){return yield gx(t,n,i)})}module.exports={getStreams:async()=>[]}'''


def test_runtime_signatures() -> None:
    assert runtime_trigger_matches("metadata_only_no_origin", metadata_only_result())
    assert runtime_trigger_matches("search_success_with_obsolete_fallback", obsolete_fallback_result())
    assert runtime_trigger_matches("provider_http_forbidden", provider_forbidden_result())
    assert runtime_trigger_matches("stream_http_forbidden", stream_forbidden_result())


def test_profile_selection_requires_explicit_runtime_auto_apply() -> None:
    candidate = {"key": "source:any-name", "canonical_id": "any-name", "local_patches": []}
    # The broad metadata mutation remains diagnostic-only.
    assert matching_profiles(candidate, metadata_only_result(), metadata_bundle().decode()) == []
    # The narrowly detected DLE repair may be generated, but compare_results
    # will retain it only after a verified playable stream.
    assert matching_profiles(candidate, obsolete_fallback_result(), html_bundle().decode()) == ["dle_html_search_recovery"]


def test_html_profile_is_syntax_safe() -> None:
    source = html_bundle()
    patched, records = apply_overrides(
        "random-provider", source, phase="runtime", profile_names=["dle_html_search_recovery"]
    )
    assert patched != source
    assert b"[Nuvio Runtime Repair] Content found via HTML search" in patched
    assert any(row.get("profile") == "dle_html_search_recovery" for row in records)
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / "provider.js"
        target.write_bytes(patched)
        subprocess.run(["node", "--check", str(target)], check=True)
        subprocess.run(["node", str(ROOT / "scripts" / "validate_provider_artifact.cjs"), str(target)], check=True)


def test_repair_candidate_and_comparison_requires_playable_stream() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        stage = Path(tmp)
        source_path = stage / "providers" / "upstream" / "sample.js"
        source_path.parent.mkdir(parents=True)
        source = metadata_bundle()
        source_path.write_bytes(source)
        candidate = {
            "key": "upstream:sample",
            "source": "upstream",
            "canonical_id": "sample",
            "upstream_id": "sample",
            "local_path": "providers/upstream/sample.js",
            "sha256": hashlib.sha256(source).hexdigest(),
            "local_patches": [],
        }
        repaired, error = create_repair_candidate(stage, candidate, "metadata_context_recovery", 1)
        assert error is None and repaired is not None

    reachable_without_stream = {
        "status": "reachable",
        "score": 75,
        "evidence": {"streams_playable": 0, "fixture_status_counts": {"reachable": 1, "runtime_error": 0}},
        "tests": [{"status": "reachable", "streams_returned": 0, "streams_playable": 0}],
    }
    accepted, reason = compare_results(metadata_only_result(), reachable_without_stream)
    assert not accepted and reason == "insufficient_playable_stream_proof"

    accepted, reason = compare_results(metadata_only_result(), healthy_result())
    assert accepted and reason == "strict_playable_stream_improvement"

    with_runtime_error = healthy_result()
    with_runtime_error["tests"].append({
        "status": "runtime_error",
        "error_details": {"code": "BROKEN", "message": "boom"},
        "streams_returned": 0,
        "streams_playable": 0,
    })
    with_runtime_error["evidence"]["fixture_status_counts"]["runtime_error"] = 1
    accepted, reason = compare_results(metadata_only_result(), with_runtime_error)
    assert not accepted and reason == "introduced_runtime_error"


def test_accepted_profiles_are_persistable() -> None:
    config = {"provider_patches": {"sample": {"profiles": ["existing"]}}}
    records = persist_runtime_profiles(config, {"sample": {"dle_html_search_recovery"}})
    assert records == [{"provider_id": "sample", "profile": "dle_html_search_recovery"}]
    assert config["provider_patches"]["sample"]["profiles"] == ["existing", "dle_html_search_recovery"]


def test_bounded_loop_accepts_only_verified_dle_repair() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        temp = Path(tmp)
        stage = temp / "staging"
        output = temp / "health-output"
        provider = stage / "providers" / "upstream" / "sample.js"
        provider.parent.mkdir(parents=True)
        source = html_bundle()
        provider.write_bytes(source)
        candidate = {
            "key": "upstream:sample",
            "source": "upstream",
            "canonical_id": "sample",
            "upstream_id": "sample",
            "local_path": "providers/upstream/sample.js",
            "sha256": hashlib.sha256(source).hexdigest(),
            "local_patches": [],
            "metadata": {"id": "sample", "name": "Sample", "supportedTypes": ["movie"]},
        }
        registry = {"schema_version": 66, "candidates": [candidate], "candidate_count": 1, "canonical_provider_count": 1}
        (stage / "candidates.json").write_text(json.dumps(registry), encoding="utf-8")
        fake = temp / "fake-health.mjs"
        fake.write_text(
            """
import { promises as fs } from 'node:fs';
import path from 'node:path';
const registry=JSON.parse(await fs.readFile(process.env.NUVIO_CANDIDATES_PATH,'utf8'));
const results=[];
for (const candidate of registry.candidates) {
 const text=await fs.readFile(path.join(process.env.NUVIO_STAGE,candidate.local_path),'utf8');
 const repaired=text.includes('[Nuvio Runtime Repair] Content found via HTML search');
 results.push({key:candidate.key,source:candidate.source,upstream_id:candidate.upstream_id,canonical_id:candidate.canonical_id,sha256:candidate.sha256,status:repaired?'healthy':'no_streams',score:repaired?100:10,evidence:{streams_playable:repaired?1:0,provider_server_accessible:true,provider_server_successful_response:true,fixture_status_counts:{healthy:repaired?1:0,no_streams:repaired?0:1,runtime_error:0}},tests:[{status:repaired?'healthy':'no_streams',stream_count:repaired?1:0,streams_returned:repaired?1:0,streams_playable:repaired?1:0,provider_server_accessible:true,provider_server_successful_response:true,network_observations:repaired?[{host:'provider.example',status:200,infrastructure:false,stage:'player'}]:[{host:'provider.example',status:200,infrastructure:false,stage:'search'},{host:'provider.example',status:404,infrastructure:false,stage:'content_lookup'},{host:'provider.example',status:404,infrastructure:false,stage:'content_lookup'}]}]});
}
await fs.mkdir(process.env.NUVIO_HEALTH_OUTPUT,{recursive:true});
await fs.writeFile(path.join(process.env.NUVIO_HEALTH_OUTPUT,'health-results.json'),JSON.stringify({schema_version:66,results,counts:{}},null,2)+'\\n');
""",
            encoding="utf-8",
        )
        subprocess.run([
            sys.executable, str(ROOT / "scripts" / "deep_repair_loop.py"),
            "--stage", str(stage), "--output", str(output), "--mode", "deep", "--health-check", str(fake),
        ], check=True, cwd=ROOT)
        final = json.loads((output / "repair-report.json").read_text())
        assert final["accepted_repairs"] == 1
        assert final["rounds"][0]["accepted"][0]["reason"] == "strict_playable_stream_improvement"
        assert final["rounds"][0]["accepted"][0]["streams_playable_after"] == 1
        assert len(final["rounds"]) <= 2


test_runtime_signatures()
test_profile_selection_requires_explicit_runtime_auto_apply()
test_html_profile_is_syntax_safe()
test_repair_candidate_and_comparison_requires_playable_stream()
test_accepted_profiles_are_persistable()
test_bounded_loop_accepts_only_verified_dle_repair()
print("runtime repair tests passed")
