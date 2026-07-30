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


# Stable replacements still happen during discovery.
patched, records = apply_overrides("movix", b'const API="https://api.movix.cash/";')
assert b"api.movix.fun" in patched
assert b"api.movix.cash" not in patched
assert records and records[0]["count"] == 1


def test_staged_artifact_contract() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        stage = Path(tmp)
        (stage / "providers" / "gowaru").mkdir(parents=True)
        upstream = b'const APIS=["https://api.movix.cloud","https://api.movix.cash"];'
        output, patch_records = apply_overrides("movix", upstream)
        target = stage / "providers" / "gowaru" / "movix.js"
        target.write_bytes(output)
        registry = {
            "candidates": [
                {
                    "key": "gowaru:movix",
                    "canonical_id": "movix",
                    "upstream_id": "movix",
                    "local_path": "providers/gowaru/movix.js",
                    "upstream_sha256": hashlib.sha256(upstream).hexdigest(),
                    "sha256": hashlib.sha256(output).hexdigest(),
                    "local_patches": patch_records,
                }
            ]
        }
        (stage / "candidates.json").write_text(json.dumps(registry), encoding="utf-8")
        subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "validate_override_pipeline.py"),
                "--stage",
                str(stage),
            ],
            check=True,
        )


def test_domain_overrides() -> None:
    source = b"const BASE='https://french-stream.one';"
    output, patch_records = apply_overrides("frenchstream", source)
    assert b"frenchstream.food" in output
    assert b"french-stream.one" not in output
    assert any(
        row.get("from") == "french-stream.one"
        and row.get("to") == "frenchstream.food"
        for row in patch_records
    )


def synthetic_metadata_bundle() -> bytes:
    return b'''function G(a,b,c){return c()}function W(t,n){return function(A,D,T,x){return G(this,arguments,function*(f,g,h,_,m={}){let $=null,s=1,M="x";let P=yield zw(n(f,g,h,_,{signal:$}),s,M);return P})}}function zw(v){return v}function P(c,f,g,h){return G(this,arguments,function*(t,n,i,s,a={}){let D=yield X2(t,n,{season:i});if(!D||D.length===0)return[];return D})}function X2(){return Promise.resolve([])}module.exports={getStreams:async()=>[]}'''


def test_runtime_profiles_are_not_blindly_applied() -> None:
    config = json.loads((ROOT / "provider-overrides.json").read_text())
    for name, profile in config["patch_profiles"].items():
        assert profile["phase"] == "runtime", name
        assert profile["auto_apply"] is False, name
        assert "provider_id" not in profile, name
        assert profile["runtime_trigger"], name

    source = synthetic_metadata_bundle()
    discovery, discovery_records = apply_overrides("arbitrary-provider", source)
    assert b"NUVIO_GLOBAL_STREAM_OUTPUT_GUARD_V3" not in discovery
    assert b"NUVIO_STREAM_OUTPUT_RECOVERY_V1" not in discovery
    assert not any(row.get("type") == "patch_profile" for row in discovery_records)

    runtime, runtime_records = apply_overrides(
        "another-arbitrary-provider",
        source,
        phase="runtime",
        profile_names=["metadata_context_recovery"],
    )
    assert b"[Nuvio Runtime Repair] Using fixture title metadata" in runtime
    assert b"Object.assign({},m||{},{signal:$})" in runtime
    assert any(
        row.get("type") == "patch_profile"
        and row.get("profile") == "metadata_context_recovery"
        for row in runtime_records
    )
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / "provider.js"
        target.write_bytes(runtime)
        subprocess.run(["node", "--check", str(target)], check=True)
        subprocess.run(
            ["node", str(ROOT / "scripts" / "validate_provider_artifact.cjs"), str(target)],
            check=True,
        )


test_staged_artifact_contract()
test_domain_overrides()
test_runtime_profiles_are_not_blindly_applied()


def test_obfuscated_runtime_endpoint_override() -> None:
    source = b"""var DOMAINS_URL='https://raw.githubusercontent.com/wooodyhood/nuvio-repo/main/domains.json',MOVIX_FALLBACK='cash',_cachedEndpoint=null;function detectApi(){if(_cachedEndpoint)return Promise.resolve(_cachedEndpoint);return fetch(DOMAINS_URL).then(function(r){return r.json()}).then(function(x){return {api:'https://api.movix.'+x.movix}}).catch(function(){return {api:'https://api.movix.'+MOVIX_FALLBACK}})};module.exports={getStreams:async function(){var e=await detectApi();await fetch(e.api+'/api/purstream/movie/157336/stream');return []}};"""
    output, records = apply_overrides("movix", source)
    assert b"NUVIO_FIXED_ENDPOINT:https://api.movix.fun" in output
    assert b"NUVIO_RUNTIME_DOMAIN_OVERRIDES_V1" in output
    assert b"fetch(DOMAINS_URL)" not in output
    assert any(row.get("type") == "fixed_endpoint" for row in records)
    assert any(row.get("type") == "runtime_domain_overrides" for row in records)
    second, second_records = apply_overrides("movix", output)
    assert second == output
    assert not any(row.get("type") in {"fixed_endpoint", "runtime_domain_overrides"} for row in second_records)
    with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
        target = Path(tmp) / "provider.js"
        target.write_bytes(output)
        subprocess.run(["node", "--check", str(target)], check=True)
        result = subprocess.run(
            [
                "node",
                str(ROOT / "scripts" / "provider_worker.cjs"),
                str(target),
                '{"tmdbId":"157336","mediaType":"movie","title":"Interstellar","year":2014,"label":"Interstellar (2014)","category":"movie"}',
                '{"locale":"fr-FR","language":"fr","languages":["fr-FR","fr"],"platform":"android","settings":{},"storage":{}}',
            ],
            text=True,
            capture_output=True,
            check=True,
        )
        assert "wooodyhood/nuvio-repo/main/domains.json" not in result.stdout
        assert '"host":"api.movix.fun"' in result.stdout
        assert '"host":"api.movix.cash"' not in result.stdout


test_obfuscated_runtime_endpoint_override()


def test_provider_request_headers_fix_request_stage_403() -> None:
    source = b'''module.exports={getStreams:function(){return fetch("https://api.movix.fun/api/fstream/movie/157336",{headers:{"X-Keep":"yes"}}).then(function(){return []})}};'''
    output, records = apply_overrides("movix", source)
    assert b"NUVIO_REQUEST_HEADER_OVERRIDES_V1" in output
    assert any(row.get("type") == "request_header_overrides" for row in records)
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / "provider.js"
        target.write_bytes(output)
        script = f'''global.fetch=(url,init)=>{{console.log(JSON.stringify({{url,headers:init.headers}}));return Promise.resolve({{}})}};const p=require({json.dumps(str(target))});Promise.resolve(p.getStreams()).catch(()=>{{}});'''
        row = json.loads(subprocess.check_output(["node", "-e", script], text=True).strip())
    headers = {str(k).lower(): str(v) for k, v in row["headers"].items()}
    assert headers["x-keep"] == "yes"
    assert headers["origin"] == "https://movix.fun"
    assert headers["referer"] == "https://movix.fun/"
    assert "application/json" in headers["accept"]
    assert headers["user-agent"]


test_provider_request_headers_fix_request_stage_403()


def test_request_header_policies_accumulate_across_loaded_providers() -> None:
    movix_source = b'module.exports={getStreams:function(){return fetch("https://api.movix.fun/test").then(function(){return []})}};'
    dahmer_source = b'module.exports={getStreams:function(){return fetch("https://a.111477.xyz/test").then(function(){return []})}};'
    movix, _ = apply_overrides("movix", movix_source)
    dahmer, _ = apply_overrides("dahmermovies", dahmer_source)
    with tempfile.TemporaryDirectory() as tmp:
        movix_path = Path(tmp) / "movix.js"
        dahmer_path = Path(tmp) / "dahmer.js"
        movix_path.write_bytes(movix)
        dahmer_path.write_bytes(dahmer)
        script = f'''const calls=[];global.fetch=(url,init)=>{{calls.push({{url,headers:init.headers}});return Promise.resolve({{}})}};const m=require({json.dumps(str(movix_path))});const d=require({json.dumps(str(dahmer_path))});Promise.resolve(d.getStreams()).then(()=>m.getStreams()).then(()=>console.log(JSON.stringify(calls)));'''
        calls = json.loads(subprocess.check_output(["node", "-e", script], text=True).strip())
    movix_headers = {str(k).lower(): str(v) for k, v in calls[1]["headers"].items()}
    assert movix_headers["origin"] == "https://movix.fun"
    assert movix_headers["referer"] == "https://movix.fun/"


test_request_header_policies_accumulate_across_loaded_providers()

print("override tests passed")
