#!/usr/bin/env python3
"""Keep universal HLS validation/enrichment and short-placeholder policy at its current contract.

The HLS Block already fetches the master playlist for bounded integrity checks.
Reuse that same response for technical facts instead of maintaining provider-only
opt-ins. This script is intentionally idempotent and may be run by the short CI.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HLS = ROOT / "scripts/provider_patches/hls_runtime_integrity_v1.py"
OVERRIDES = ROOT / "provider-overrides.json"

POLICY = {
    "timeout_ms": 6500,
    "max_children": 2,
    "probe_first_segment_native": True,
    "native_probe_max_rows": 8,
    "native_probe_timeout_ms": 2500,
    "minimum_vod_duration_seconds": 90,
    "short_static_media_seconds": 30,
    "inspect_master_facts": True,
    "drop_unprobed_hls_after_budget": True,
}


def patch_overrides() -> bool:
    data = json.loads(OVERRIDES.read_text(encoding="utf-8"))
    playback = data.setdefault("playback_integrity_policy", {})
    changed = False
    if playback.get("version") != 5:
        playback["version"] = 5
        changed = True
    options = playback.setdefault("hls_runtime_options", {})
    for key, value in POLICY.items():
        if options.get(key) != value:
            options[key] = value
            changed = True
    wanted_probe = "bounded_native_hls_playlist_segment_validation_and_master_fact_enrichment"
    if playback.get("native_hls_probe_policy") != wanted_probe:
        playback["native_hls_probe_policy"] = wanted_probe
        changed = True
    wanted_facts = "reuse_already_fetched_master_resolution_bandwidth_codecs_framerate_range_audio_subtitles"
    if playback.get("hls_master_fact_policy") != wanted_facts:
        playback["hls_master_fact_policy"] = wanted_facts
        changed = True

    media = data.setdefault("runtime_capability_media_safety", {})
    media_options = media.setdefault("options", {})
    if media_options.get("min_vod_duration_seconds") != 60:
        media_options["min_vod_duration_seconds"] = 60
        changed = True

    keh = data.setdefault("provider_patches", {}).setdefault("kehflix", {})
    core = keh.setdefault("core_options", {})
    hls = core.setdefault("hls_runtime_integrity", {})
    for key, value in {
        "probe_first_segment_native": True,
        "native_probe_max_rows": 8,
        "native_probe_timeout_ms": 2500,
        "inspect_master_facts": True,
    }.items():
        if hls.get(key) != value:
            hls[key] = value
            changed = True

    if changed:
        OVERRIDES.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return changed


def verify_source() -> None:
    source = HLS.read_text(encoding="utf-8")
    for needle in (
        'cfg.get("inspect_master_facts", True)',
        '"implementationRevision": "native-master-facts-v11"',
        "function masterFacts(body)",
        "AVERAGE-BANDWIDTH",
        "FRAME-RATE",
        "VIDEO-RANGE",
        "dropUnprobedHlsAfterBudget",
        "shortStaticMedia",
    ):
        if needle not in source:
            raise AssertionError(f"HLS universal Block missing {needle}")


def main() -> int:
    verify_source()
    changed = patch_overrides()
    print(f"HLS_MASTER_FACTS_V2_OK changed={str(changed).lower()} global=1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
