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
from runtime_repair import (
    compare_results,
    create_repair_candidate,
    matching_profiles,
    runtime_trigger_matches,
)
from deep_repair_loop import persist_runtime_profiles


def metadata_only_result() -> dict:
    return {
        "key": "source:sample",
        "status": "no_streams",
        "score": 10,
        "evidence": {
            "streams_playable": 0,
            "provider_server_accessible": False,
            "provider_server_successful_response": False,
        },
        "tests": [
            {
                "stream_count": 0,
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
        "status": "reachable",
        "score": 75,
        "evidence": {
            "streams_playable": 0,
            "provider_server_accessible": True,
            "provider_server_successful_response": True,
        },
        "tests": [
            {
                "stream_count": 0,
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
        "key": "source:sample",
        "status": "reachable",
        "score": 75,
        "evidence": {
            "streams_playable": 0,
            "provider_server_accessible": True,
            "provider_server_successful_response": False,
        },
        "tests": [{
            "stream_count": 0,
            "provider_server_accessible": True,
            "provider_server_successful_response": False,
            "network_observations": [
                {"host": "provider.example", "status": 403, "infrastructure": False, "stage": "content_lookup"}
            ],
        }],
    }


def stream_forbidden_result() -> dict:
    return {
        "key": "source:sample",
        "status": "degraded",
        "score": 60,
        "evidence": {
            "streams_playable": 1,
            "provider_server_accessible": True,
            "provider_server_successful_response": True,
        },
        "tests": [{
            "stream_count": 1,
            "provider_server_accessible": True,
            "provider_server_successful_response": True,
            "network_observations": [
                {"host": "media.example", "status": 403, "infrastructure": False, "stage": "content_lookup"}
            ],
        }],
    }


def fetch_bundle() -> bytes:
    return b'module.exports={getStreams:function(){return fetch("https://provider.example/api").then(function(){return []})}};'


def metadata_bundle() -> bytes:
    return b'''function G(a,b,c){return c()}function W(t,n){return function(A,D,T,x){return G(this,arguments,function*(f,g,h,_,m={}){let $=null,s=1,M="x";let P=yield zw(n(f,g,h,_,{signal:$}),s,M);return P})}}function zw(v){return v}function P(c,f,g,h){return G(this,arguments,function*(t,n,i,s,a={}){let D=yield X2(t,n,{season:i});if(!D||D.length===0)return[];return D})}function X2(){return Promise.resolve([])}module.exports={getStreams:async()=>[]}'''


def html_bundle() -> bytes:
    return b'''var Ko={default:{load:function(){return function(){return {each:function(){},first:function(){return this},find:function(){return this},attr:function(){return ""},text:function(){return ""}}}}}};function G(a,b,c){return c()}function tx(v){return v}function ZE(){return "1"}function QE(){return false}function rx(t){return t||[]}function ex(t,n){let i=Ko.default.load(t);return []}function ix(t,n){return Promise.resolve("<html></html>").then(h=>ex(h,t))}function cs(){return Promise.resolve([])}function mi(){return Promise.resolve([])}function gx(t,n,i){return G(this,null,function*(){let s=rx(n);for(let c of s){let f=yield ix(c,"movie");if(f.length){let h=yield cs("1",t,i);return yield mi(h)}}return[]})}function sg(t,n,i){return G(this,null,function*(){return yield gx(t,n,i)})}module.exports={getStreams:async()=>[]}'''


def test_runtime_signatures() -> None:
    assert runtime_trigger_matches("metadata_only_no_origin", metadata_only_result())
    assert not runtime_trigger_matches("search_success_with_obsolete_fallback", metadata_only_result())
    assert runtime_trigger_matches("search_success_with_obsolete_fallback", obsolete_fallback_result())
    assert runtime_trigger_matches("provider_http_forbidden", provider_forbidden_result())
    assert not runtime_trigger_matches("stream_http_forbidden", provider_forbidden_result())
    assert runtime_trigger_matches("stream_http_forbidden", stream_forbidden_result())


def test_profile_selection_is_provider_agnostic() -> None:
    candidate = {"key": "source:any-name", "canonical_id": "any-name", "local_patches": []}
    source = metadata_bundle().decode()
    profiles = matching_profiles(candidate, metadata_only_result(), source)
    assert profiles == ["metadata_context_recovery"]

    source = html_bundle().decode()
    profiles = matching_profiles(candidate, obsolete_fallback_result(), source)
    assert profiles == ["dle_html_search_recovery"]

    source = fetch_bundle().decode()
    profiles = matching_profiles(candidate, provider_forbidden_result(), source)
    assert "request_header_recovery" not in profiles

    profiles = matching_profiles(candidate, stream_forbidden_result(), source)
    assert "stream_output_recovery" not in profiles


def test_html_profile_rewrites_exact_functions_without_deleting_neighbours() -> None:
    source = html_bundle()
    patched, records = apply_overrides(
        "random-provider",
        source,
        phase="runtime",
        profile_names=["dle_html_search_recovery"],
    )
    assert patched != source
    assert b"[Nuvio Runtime Repair] Content found via HTML search" in patched
    assert b"function rx(" in patched
    assert b"function sg(" in patched
    assert any(row.get("profile") == "dle_html_search_recovery" for row in records)
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / "provider.js"
        target.write_bytes(patched)
        subprocess.run(["node", "--check", str(target)], check=True)
        subprocess.run(
            ["node", str(ROOT / "scripts" / "validate_provider_artifact.cjs"), str(target)],
            check=True,
        )



def test_real_minified_bundle_rewrite_is_syntax_safe() -> None:
    source_path = ROOT / "providers" / "frenchstream--gowaru--c4735951ca7fb2df.js"
    source = source_path.read_bytes()
    discovery, _ = apply_overrides("frenchstream", source, phase="discovery")
    metadata, _ = apply_overrides(
        "frenchstream", discovery, phase="runtime", profile_names=["metadata_context_recovery"]
    )
    patched, records = apply_overrides(
        "frenchstream", metadata, phase="runtime", profile_names=["dle_html_search_recovery"]
    )
    assert patched != metadata
    assert any(row.get("profile") == "dle_html_search_recovery" for row in records)
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / "provider.js"
        target.write_bytes(patched)
        subprocess.run(["node", "--check", str(target)], check=True)
        subprocess.run(
            ["node", str(ROOT / "scripts" / "validate_provider_artifact.cjs"), str(target)],
            check=True,
        )

def test_repair_candidate_and_comparison() -> None:
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
            "upstream_sha256": hashlib.sha256(source).hexdigest(),
            "local_patches": [],
            "metadata": {"id": "sample", "name": "Sample"},
        }
        repaired, error = create_repair_candidate(stage, candidate, "metadata_context_recovery", 1)
        assert error is None
        assert repaired is not None
        assert repaired["sha256"] != candidate["sha256"]
        assert (stage / repaired["local_path"]).is_file()

        improved = {
            "status": "reachable",
            "score": 75,
            "evidence": {
                "streams_playable": 0,
                "provider_server_accessible": True,
                "provider_server_successful_response": True,
            },
            "tests": [{"stream_count": 0, "network_observations": []}],
        }
        accepted, reason = compare_results(metadata_only_result(), improved)
        assert accepted and reason == "strict_runtime_improvement"

        broken = {"status": "runtime_error", "score": 0, "evidence": {}, "tests": []}
        accepted, reason = compare_results(metadata_only_result(), broken)
        assert not accepted and reason.startswith("hard_failure")

        route_only = {
            "status": "reachable",
            "score": 75,
            "evidence": {
                "streams_playable": 0,
                "provider_server_accessible": True,
                "provider_server_successful_response": True,
            },
            "tests": [{
                "stream_count": 0,
                "network_observations": [
                    {"host": "provider.example", "status": 200, "infrastructure": False, "stage": "search"}
                ],
            }],
        }
        accepted, reason = compare_results(obsolete_fallback_result(), route_only)
        assert not accepted and reason == "no_strict_runtime_improvement"


def test_accepted_profiles_are_persistable_without_provider_specific_code() -> None:
    config = {"provider_patches": {"sample": {"profiles": ["existing"]}}}
    records = persist_runtime_profiles(config, {"sample": {"request_header_recovery"}, "other": {"stream_output_recovery"}})
    assert {row["profile"] for row in records} == {"request_header_recovery", "stream_output_recovery"}
    assert config["provider_patches"]["sample"]["profiles"] == ["existing", "request_header_recovery"]
    assert config["provider_patches"]["other"]["profiles"] == ["stream_output_recovery"]


test_runtime_signatures()
test_profile_selection_is_provider_agnostic()
test_accepted_profiles_are_persistable_without_provider_specific_code()
test_html_profile_rewrites_exact_functions_without_deleting_neighbours()
test_repair_candidate_and_comparison()
print("runtime repair tests passed")


def test_build_wiring_and_no_provider_specific_repair_code() -> None:
    repair_engine = (ROOT / "scripts" / "runtime_repair.py").read_text(encoding="utf-8").casefold()
    loop = (ROOT / "scripts" / "deep_repair_loop.py").read_text(encoding="utf-8").casefold()
    workflow = (ROOT / ".github" / "workflows" / "sync.yml").read_text(encoding="utf-8")
    for provider_name in ("frenchstream", "streamzo", "flemmix"):
        assert provider_name not in repair_engine
        assert provider_name not in loop
    assert "python scripts/deep_repair_loop.py" in workflow
    assert "python scripts/validate_override_pipeline.py --stage staging" in workflow


test_build_wiring_and_no_provider_specific_repair_code()


def test_bounded_deep_loop_retests_and_keeps_only_improvements() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        temp = Path(tmp)
        stage = temp / "staging"
        output = temp / "health-output"
        provider = stage / "providers" / "upstream" / "sample.js"
        provider.parent.mkdir(parents=True)
        source = metadata_bundle() + b"\n" + html_bundle()
        provider.write_bytes(source)
        candidate = {
            "key": "upstream:sample",
            "source": "upstream",
            "canonical_id": "sample",
            "upstream_id": "sample",
            "local_path": "providers/upstream/sample.js",
            "sha256": hashlib.sha256(source).hexdigest(),
            "upstream_sha256": hashlib.sha256(source).hexdigest(),
            "local_patches": [],
            "metadata": {"id": "sample", "name": "Sample", "supportedTypes": ["movie"]},
        }
        registry = {
            "schema_version": 64,
            "candidate_count": 1,
            "canonical_provider_count": 1,
            "excluded_count": 0,
            "excluded": [],
            "upstreams": {},
            "errors": [],
            "candidates": [candidate],
        }
        (stage / "candidates.json").write_text(json.dumps(registry), encoding="utf-8")

        fake = temp / "fake-health.mjs"
        fake.write_text(
            """
import { promises as fs } from 'node:fs';
import path from 'node:path';
const registry = JSON.parse(await fs.readFile(process.env.NUVIO_CANDIDATES_PATH, 'utf8'));
const stage = process.env.NUVIO_STAGE;
const results = [];
for (const candidate of registry.candidates) {
  const text = await fs.readFile(path.join(stage, candidate.local_path), 'utf8');
  const metadataRepaired = text.includes('[Nuvio Runtime Repair] Using fixture title metadata');
  const searchRepaired = text.includes('[Nuvio Runtime Repair] Content found via HTML search');
  const fullyRepaired = metadataRepaired && searchRepaired;
  const observations = !metadataRepaired
    ? [{host:'metadata.example',status:200,infrastructure:true,stage:'content_lookup'}]
    : !searchRepaired
      ? [
          {host:'provider.example',status:200,infrastructure:false,stage:'search'},
          {host:'provider.example',status:404,infrastructure:false,stage:'content_lookup'},
          {host:'provider.example',status:404,infrastructure:false,stage:'content_lookup'},
        ]
      : [{host:'provider.example',status:200,infrastructure:false,stage:'search'}];
  results.push({
    key: candidate.key,
    source: candidate.source,
    upstream_id: candidate.upstream_id,
    canonical_id: candidate.canonical_id,
    sha256: candidate.sha256,
    mode: 'deep',
    status: fullyRepaired ? 'healthy' : metadataRepaired ? 'reachable' : 'no_streams',
    score: fullyRepaired ? 100 : metadataRepaired ? 75 : 10,
    evidence: {
      streams_playable: fullyRepaired ? 1 : 0,
      provider_server_accessible: metadataRepaired,
      provider_server_successful_response: metadataRepaired,
    },
    tests: [{
      stream_count: fullyRepaired ? 1 : 0,
      provider_server_accessible: metadataRepaired,
      provider_server_successful_response: metadataRepaired,
      network_observations: observations,
    }],
  });
}
const report = {schema_version:64,environment:'test',mode:'deep',generated_at:new Date().toISOString(),duration_seconds:0,candidate_count:results.length,excluded_during_discovery:0,counts:{},results};
await fs.mkdir(process.env.NUVIO_HEALTH_OUTPUT,{recursive:true});
await fs.writeFile(path.join(process.env.NUVIO_HEALTH_OUTPUT,'health-results.json'),JSON.stringify(report,null,2)+'\\n');
""",
            encoding="utf-8",
        )

        subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "deep_repair_loop.py"),
                "--stage",
                str(stage),
                "--output",
                str(output),
                "--mode",
                "deep",
                "--health-check",
                str(fake),
            ],
            check=True,
            cwd=ROOT,
        )
        final_registry = json.loads((stage / "candidates.json").read_text())
        final_candidate = final_registry["candidates"][0]
        assert final_candidate["key"] == "upstream:sample"
        assert "runtime-repairs" in final_candidate["local_path"]
        applied = {
            row.get("profile")
            for row in final_candidate.get("local_patches", [])
            if row.get("type") == "patch_profile"
        }
        assert applied == {"metadata_context_recovery", "dle_html_search_recovery"}
        final_health = json.loads((output / "health-results.json").read_text())
        assert final_health["results"][0]["status"] == "healthy"
        repair_report = json.loads((output / "repair-report.json").read_text())
        assert repair_report["provider_specific_rules"] is False
        assert repair_report["accepted_repairs"] == 2


test_bounded_deep_loop_retests_and_keeps_only_improvements()
print("bounded deep repair integration test passed")
