#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlparse

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
TV_PLAYABLE_FIRST = "scripts/provider_patches/nuvio_tv_playable_first_v1.py"
QUARANTINE = "scripts/provider_patches/quarantine_provider_v1.py"
NATIVE_TARGET_ORDER_COMPAT = "scripts/provider_patches/native_sync_fetch_target_order_minified_v5.py"
NATIVE_TARGET_ORDER = "scripts/provider_patches/native_sync_fetch_target_order_v1.py"
RUNTIME_MEDIA_SAFETY = "scripts/provider_patches/runtime_capability_media_safety_v4.py"
PROVIDER_RUNTIME_TAIL = [
    NATIVE_TARGET_ORDER_COMPAT,
    NATIVE_TARGET_ORDER,
]
COFLIX_BLOCKED_PATHS = {
    "/wp-admin/",
    "/wp-json/",
    "/wp-content/plugins/ajax-search-lite/",
}


def target_options(provider: dict) -> dict:
    return (provider.get("patch_script_options") or {}).get(TARGET) or {}


def provider_profile(scripts: list[str], provider_id: str) -> list[str]:
    """Return provider-owned recovery after validating its optional runtime-order tail.

    Media safety is a Core-global invariant and must never be materialized in
    provider_patches.patch_scripts. Only the two provider-scoped native target
    ordering adapters may form an optional trailing pair here.
    """
    assert RUNTIME_MEDIA_SAFETY not in scripts, (provider_id, scripts)
    counts = {path: scripts.count(path) for path in PROVIDER_RUNTIME_TAIL}
    present = [path for path, count in counts.items() if count]
    if not present:
        return list(scripts)
    assert present == PROVIDER_RUNTIME_TAIL, (provider_id, scripts, counts)
    assert all(count == 1 for count in counts.values()), (provider_id, scripts, counts)
    assert scripts[-len(PROVIDER_RUNTIME_TAIL):] == PROVIDER_RUNTIME_TAIL, (provider_id, scripts)
    return scripts[:-len(PROVIDER_RUNTIME_TAIL)]


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
        provider_profile(scripts, provider_id)
        options = target_options(provider)
        assert options.get("force_rewrap_target_media") is True, (provider_id, options)
        assert int(options.get("max_candidates") or 0) >= 20, (provider_id, options)

    coflix = providers["coflix"]
    scripts = coflix.get("patch_scripts") or []
    coflix_profile = provider_profile(scripts, "coflix")
    assert coflix_profile == [RECOVERY, COFLIX_EXACT, TARGET, STRICT_SANITIZER, DESKTOP], scripts
    recovery = (coflix.get("patch_script_options") or {}).get(RECOVERY) or {}
    assert recovery.get("strategy") == "html", recovery
    official_site = coflix.get("official_site")
    assert isinstance(official_site, str) and official_site.strip(), coflix
    recovery_base = recovery.get("base_url")
    assert isinstance(recovery_base, str) and recovery_base.strip(), recovery
    assert recovery_base.rstrip("/") == official_site.rstrip("/"), (recovery, official_site)
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
    official_host = (urlparse(official_site).hostname or "").casefold()
    legacy_target = (coflix.get("runtime_domain_replacements") or {}).get("coflix.cymru")
    if legacy_target is not None:
        assert isinstance(legacy_target, str) and legacy_target.strip(), coflix
        assert legacy_target.casefold().strip(".") == official_host, (coflix, official_site)
    assert coflix.get("manifest_overrides", {}).get("supportsExternalPlayer") is False, coflix
    assert "disabledPlatforms" not in (coflix.get("manifest_overrides") or {}), coflix

    frenchstream = providers["frenchstream"]
    fs_scripts = frenchstream.get("patch_scripts") or []
    fs_profile = provider_profile(fs_scripts, "frenchstream")
    assert FRENCHSTREAM_RAW_TV in fs_profile, fs_scripts
    assert fs_profile[-5:] == [FRENCHSTREAM_RAW_TV, TARGET, SANITIZER, DESKTOP, QUARANTINE], fs_scripts
    assert frenchstream.get("manifest_overrides", {}).get("enabled") is False, frenchstream
    assert "s1.fsvid.lol" in (target_options(frenchstream).get("blocked_hosts") or []), target_options(frenchstream)

    streamzo = providers["streamzo"]
    sz_scripts = streamzo.get("patch_scripts") or []
    sz_profile = provider_profile(sz_scripts, "streamzo")
    assert sz_profile == [TARGET, SANITIZER, DESKTOP, TV_PLAYABLE_FIRST], sz_scripts
    assert not [path for path in sz_scripts if "/streamzo_" in path], sz_scripts
    shared = (streamzo.get("patch_script_options") or {}).get("scripts/provider_patches/global_catalogue_alias_recovery_v2.py") or {}
    assert shared.get("mirror_routes") == ["/api/mirrors/film/{id}"], shared

    print("VF terminal recovery profile tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
