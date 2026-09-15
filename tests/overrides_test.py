#!/usr/bin/env python3
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from apply_provider_overrides import apply_overrides  # noqa: E402
from provider_v3_core import clean_v3, ensure_contract, validate_with_report  # noqa: E402


def test_movix_override_pipeline() -> None:
    upstream = clean_v3(b'''/* provider */\nconst API="https://api.movix.cash";\nfunction get(){return API;}\n''')
    output, patch_records = apply_overrides("movix", upstream, include_global_core=False)
    assert output != upstream
    assert b"api.movix.fun" in output
    assert b"api.movix.cash" not in output
    ensure_contract(output)
    report = validate_with_report(output, materialization_context="candidate")
    assert report.get("status") == "valid", report
    assert any(row.get("type") == "replace" for row in patch_records)

    with tempfile.TemporaryDirectory() as tmp:
        stage = Path(tmp)
        (stage / "providers" / "gowaru").mkdir(parents=True)
        local = stage / "providers" / "gowaru" / "movix.js"
        local.write_bytes(output)
        registry = {
            "schema_version": 2,
            "candidate_count": 1,
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
    # Current live/site authority is purstream.ad. purstream.mx remains a known
    # runtime/domain-history fallback and must not be confused with official_site.
    assert urlsplit(site).hostname == "purstream.ad", site
    assert urlsplit(api).hostname == "api.purstream.ad", api
    runtime_domains = purstream.get("runtime_domain_replacements") or {}
    assert isinstance(runtime_domains, dict) and runtime_domains
    replacement_hosts = {urlsplit(value if "://" in str(value) else f"https://{value}").hostname for value in runtime_domains.values()}
    assert "purstream.mx" in replacement_hosts and "api.purstream.ad" in replacement_hosts, replacement_hosts
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
    assert any(row.get("type") == "global_compat" for row in patch_records)


def test_provider_specific_patches_are_scoped() -> None:
    source = clean_v3(b'''const BASE="https://example.invalid";\nfunction get(){return BASE;}\n''')
    output, patch_records = apply_overrides("example-provider", source, include_global_core=False)
    assert output == source
    assert patch_records == []


def test_global_core_can_be_disabled() -> None:
    source = clean_v3(b'''function get(){return "https://example.invalid";}\n''')
    output, patch_records = apply_overrides("example-provider", source, include_global_core=False)
    assert output == source
    assert patch_records == []


def test_no_bare_regexp_lookbehind() -> None:
    config = json.loads((ROOT / "provider-overrides.json").read_text(encoding="utf-8"))
    for provider, patch in (config.get("provider_patches") or {}).items():
        for key, value in patch.items():
            if isinstance(value, str):
                assert "(?<=" not in value and "(?<!" not in value, (provider, key)


def test_runtime_domain_replacements_are_strings() -> None:
    config = json.loads((ROOT / "provider-overrides.json").read_text(encoding="utf-8"))
    for provider, patch in (config.get("provider_patches") or {}).items():
        replacements = patch.get("runtime_domain_replacements") or {}
        assert isinstance(replacements, dict), provider
        for old, new in replacements.items():
            assert isinstance(old, str) and old.strip(), (provider, old)
            assert isinstance(new, str) and new.strip(), (provider, new)


def test_provider_lego_scripts_exist() -> None:
    config = json.loads((ROOT / "provider-overrides.json").read_text(encoding="utf-8"))
    for provider, patch in (config.get("provider_patches") or {}).items():
        for script in patch.get("provider_lego_scripts") or []:
            assert (ROOT / script).is_file(), (provider, script)


def test_patch_scripts_exist() -> None:
    config = json.loads((ROOT / "provider-overrides.json").read_text(encoding="utf-8"))
    for provider, patch in (config.get("provider_patches") or {}).items():
        for script in patch.get("patch_scripts") or []:
            assert (ROOT / script).is_file(), (provider, script)


def test_manifest_override_enabled_is_boolean() -> None:
    config = json.loads((ROOT / "provider-overrides.json").read_text(encoding="utf-8"))
    for provider, patch in (config.get("provider_patches") or {}).items():
        overrides = patch.get("manifest_overrides") or {}
        if "enabled" in overrides:
            assert isinstance(overrides["enabled"], bool), provider


def test_declared_hub_is_http_url() -> None:
    config = json.loads((ROOT / "provider-overrides.json").read_text(encoding="utf-8"))
    for provider, patch in (config.get("provider_patches") or {}).items():
        hub = str(patch.get("official_hub") or "").strip()
        if not hub:
            continue
        parsed = urlsplit(hub)
        assert parsed.scheme in {"http", "https"} and parsed.hostname, (provider, hub)


def test_official_site_is_http_url() -> None:
    config = json.loads((ROOT / "provider-overrides.json").read_text(encoding="utf-8"))
    for provider, patch in (config.get("provider_patches") or {}).items():
        site = str(patch.get("official_site") or "").strip()
        if not site:
            continue
        parsed = urlsplit(site)
        assert parsed.scheme in {"http", "https"} and parsed.hostname, (provider, site)


def test_official_api_is_http_url() -> None:
    config = json.loads((ROOT / "provider-overrides.json").read_text(encoding="utf-8"))
    for provider, patch in (config.get("provider_patches") or {}).items():
        api = str(patch.get("official_api") or "").strip()
        if not api:
            continue
        parsed = urlsplit(api)
        assert parsed.scheme in {"http", "https"} and parsed.hostname, (provider, api)


def test_manifest_override_enabled_matches_current_policy() -> None:
    config = json.loads((ROOT / "provider-overrides.json").read_text(encoding="utf-8"))
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    rows = {
        str(row.get("id") or "").strip().casefold().replace("_", "-"): row
        for row in manifest.get("scrapers") or []
        if isinstance(row, dict) and row.get("id")
    }
    for provider, patch in (config.get("provider_patches") or {}).items():
        if provider not in rows:
            continue
        overrides = patch.get("manifest_overrides") or {}
        if "enabled" in overrides:
            assert bool(overrides["enabled"]) is bool(rows[provider].get("enabled")), provider


def main() -> int:
    test_movix_override_pipeline()
    test_domain_overrides()
    test_runtime_profiles_are_not_blindly_applied()
    test_provider_specific_patches_are_scoped()
    test_global_core_can_be_disabled()
    test_no_bare_regexp_lookbehind()
    test_runtime_domain_replacements_are_strings()
    test_provider_lego_scripts_exist()
    test_patch_scripts_exist()
    test_manifest_override_enabled_is_boolean()
    test_declared_hub_is_http_url()
    test_official_site_is_http_url()
    test_official_api_is_http_url()
    test_manifest_override_enabled_matches_current_policy()
    print("provider override tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
