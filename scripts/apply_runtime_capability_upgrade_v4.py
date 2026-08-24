#!/usr/bin/env python3
"""Configure the standalone runtime-capability media safety engine repository-wide."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from normalize_fusion_badge_feed import normalize as normalize_fusion_badge_feed
from normalize_runtime_domain_fixed_point import behavior_contract, normalized as normalize_runtime_domain_fixed_point

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manifest.json"
OVERRIDES = ROOT / "provider-overrides.json"
CORE_SAFETY = ROOT / "scripts" / "core_rebuild_safety.py"
CORE_FIXED_POINT = ROOT / "scripts" / "normalize_core_fixed_point_contract.py"
TARGET_ORDER_COMPAT_PATCH = "scripts/provider_patches/native_sync_fetch_target_order_minified_v5.py"
TARGET_ORDER_PATCH = "scripts/provider_patches/native_sync_fetch_target_order_v1.py"
RUNTIME_PATCH = "scripts/provider_patches/runtime_capability_media_safety_v4.py"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def materialize_runtime_domain_fixed_point() -> None:
    """Activate the durable Core scanner before any content-addressed provider rebuild.

    The Core contract normalizer must run again after the owning safety module changes,
    otherwise apply_provider_overrides.py would still contain the previous generated
    scanner for this run. Keeping both operations here makes the expensive 92-provider
    loop consume exactly the implementation that its fixed-point checks are proving.
    """
    current = CORE_SAFETY.read_text(encoding="utf-8")
    expected = normalize_runtime_domain_fixed_point(current)
    changed = expected != current
    if changed:
        CORE_SAFETY.write_text(expected, encoding="utf-8")
    behavior_contract(expected)
    subprocess.run(
        [sys.executable, str(CORE_FIXED_POINT), "--apply"],
        cwd=ROOT,
        check=True,
    )
    print(
        "FIELD_RUNTIME_DOMAIN_FIXED_POINT "
        f"changed={int(changed)} activation=explicit pre_provider_rebuild=true"
    )


def is_hls_entry(entry: dict, policy_targets: set[str]) -> bool:
    provider_id = str(entry.get("id") or "").strip().casefold()
    if provider_id in policy_targets:
        return True
    formats = entry.get("formats") or []
    if isinstance(formats, str):
        formats = [formats]
    return any(str(value).strip().casefold() in {"m3u8", "hls", "mpegurl", "application/vnd.apple.mpegurl"} for value in formats)


def main() -> int:
    materialize_runtime_domain_fixed_point()
    fusion_changed = normalize_fusion_badge_feed(apply=True)
    print(
        "FIELD_FUSION_BADGE_FEED "
        f"changed={int(fusion_changed)} url=https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/stream-badges-fusion.json"
    )

    manifest = load(MANIFEST)
    config = load(OVERRIDES)
    policy = config.get("playback_integrity_policy") if isinstance(config.get("playback_integrity_policy"), dict) else {}
    policy_targets = {str(value).strip().casefold() for value in (policy.get("hls_targets") or []) if str(value).strip()}
    provider_patches = config.setdefault("provider_patches", {})
    targets: list[str] = []
    changed = 0

    for entry in manifest.get("scrapers", []):
        if not isinstance(entry, dict) or not is_hls_entry(entry, policy_targets):
            continue
        provider_id = str(entry.get("id") or "").strip().casefold()
        if not provider_id:
            continue
        targets.append(provider_id)
        row = provider_patches.setdefault(provider_id, {})
        scripts = row.setdefault("patch_scripts", [])
        if not isinstance(scripts, list):
            raise ValueError(f"provider_patches.{provider_id}.patch_scripts must be an array")
        original = list(scripts)
        scripts = [
            script for script in scripts
            if script not in {
                TARGET_ORDER_COMPAT_PATCH,
                TARGET_ORDER_PATCH,
                "scripts/provider_patches/native_sync_fetch_target_order_diag.py",
                RUNTIME_PATCH,
            }
        ]
        scripts.append(TARGET_ORDER_COMPAT_PATCH)
        scripts.append(TARGET_ORDER_PATCH)
        scripts.append(RUNTIME_PATCH)
        if scripts != original:
            row["patch_scripts"] = scripts
            changed += 1

    config["runtime_capability_media_safety"] = {
        "version": 4,
        "scope": "all_hls_capable_providers",
        "target_order_compat_patch": TARGET_ORDER_COMPAT_PATCH,
        "target_order_patch": TARGET_ORDER_PATCH,
        "final_patch": RUNTIME_PATCH,
        "platforms": {
            "desktop_native": "native_quickjs_static_validation_without_extra_media_fetch",
            "mobile_android": "native_quickjs_static_validation_without_extra_media_fetch",
            "tv_android": "prioritized_target_media_traversal_on_synchronous_native_fetch_plus_existing_tv_identity_guards",
            "non_native_web_like": "bounded_media_preflight_when_fetch_is_abortable",
        },
        "native_detection": "presence_of___native_fetch_host_bridge",
        "static_fail_closed": [
            "missing_or_invalid_media_url",
            "youtube_or_embed_page_url",
            "obvious_html_or_php_page_url",
            "malformed_nested_url",
        ],
        "wrapper_upgrade": "Terser-normalized V5 compatibility precedes strict target traversal ordering; final safety patch remains last",
        "targets": sorted(set(targets)),
    }
    dump(OVERRIDES, config)
    print(f"runtime capability upgrade v4 configured: targets={len(set(targets))} changed={changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
