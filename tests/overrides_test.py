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

def literal_url_hosts(value: str | bytes) -> set[str]:
    text = value.decode("utf-8", errors="ignore") if isinstance(value, bytes) else value
    return {host for raw in URL_LITERAL_RE.findall(text) if (host := urlsplit(raw).hostname)}

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
    # A configured terminal safety quarantine replaces the provider with an
    # inert artifact. Historical route/domain mappings are intentionally pruned
    # from terminal quarantines so a later reapply cannot resurrect a stale
    # repair path. Domain replacement behavior remains covered by active
    # providers such as Movix and Flemmix below.
    assert b"NUVIO_PROVIDER_QUARANTINE_V1" in output
    assert b"french-stream.one" not in output
    assert not any(
        row.get("type") == "replace"
        and row.get("from") == "french-stream.one"
        for row in patch_records
    )

    movix_source = b"const A='https://api.movix.cash'; const B='https://api.movix.cloud';"
    movix_output, movix_records = apply_overrides("movix", movix_source)
    assert b"api.movix.fun" in movix_output
    assert b"api.movix.cash" not in movix_output
    assert b"api.movix.cloud" not in movix_output
    assert any(row.get("type") == "replace" for row in movix_records)


def test_runtime_profiles_are_not_blindly_applied() -> None:
    source = b'''function*(x){if(x.length===0)return[];return {signal:true,effectiveSeason:1}}'''
    output, patch_records = apply_overrides("example-provider", source)
    assert output == source
    assert not any(row.get("type") == "patch_profile" for row in patch_records)


def test_domain_prefix_collision_is_idempotent() -> None:
    # flemmix.me is a prefix of historical flemmix.men/flemmix.menn spellings.
    # This is specifically a stable-domain/runtime-rewrite contract. Keep the
    # synthetic fixture in the runtime phase so unrelated discovery-time Core
    # wrappers cannot turn this focused unit test into a second end-to-end
    # publication-idempotence suite. Published artifacts retain their dedicated
    # byte-level reapply checks elsewhere in npm test.
    source = b'const BASE="https://flemmix.me/";'
    config = json.loads((ROOT / "provider-overrides.json").read_text())
    patch = config["provider_patches"]["flemmix"]
    target_host = (
        (patch.get("runtime_domain_replacements") or patch.get("replacements") or {})
        .get("flemmix.me")
    )
    assert target_host, patch
    first, records = apply_overrides("flemmix", source, phase="runtime")
    assert ("https://" + target_host + "/").encode() in first
    assert b"flemmix.menn" not in first
    assert any(row.get("from") == "flemmix.me" for row in records)
    second, second_records = apply_overrides("flemmix", first, phase="runtime")
    assert second == first
    assert b"flemmix.menn" not in second
    assert not any(row.get("type") == "replace" and row.get("from") == "flemmix.me" for row in second_records)


test_staged_artifact_contract()
test_domain_overrides()
test_runtime_profiles_are_not_blindly_applied()
test_domain_prefix_collision_is_idempotent()


def test_obfuscated_runtime_endpoint_override() -> None:
    source = b'''var DOMAINS_URL='https://raw.githubusercontent.com/wooodyhood/nuvio-repo/main/domains.json',MOVIX_FALLBACK='cash',_cachedEndpoint=null;function detectApi(){if(_cachedEndpoint)return Promise.resolve(_cachedEndpoint);return fetch(DOMAINS_URL).then(function(r){return r.json()}).then(function(x){return {api:'https://api.movix.'+x.movix}}).catch(function(){return {api:'https://api.movix.'+MOVIX_FALLBACK}})};module.exports={getStreams:async function(){var e=await detectApi();await fetch(e.api+'/api/purstream/movie/157336/stream');return []}};'''
    output, records = apply_overrides("movix", source)
    assert b"NUVIO_FIXED_ENDPOINT:https://api.movix.fun" in output
    assert b"NUVIO_RUNTIME_DOMAIN_OVERRIDES_V1" in output
    assert b"fetch(DOMAINS_URL)" not in output
    assert any(row.get("type") == "fixed_endpoint" for row in records)
    assert any(row.get("type") == "runtime_domain_overrides" for row in records)
    second, second_records = apply_overrides("movix", output)
    assert second == output
    assert not any(row.get("type") in {"fixed_endpoint", "runtime_domain_overrides"} for row in second_records)
    with tempfile.TemporaryDirectory(prefix="niakvio-overrides-") as tmp:
        target = Path(tmp) / "provider.js"
        target.write_bytes(output)
        subprocess.run(["node", "--check", str(target)], check=True)
        subprocess.run(
            ["node", str(ROOT / "scripts" / "validate_provider_artifact.cjs"), str(target)],
            check=True,
        )


test_obfuscated_runtime_endpoint_override()


def test_runtime_domain_override_rewrites_polyfilled_urls_without_mutating_hostname() -> None:
    source = b'''module.exports={getStreams:async function(){await fetch("https://api.movix.cash/stream");return []}};'''
    output, records = apply_overrides("movix", source, phase="runtime")
    text = output.decode("utf-8")
    assert "NUVIO_RUNTIME_DOMAIN_OVERRIDES_V1" in text
    assert "url.hostname=replacement" in text
    assert any(row.get("type") == "runtime_domain_overrides" for row in records)


test_runtime_domain_override_rewrites_polyfilled_urls_without_mutating_hostname()

print("override pipeline tests passed")
