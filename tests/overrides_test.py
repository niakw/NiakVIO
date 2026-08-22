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
    # providers below.
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

    # Discovery-time Core finalization is intentionally universal. This test is
    # only about runtime repair profiles: matching their old structural markers
    # must never auto-apply a provider-specific runtime mutation. We assert the
    # final bundle contract itself rather than an internal patch-record ordering.
    assert output != source
    assert b"NUVIO_GLOBAL_STREAM_FACTS_V1" in output
    assert b"NUVIO_GLOBAL_STREAM_IDENTITY_V1" in output
    assert b"NUVIO_GLOBAL_STREAM_PRESENTATION_V1" in output
    assert not any(row.get("type") == "patch_profile" for row in patch_records)


def test_runtime_domain_prefix_collisions_are_globally_idempotent() -> None:
    """Every configured host-prefix collision must be byte-idempotent.

    This is a Core override-engine contract, not a provider-specific repair. The
    fixture set is discovered from provider-overrides.json so adding a new
    provider with overlapping historical domains automatically extends coverage.
    """
    config = json.loads((ROOT / "provider-overrides.json").read_text())
    patches = config.get("provider_patches") or {}
    exercised = 0

    for provider_id, patch in patches.items():
        if not isinstance(patch, dict):
            continue
        replacements = patch.get("runtime_domain_replacements") or patch.get("replacements") or {}
        if not isinstance(replacements, dict) or len(replacements) < 2:
            continue

        old_hosts = [str(value).strip().lower().rstrip("/") for value in replacements if str(value).strip()]
        collisions = [
            host
            for host in old_hosts
            if any(other != host and other.startswith(host) for other in old_hosts)
        ]
        if not collisions:
            continue

        for old_host in sorted(set(collisions)):
            target_host = str(replacements.get(old_host) or "").strip().lower().rstrip("/")
            if not target_host or target_host == old_host:
                continue
            exercised += 1
            source = f'const BASE="https://{old_host}/";'.encode()
            first, first_records = apply_overrides(provider_id, source, phase="runtime")
            assert f"https://{target_host}/".encode() in first, (provider_id, old_host, target_host)
            assert any(
                row.get("type") == "replace" and row.get("from") == old_host
                for row in first_records
            ), (provider_id, old_host, first_records)

            second, second_records = apply_overrides(provider_id, first, phase="runtime")
            assert second == first, f"runtime domain override is not idempotent for {provider_id}:{old_host}"
            assert not any(
                row.get("type") == "replace" and row.get("from") == old_host
                for row in second_records
            ), (provider_id, old_host, second_records)

    assert exercised > 0, "expected at least one configured runtime-domain prefix collision fixture"


test_staged_artifact_contract()
test_domain_overrides()
test_runtime_profiles_are_not_blindly_applied()
test_runtime_domain_prefix_collisions_are_globally_idempotent()


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
