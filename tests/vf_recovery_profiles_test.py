#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "provider-overrides.json"
TARGET = "scripts/provider_patches/nuvio_tv_target_media_v4.py"
RECOVERY = "scripts/provider_patches/vf_catalogue_recovery.py"
SANITIZER = "scripts/provider_patches/stream_output_sanitizer_v5.py"
STRICT_SANITIZER = "scripts/provider_patches/stream_output_sanitizer_v6.py"
DESKTOP = "scripts/provider_patches/desktop_runtime_compat_v1.py"
OLD_DIRECT = "scripts/provider_patches/nuvio_tv_direct_media_v2.py"
FRENCHSTREAM_RAW_TV = "scripts/provider_patches/frenchstream_raw_tv_fallback.py"
COFLIX_EXACT = "scripts/provider_patches/coflix_exact_catalogue.py"
COFLIX_BLOCKED_PATHS = {
    "/wp-admin/",
    "/wp-json/",
    "/wp-content/plugins/ajax-search-lite/",
}


def target_options(provider: dict) -> dict:
    return (provider.get("patch_script_options") or {}).get(TARGET) or {}


def main() -> int:
    data = json.loads(CONFIG.read_text(encoding="utf-8"))
    providers = data["provider_patches"]

    for provider_id in ("streamzo", "frenchstream", "coflix"):
        provider = providers[provider_id]
        scripts = provider.get("patch_scripts") or []
        assert TARGET in scripts, (provider_id, scripts)
        assert DESKTOP in scripts, (provider_id, scripts)
        assert OLD_DIRECT not in scripts, (provider_id, scripts)
        assert scripts.index(TARGET) < scripts.index(DESKTOP), (provider_id, scripts)
        options = target_options(provider)
        assert options.get("force_rewrap_target_media") is True, (provider_id, options)
        assert int(options.get("max_candidates") or 0) >= 20, (provider_id, options)

    coflix = providers["coflix"]
    scripts = coflix.get("patch_scripts") or []
    assert scripts == [RECOVERY, COFLIX_EXACT, TARGET, STRICT_SANITIZER, DESKTOP], scripts
    recovery = (coflix.get("patch_script_options") or {}).get(RECOVERY) or {}
    assert recovery.get("strategy") == "html", recovery
    assert recovery.get("base_url") == "https://coflix.esq", recovery
    assert "/film/{slug}/" in (recovery.get("direct_paths") or []), recovery
    assert "/?s={query}" in (recovery.get("search_paths") or []), recovery
    assert set(recovery.get("types") or []) == {"movie", "tv", "anime"}, recovery
    assert COFLIX_BLOCKED_PATHS.issubset(set(recovery.get("blocked_path_patterns") or [])), recovery
    strict = (coflix.get("patch_script_options") or {}).get(STRICT_SANITIZER) or {}
    assert strict.get("probe_direct_media") is True, strict
    assert strict.get("probe_all_urls") is True, strict
    assert int(strict.get("max_probes") or 0) == 20, strict
    assert COFLIX_BLOCKED_PATHS.issubset(set(strict.get("blocked_path_patterns") or [])), strict
    assert SANITIZER not in scripts, scripts
    assert coflix.get("runtime_domain_replacements", {}).get("coflix.cymru") == "coflix.esq", coflix
    assert coflix.get("manifest_overrides", {}).get("supportsExternalPlayer") is False, coflix
    assert "disabledPlatforms" not in (coflix.get("manifest_overrides") or {}), coflix

    frenchstream = providers["frenchstream"]
    fs_scripts = frenchstream.get("patch_scripts") or []
    assert FRENCHSTREAM_RAW_TV in fs_scripts, fs_scripts
    assert fs_scripts[-4:] == [FRENCHSTREAM_RAW_TV, TARGET, SANITIZER, DESKTOP], fs_scripts
    assert "s1.fsvid.lol" in (target_options(frenchstream).get("blocked_hosts") or []), target_options(frenchstream)

    streamzo = providers["streamzo"]
    sz_scripts = streamzo.get("patch_scripts") or []
    assert sz_scripts[-3:] == [TARGET, SANITIZER, DESKTOP], sz_scripts

    print("VF terminal recovery profile tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
