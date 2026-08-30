#!/usr/bin/env python3
"""Guard the provider capabilities that were proven in production at NiakVIO 5.21.0."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASELINE = json.loads((ROOT / "provider-capability-lkg-5.21.0.json").read_text(encoding="utf-8"))
MANIFEST = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
OVERRIDES = json.loads((ROOT / "provider-overrides.json").read_text(encoding="utf-8"))


def normalize_types(values: object) -> set[str]:
    iterable = values if isinstance(values, list) else []
    return {
        str(value).strip().casefold()
        for value in iterable
        if str(value).strip().casefold() in {"movie", "tv", "anime"}
    }


def semantic_types(row: dict) -> set[str]:
    canonical = normalize_types(row.get("canonicalSupportedTypes"))
    return canonical or normalize_types(row.get("supportedTypes"))


rows = {
    str(row.get("id") or "").strip().casefold(): row
    for row in MANIFEST.get("scrapers") or []
    if isinstance(row, dict) and str(row.get("id") or "").strip()
}
caps = OVERRIDES.get("provider_capabilities") or {}

missing = []
type_regressions = []
hls_regressions = []
capability_regressions = []

for provider_id, floor in (BASELINE.get("providers") or {}).items():
    row = rows.get(provider_id)
    if row is None:
        missing.append(provider_id)
        continue

    required_types = normalize_types(floor.get("supportedTypes"))
    current_types = semantic_types(row)
    lost_types = sorted(required_types - current_types)
    if lost_types:
        type_regressions.append({
            "provider": provider_id,
            "required": sorted(required_types),
            "current": sorted(current_types),
            "lost": lost_types,
        })

    old_formats = {str(value).strip().casefold() for value in floor.get("formats") or []}
    new_formats = {str(value).strip().casefold() for value in row.get("formats") or []}
    if "m3u8" in old_formats and "m3u8" not in new_formats:
        hls_regressions.append({
            "provider": provider_id,
            "required": "m3u8",
            "current": sorted(new_formats),
        })

    old_cap = floor.get("capability")
    if isinstance(old_cap, dict):
        current = caps.get(provider_id)
        if not isinstance(current, dict):
            capability_regressions.append({
                "provider": provider_id,
                "reason": "missing_current_capability",
            })
            continue
        for key in ("strategy", "validation", "allow_html_url", "requires_direct_media"):
            expected = old_cap.get(key)
            if expected is None:
                continue
            if current.get(key) != expected:
                capability_regressions.append({
                    "provider": provider_id,
                    "field": key,
                    "expected": expected,
                    "current": current.get(key),
                })

assert not missing, f"5.21.0 providers disappeared from current manifest: {missing}"
assert not type_regressions, f"semantic type regressions from 5.21.0: {type_regressions}"
assert not hls_regressions, f"HLS format regressions from 5.21.0: {hls_regressions}"
assert not capability_regressions, (
    f"provider capability regressions from 5.21.0: {capability_regressions}"
)

print(
    "5.21.0 provider capability floor passed: "
    f"providers={len(BASELINE.get('providers') or {})} "
    f"hls={sum('m3u8' in {str(v).casefold() for v in row.get('formats') or []} for row in (BASELINE.get('providers') or {}).values())}"
)
