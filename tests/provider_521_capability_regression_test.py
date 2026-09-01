#!/usr/bin/env python3
"""Prevent silent loss of provider capabilities proven in production 5.21.0."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = json.loads(
    (ROOT / "tests/fixtures/provider-production-5.21.0-capabilities.json").read_text(encoding="utf-8")
)
MANIFEST = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
OVERRIDES = json.loads((ROOT / "provider-overrides.json").read_text(encoding="utf-8"))

rows = {
    str(row.get("id") or "").strip().casefold(): row
    for row in MANIFEST.get("scrapers") or []
    if isinstance(row, dict) and str(row.get("id") or "").strip()
}
caps = OVERRIDES.get("provider_capabilities") or {}


def norm_types(values: object) -> set[str]:
    source = values if isinstance(values, list) else []
    return {
        str(value).strip().casefold()
        for value in source
        if str(value).strip().casefold() in {"movie", "tv", "anime"}
    }


def semantic_types(row: dict) -> set[str]:
    canonical = norm_types(row.get("canonicalSupportedTypes"))
    return canonical or norm_types(row.get("supportedTypes"))


errors: list[str] = []
hls_count = 0

for provider_id, floor in (FIXTURE.get("providers") or {}).items():
    current = rows.get(provider_id)
    if current is None:
        errors.append(f"{provider_id}: provider removed since production 5.21.0")
        continue

    # 5.21.0's supportedTypes sometimes mixed semantic capability with
    # Nuvio transport aliases. semanticTypes is present only for those proven
    # exceptions; otherwise the production 5.21 type set remains the floor.
    explicit_semantic = norm_types(floor.get("semanticTypes"))
    required_types = explicit_semantic or norm_types(floor.get("types"))
    current_types = semantic_types(current)
    if explicit_semantic:
        if current_types != explicit_semantic:
            errors.append(
                f"{provider_id}: semantic type contract drift "
                f"required={sorted(explicit_semantic)} current={sorted(current_types)}"
            )
    else:
        lost = sorted(required_types - current_types)
        if lost:
            errors.append(
                f"{provider_id}: semantic type regression lost={lost} "
                f"required={sorted(required_types)} current={sorted(current_types)}"
            )

    old_formats = {str(value).strip().casefold() for value in floor.get("formats") or []}
    current_formats = {str(value).strip().casefold() for value in current.get("formats") or []}
    if "m3u8" in old_formats:
        hls_count += 1
        if "m3u8" not in current_formats:
            errors.append(
                f"{provider_id}: HLS regression, 5.21.0 advertised m3u8 "
                f"but current formats={sorted(current_formats)}"
            )

    expected_cap = floor.get("capability")
    current_cap = caps.get(provider_id)
    if isinstance(expected_cap, dict):
        if not isinstance(current_cap, dict):
            errors.append(f"{provider_id}: provider capability contract disappeared")
        else:
            for field in ("strategy", "validation", "allow_html_url", "requires_direct_media"):
                expected = expected_cap.get(field)
                if expected is None:
                    continue
                if current_cap.get(field) != expected:
                    errors.append(
                        f"{provider_id}: capability regression {field} "
                        f"expected={expected!r} current={current_cap.get(field)!r}"
                    )

playback = OVERRIDES.get("playback_integrity_policy") or {}
pre = [str(value) for value in playback.get("pre_media_discovery_hooks") or []]
post = [str(value) for value in playback.get("post_media_discovery_hooks") or []]
global_hooks = [str(value) for value in playback.get("global_discovery_hooks") or []]
if pre:
    errors.append(f"pre-media Core must not own HLS validation: {pre!r}")
if post != ["scripts/provider_patches/hls_runtime_integrity_v1.py"]:
    errors.append(f"single post-media HLS owner missing or duplicated: {post!r}")
if "scripts/provider_patches/hls_master_audio_preserver_v1.py" in global_hooks:
    errors.append("retired HLS audio cross-mutator reappeared in global Core")
if "scripts/provider_patches/native_hls_integrity_budget_v1.py" in pre + post + global_hooks:
    errors.append("retired native HLS cross-mutator reappeared in Core")

assert int(FIXTURE.get("provider_count") or 0) == len(FIXTURE.get("providers") or {}), (
    "5.21.0 capability fixture count drift"
)
assert not errors, "5.21.0 production capability regressions:\n- " + "\n- ".join(errors)

print(
    "5.21.0 production capability regression gate passed: "
    f"providers={len(FIXTURE.get('providers') or {})} hls_providers={hls_count}"
)
