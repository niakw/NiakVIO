#!/usr/bin/env python3
"""Preserve trustworthy 5.21.0 capability evidence without reviving archived providers.

The 5.21.0 fixture predates the strict semantic/transport split. Its `types` field
can therefore contain transport aliases that are not semantic capability proof.
Only explicit `semanticTypes` remains a semantic floor. Providers intentionally
removed from the current 46-provider release must remain present in `provider-old/`
as historical material instead of being silently lost or republished.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CURRENT_PROVIDER_COUNT = 46
HISTORICAL_PROVIDER_COUNT = 50
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
archive_dir = ROOT / "provider-old"
archived_ids = {
    path.name.split("--base--", 1)[0].casefold()
    for path in archive_dir.glob("*--base--*.js")
    if "--base--" in path.name
}


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
archived_count = 0
current_fixture_count = 0

assert len(rows) == CURRENT_PROVIDER_COUNT, f"current release must contain {CURRENT_PROVIDER_COUNT} providers, got {len(rows)}"
fixture_ids = {str(value).strip().casefold() for value in (FIXTURE.get("providers") or {})}
current_ids = set(rows)
fixture_archived = fixture_ids - current_ids
assert len(fixture_archived) == HISTORICAL_PROVIDER_COUNT, (
    f"historical split drift: expected {HISTORICAL_PROVIDER_COUNT}, got {len(fixture_archived)}"
)

for provider_id, floor in (FIXTURE.get("providers") or {}).items():
    provider_id = str(provider_id).strip().casefold()
    current = rows.get(provider_id)
    if current is None:
        archived_count += 1
        if provider_id not in archived_ids:
            errors.append(f"{provider_id}: absent from current release and missing from provider-old history")
        continue

    current_fixture_count += 1
    current_types = semantic_types(current)
    if not current_types:
        errors.append(f"{provider_id}: current semantic capability is empty")

    # Only explicit historical semanticTypes is valid semantic evidence. The
    # legacy `types` field mixed Nuvio transport aliases with actual capability
    # and must not reintroduce fake movie/tv support into the current release.
    explicit_semantic = norm_types(floor.get("semanticTypes"))
    if explicit_semantic and current_types != explicit_semantic:
        errors.append(
            f"{provider_id}: semantic type contract drift "
            f"required={sorted(explicit_semantic)} current={sorted(current_types)}"
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

    if isinstance(floor.get("capability"), dict) and not isinstance(caps.get(provider_id), dict):
        errors.append(f"{provider_id}: current provider capability contract disappeared")

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
assert current_fixture_count == CURRENT_PROVIDER_COUNT, current_fixture_count
assert archived_count == HISTORICAL_PROVIDER_COUNT, archived_count
assert not errors, "5.21.0 production capability regressions:\n- " + "\n- ".join(errors)

print(
    "5.21.0 capability/history regression gate passed: "
    f"current={current_fixture_count} historical={archived_count} hls_current={hls_count}"
)
