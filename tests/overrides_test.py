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
    assert b"fs16.lol" in output
    assert b"french-stream.one" not in output
    assert any(
        row.get("from") == "french-stream.one"
        and row.get("to") == "fs16.lol"
        for row in patch_records
    )


def synthetic_metadata_bundle() -> bytes:
    return b'''function G(a,b,c){return c()}function W(t,n){return function(A,D,T,x){return G(this,arguments,function*(f,g,h,_,m={}){let $=null,s=1,M="x";let P=yield zw(n(f,g,h,_,{signal:$}),s,M);return P})}}function zw(v){return v}function P(c,f,g,h){return G(this,arguments,function*(t,n,i,s,a={}){let D=yield X2(t,n,{season:i});if(!D||D.length===0)return[];return D})}function X2(){return Promise.resolve([])}module.exports={getStreams:async()=>[]}'''


def test_runtime_profiles_are_not_blindly_applied() -> None:
    config = json.loads((ROOT / "provider-overrides.json").read_text())
    for name, profile in config["patch_profiles"].items():
        phase = profile.get("phase")
        assert phase in {"runtime", "build"}, name
        assert "provider_id" not in profile, name
        if phase == "runtime":
            assert profile.get("auto_apply") is False, name
            assert profile.get("runtime_trigger"), name
        else:
            assert profile.get("auto_apply") is True, name
            assert profile.get("patch_script"), name
            assert "runtime_trigger" not in profile, name

    source = synthetic_metadata_bundle()
    discovery, discovery_records = apply_overrides("arbitrary-provider", source)
    assert b"NUVIO_GLOBAL_STREAM_OUTPUT_GUARD" not in discovery
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
        # This contract must not depend on live DNS/network conditions. Execute
        # the synthetic provider with a deterministic fetch stub and inspect the
        # URL actually requested after all runtime wrappers were installed.
        harness = r"""
const target = process.argv[1];
const requested = [];
global.fetch = async function(input) {
  const url = typeof input === "string" ? input : String(input && input.url || input);
  requested.push(url);
  return { ok: true, status: 200, json: async () => ({}) };
};
(async () => {
  const provider = require(target);
  await provider.getStreams("157336", "movie", null, null);
  process.stdout.write(JSON.stringify(requested));
})().catch((error) => {
  console.error(error && error.stack || error);
  process.exit(1);
});
"""
        result = subprocess.run(
            ["node", "-e", harness, str(target.resolve())],
            text=True,
            capture_output=True,
            check=True,
        )
        requested = json.loads(result.stdout)
        expected = "https://api.movix.fun/api/purstream/movie/157336/stream"
        assert requested, requested
        assert all(url == expected for url in requested), requested


test_obfuscated_runtime_endpoint_override()


def test_idempotent_override_validation() -> None:
    validator = str(ROOT / "scripts" / "validate_override_pipeline.py")

    # A staged provider that already contains the terminal target is valid even
    # when no replacement record was emitted during this run.
    with tempfile.TemporaryDirectory() as tmp:
        stage = Path(tmp)
        target = stage / "providers" / "gowaru" / "movix.js"
        target.parent.mkdir(parents=True)
        output = b'const API="https://api.movix.fun";'
        target.write_bytes(output)
        registry = {
            "candidates": [{
                "key": "gowaru:movix",
                "canonical_id": "movix",
                "upstream_id": "movix",
                "local_path": "providers/gowaru/movix.js",
                "upstream_sha256": hashlib.sha256(output).hexdigest(),
                "sha256": hashlib.sha256(output).hexdigest(),
                "local_patches": [],
            }]
        }
        (stage / "candidates.json").write_text(json.dumps(registry), encoding="utf-8")
        subprocess.run([sys.executable, validator, "--stage", str(stage)], check=True)

    # Neither a historical value nor the terminal target means the provider
    # structure changed and the configured override must be reviewed.
    with tempfile.TemporaryDirectory() as tmp:
        stage = Path(tmp)
        target = stage / "providers" / "gowaru" / "movix.js"
        target.parent.mkdir(parents=True)
        output = b'const API="https://unexpected.example";'
        target.write_bytes(output)
        registry = {
            "candidates": [{
                "key": "gowaru:movix",
                "canonical_id": "movix",
                "upstream_id": "movix",
                "local_path": "providers/gowaru/movix.js",
                "upstream_sha256": hashlib.sha256(output).hexdigest(),
                "sha256": hashlib.sha256(output).hexdigest(),
                "local_patches": [],
            }]
        }
        (stage / "candidates.json").write_text(json.dumps(registry), encoding="utf-8")
        result = subprocess.run(
            [sys.executable, validator, "--stage", str(stage)],
            text=True, capture_output=True,
        )
        assert result.returncode == 1
        assert "override stale" in result.stdout


test_idempotent_override_validation()


def test_chained_provider_patch_scripts_and_output_guard() -> None:
    source = b'''async function getStreams(){return [{url:"http://fstream.top/bad.m3u8"},{url:"https://media.example/malformed.m3u8"},{url:"https://media.example/good.m3u8"}]};module.exports={getStreams};'''
    output, records = apply_overrides("frenchstream", source)
    assert b"NUVIO_STREAM_OUTPUT_SANITIZER_V2" in output
    assert any(
        row.get("type") == "patch_script"
        and row.get("path") == "scripts/provider_patches/stream_output_sanitizer.py"
        for row in records
    )
    second, second_records = apply_overrides("frenchstream", output)
    assert second == output
    assert not any(
        row.get("path") == "scripts/provider_patches/stream_output_sanitizer.py"
        for row in second_records
    )
    with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
        target = Path(tmp) / "provider.js"
        target.write_bytes(output)
        harness = r"""
const provider = require(process.argv[1]);
global.fetch = async function(url) {
  return {
    ok: true,
    url: String(url),
    headers: { get: () => "application/vnd.apple.mpegurl" },
    body: {
      getReader: () => ({
        read: async () => ({ value: new TextEncoder().encode(String(url).includes("malformed") ? "<html>blocked</html>" : "#EXTM3U\n#EXT-X-VERSION:3\n") }),
        cancel: async () => {}
      })
    }
  };
};
provider.getStreams().then((rows) => process.stdout.write(JSON.stringify(rows)));
"""
        result = subprocess.run(
            ["node", "-e", harness, str(target.resolve())],
            check=True,
            text=True,
            capture_output=True,
        )
        rows = json.loads(result.stdout)
        assert [row["url"] for row in rows] == ["https://media.example/good.m3u8"]


def test_toflix_terminal_bootstrap_patch() -> None:
    source = b'''var _cachedEndpoint=null;function detectToflixEndpoint(){return Promise.resolve({api:"https://api.toflix.site/toflix_api.php",referer:"https://toflix.site/"})}module.exports={getStreams:async()=>[]};'''
    output, records = apply_overrides("toflix", source)
    assert b"NUVIO_TOFLIX_OFFICIAL_ENDPOINT_V1" in output
    assert b"https://tfx05.lol" in output
    assert any(row.get("path") == "scripts/provider_patches/toflix_official_endpoint.py" for row in records)


test_chained_provider_patch_scripts_and_output_guard()
test_toflix_terminal_bootstrap_patch()

print("override tests passed")
