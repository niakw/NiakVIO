#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
URL_LITERAL_RE = re.compile(r"https?://[^\"'\s}]+")
sys.path.insert(0, str(ROOT / "scripts"))

from apply_provider_overrides import apply_overrides


def literal_url_hosts(value: str | bytes) -> set[str]:
    text = value.decode("utf-8", errors="ignore") if isinstance(value, bytes) else value
    return {host for raw in URL_LITERAL_RE.findall(text) if (host := urlsplit(raw).hostname)}


def clean_v3(source: bytes) -> bytes:
    return (
        b"/* BEGIN NIAKVIO_PROVIDER */\n"
        b"/* NIAKVIO_PROVIDER_BASE_OWNED_V3 */\n"
        + source.strip()
        + b"\n/* END NIAKVIO_PROVIDER */\n"
    )


# Stable replacements still happen during discovery.
patched, records = apply_overrides("movix", b'const API="https://api.movix.cash/";', include_global_core=False)
assert b"api.movix.fun" in patched
assert b"api.movix.cash" not in patched
assert records and records[0]["count"] == 1


def test_staged_artifact_contract() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        stage = Path(tmp)
        (stage / "providers" / "gowaru").mkdir(parents=True)
        upstream = b'const APIS=["https://api.movix.cloud","https://api.movix.cash"];'
        output, patch_records = apply_overrides("movix", upstream, include_global_core=False)
        target = stage / "providers" / "gowaru" / "movix.js"
        target.write_bytes(output)
        registry = {
            "candidates": [{
                "key": "gowaru:movix",
                "canonical_id": "movix",
                "upstream_id": "movix",
                "local_path": "providers/gowaru/movix.js",
                "upstream_sha256": hashlib.sha256(upstream).hexdigest(),
                "sha256": hashlib.sha256(output).hexdigest(),
                "local_patches": patch_records,
            }]
        }
        (stage / "candidates.json").write_text(json.dumps(registry), encoding="utf-8")
        subprocess.run([
            sys.executable,
            str(ROOT / "scripts" / "validate_override_pipeline.py"),
            "--stage", str(stage),
        ], check=True)


def test_domain_overrides() -> None:
    config = json.loads((ROOT / "provider-overrides.json").read_text(encoding="utf-8"))
    purstream = config["provider_patches"]["purstream"]
    assert purstream["capability"] == "official_domain_hub"
    hub = str(purstream.get("official_hub") or "").rstrip("/")
    site = str(purstream.get("official_site") or "").rstrip("/")
    api = str(purstream.get("official_api") or "").rstrip("/")
    assert hub == "https://purstream.wiki", hub
    assert urlsplit(site).hostname == "purstream.ad", site
    assert urlsplit(api).hostname == "api.purstream.ad", api
    runtime_domains = purstream.get("runtime_domain_replacements") or {}
    assert isinstance(runtime_domains, dict) and runtime_domains
    replacement_hosts = {urlsplit(value if "://" in str(value) else f"https://{value}").hostname for value in runtime_domains.values()}
    assert "purstream.ad" in replacement_hosts or "api.purstream.ad" in replacement_hosts, replacement_hosts
    assert (purstream.get("manifest_overrides") or {}).get("enabled") is True

    movix_source = b"const A='https://api.movix.cash'; const B='https://api.movix.cloud';"
    movix_output, movix_records = apply_overrides("movix", movix_source, include_global_core=False)
    assert b"api.movix.fun" in movix_output
    assert b"api.movix.cash" not in movix_output
    assert b"api.movix.cloud" not in movix_output
    assert any(row.get("type") == "replace" for row in movix_records)


def test_runtime_profiles_are_not_blindly_applied() -> None:
    source = b'''function*(x){if(x.length===0)return[];return {signal:true,effectiveSeason:1}}'''
    output, patch_records = apply_overrides("example-provider", clean_v3(source))
    assert output != source
    assert b"NUVIO_GLOBAL_STREAM_FACTS_V1" in output
    assert b"NUVIO_GLOBAL_STREAM_IDENTITY_V1" in output
    assert b"NUVIO_GLOBAL_STREAM_PRESENTATION_V1" in output
    assert not any(row.get("type") == "patch_profile" for row in patch_records)


def test_runtime_domain_prefix_collisions_are_globally_idempotent() -> None:
    config = json.loads((ROOT / "provider-overrides.json").read_text())
    patches = config.get("provider_patches") or {}
    exercised = 0
    for provider_id, patch in patches.items():
        if not isinstance(patch, dict):
            continue
        replacements = patch.get("runtime_domain_replacements") or patch.get("replacements") or patch.get("domain_substitutions") or {}
        if not isinstance(replacements, dict) or len(replacements) < 2:
            continue
        old_hosts = [str(value).strip().lower().rstrip("/") for value in replacements if str(value).strip()]
        collisions = [host for host in old_hosts if any(other != host and other.startswith(host) for other in old_hosts)]
        for old_host in sorted(set(collisions)):
            target_host = str(replacements.get(old_host) or "").strip().lower().rstrip("/")
            if not target_host or target_host == old_host:
                continue
            exercised += 1
            source = f'const BASE="https://{old_host}/";'.encode()
            first, first_records = apply_overrides(provider_id, source, phase="runtime")
            assert f"https://{target_host}/".encode() in first, (provider_id, old_host, target_host)
            assert any(row.get("type") == "replace" and row.get("from") == old_host for row in first_records)
            second, second_records = apply_overrides(provider_id, first, phase="runtime")
            assert second == first, f"runtime domain override is not idempotent for {provider_id}:{old_host}"
            assert not any(row.get("type") == "replace" and row.get("from") == old_host for row in second_records)
    assert exercised > 0, "expected at least one configured runtime-domain prefix collision fixture"


def test_obfuscated_runtime_endpoint_override() -> None:
    source = b'''var DOMAINS_URL='https://registry-fixture.invalid/domains.json',MOVIX_FALLBACK='cash',_cachedEndpoint=null;function detectApi(){if(_cachedEndpoint)return Promise.resolve(_cachedEndpoint);return fetch(DOMAINS_URL).then(function(r){return r.json()}).then(function(x){return {api:'https://api.movix.'+x.movix}}).catch(function(){return {api:'https://api.movix.'+MOVIX_FALLBACK}})};module.exports={getStreams:async function(){var e=await detectApi();await fetch(e.api+'/api/purstream/movie/157336/stream');return []}};'''
    # Movix is historical and intentionally outside the current Hub46 provider
    # publication. Keep fixed_endpoint covered with an isolated legacy fixture
    # instead of reintroducing a provider-specific publication row.
    with tempfile.TemporaryDirectory(prefix="niakvio-fixed-endpoint-") as tmp:
        config_path = Path(tmp) / "overrides.json"
        config_path.write_text(json.dumps({
            "domain_replacements": {
                "api.movix.cash": "api.movix.fun",
                "api.movix.cloud": "api.movix.fun",
            },
            "provider_patches": {
                "movix": {
                    "fixed_endpoint": {
                        "resolver_function": "detectApi",
                        "api": "https://api.movix.fun",
                        "referer": "https://movix.example/",
                    }
                }
            },
        }), encoding="utf-8")
        output, records = apply_overrides("movix", source, phase="runtime", config_path=config_path)
        assert b"NUVIO_FIXED_ENDPOINT:https://api.movix.fun" in output
        assert b"fetch(DOMAINS_URL)" not in output
        assert b"raw.githubusercontent.com" not in output
        assert any(row.get("type") == "fixed_endpoint" for row in records)
        assert any(row.get("type") == "runtime_domain_overrides" for row in records) == (b"NUVIO_RUNTIME_DOMAIN_OVERRIDES_V1" in output)
        second, second_records = apply_overrides("movix", output, phase="runtime", config_path=config_path)
        assert second == output
        assert not any(row.get("type") in {"fixed_endpoint", "runtime_domain_overrides"} for row in second_records)
    with tempfile.TemporaryDirectory(prefix="niakvio-overrides-") as tmp:
        target = Path(tmp) / "provider.js"
        target.write_bytes(output)
        subprocess.run(["node", "--check", str(target)], check=True)
        subprocess.run(["node", str(ROOT / "scripts" / "validate_provider_artifact.cjs"), str(target)], check=True)
        probe = Path(tmp) / "probe.cjs"
        probe.write_text(
            "const p=require(process.argv[2]);const seen=[];"
            "global.fetch=async u=>{seen.push(String(u));return {ok:true,status:200,text:async()=>'',json:async()=>({})};};"
            "Promise.resolve(p.getStreams()).then(()=>{"
            "if(seen.length!==1||!seen[0].startsWith('https://api.movix.fun/')){console.error(JSON.stringify(seen));process.exit(2);}"
            "console.log('MOVIX_FIXED_ENDPOINT_RUNTIME_OK '+seen[0]);"
            "}).catch(e=>{console.error(e);process.exit(3);});",
            encoding="utf-8",
        )
        subprocess.run(["node", str(probe), str(target)], check=True)


def test_runtime_domain_override_rewrites_polyfilled_urls_without_mutating_hostname() -> None:
    source = b'''module.exports={getStreams:async function(){await fetch("https://api.old.invalid/stream");return []}};'''
    with tempfile.TemporaryDirectory(prefix="niakvio-runtime-domain-") as tmp:
        config_path = Path(tmp) / "overrides.json"
        config_path.write_text(json.dumps({
            "provider_patches": {"synthetic": {"runtime_domain_replacements": {"api.old.invalid": "api.new.invalid"}}}
        }), encoding="utf-8")
        output, records = apply_overrides("synthetic", source, phase="runtime", config_path=config_path)
    text = output.decode("utf-8")
    assert "NUVIO_RUNTIME_DOMAIN_OVERRIDES_V1" in text
    assert "url.hostname=replacement" in text
    assert any(row.get("type") == "runtime_domain_overrides" for row in records)


test_staged_artifact_contract()
test_domain_overrides()
test_runtime_profiles_are_not_blindly_applied()
test_runtime_domain_prefix_collisions_are_globally_idempotent()
test_obfuscated_runtime_endpoint_override()
test_runtime_domain_override_rewrites_polyfilled_urls_without_mutating_hostname()
print("override pipeline tests passed")
