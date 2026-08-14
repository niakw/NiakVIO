#!/usr/bin/env python3
"""Install the runtime-capability-aware media safety engine across published HLS providers.

This is repository-wide engine configuration, not a StreamZo special case. It ensures
all HLS-capable providers run the wrapper migration immediately before the current
media-safety wrapper, so published v1/v2 wrappers cannot survive indefinitely.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manifest.json"
OVERRIDES = ROOT / "provider-overrides.json"
MIGRATION_PATCH = "scripts/provider_patches/runtime_media_safety_migration_v1.py"
SAFETY_PATCH = "scripts/provider_patches/hls_master_audio_preserver_v1.py"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def is_hls_entry(entry: dict, policy_targets: set[str]) -> bool:
    provider_id = str(entry.get("id") or "").strip().casefold()
    if provider_id in policy_targets:
        return True
    formats = entry.get("formats") or []
    if isinstance(formats, str):
        formats = [formats]
    return any(str(value).strip().casefold() in {"m3u8", "hls", "mpegurl", "application/vnd.apple.mpegurl"} for value in formats)


def main() -> int:
    manifest = load(MANIFEST)
    config = load(OVERRIDES)
    policy = config.get("playback_integrity_policy") if isinstance(config.get("playback_integrity_policy"), dict) else {}
    policy_targets = {str(value).strip().casefold() for value in (policy.get("hls_targets") or []) if str(value).strip()}
    patches = config.setdefault("provider_patches", {})
    changed = 0
    targets: list[str] = []

    for entry in manifest.get("scrapers", []):
        if not isinstance(entry, dict) or not is_hls_entry(entry, policy_targets):
            continue
        provider_id = str(entry.get("id") or "").strip().casefold()
        if not provider_id:
            continue
        targets.append(provider_id)
        row = patches.setdefault(provider_id, {})
        scripts = row.setdefault("patch_scripts", [])
        if not isinstance(scripts, list):
            raise ValueError(f"provider_patches.{provider_id}.patch_scripts must be an array")
        original = list(scripts)
        scripts = [script for script in scripts if script not in {MIGRATION_PATCH, SAFETY_PATCH}]
        scripts.extend([MIGRATION_PATCH, SAFETY_PATCH])
        if scripts != original:
            row["patch_scripts"] = scripts
            changed += 1

    config["runtime_capability_media_safety"] = {
        "version": 3,
        "scope": "all_hls_capable_providers",
        "platforms": {
            "desktop": "bounded_remote_preflight_when_abortable",
            "mobile_android": "native_quickjs_no_extra_media_probe",
            "tv_android": "native_quickjs_no_extra_media_probe_plus_tv_identity_guards",
        },
        "static_fail_closed": [
            "missing_or_invalid_media_url",
            "youtube_or_embed_page_url",
            "obvious_html_or_php_page_url",
            "malformed_nested_url",
        ],
        "published_wrapper_migration": "strip_previous_global_media_safety_then_apply_current_once",
        "targets": sorted(set(targets)),
    }
    dump(OVERRIDES, config)
    print(f"runtime capability upgrade v3 configured: targets={len(set(targets))} changed={changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
