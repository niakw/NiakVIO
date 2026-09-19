#!/usr/bin/env python3
"""Build a bounded provider-agnostic manifest for native Brain candidate retests.

The repair sandbox may mutate at most 24 providers. Retesting the entire canonical
catalogue after those mutations adds hours without increasing mutation confidence.
This helper keeps every actually mutated provider and adds deterministic unchanged
sentinels covering movie, TV and anime when available.
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

MEDIA_TYPES = ("movie", "tv", "anime")


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def provider_id(row: dict[str, Any]) -> str:
    return str(row.get("id") or "").strip().casefold()


def supported_types(row: dict[str, Any]) -> set[str]:
    values = row.get("supportedTypes") or []
    if isinstance(values, str):
        values = [values]
    return {str(value).strip().casefold() for value in values if str(value).strip()}


def build_scope(manifest: dict[str, Any], report: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    rows = [row for row in manifest.get("scrapers") or [] if isinstance(row, dict) and provider_id(row)]
    by_id = {provider_id(row): row for row in rows}

    mutated: list[str] = []
    for value in report.get("providers") or []:
        key = str(value or "").strip().casefold()
        if key and key not in mutated:
            mutated.append(key)
    if not mutated:
        raise ValueError("repair report contains no mutated providers")
    missing = [key for key in mutated if key not in by_id]
    if missing:
        raise ValueError("mutated providers absent from repair manifest: " + ", ".join(missing))

    mutated_set = set(mutated)
    sentinel_ids: list[str] = []
    sentinel_types: dict[str, list[str]] = {}
    unchanged = sorted(
        (row for row in rows if provider_id(row) not in mutated_set and row.get("enabled") is True),
        key=lambda row: provider_id(row),
    )
    for media_type in MEDIA_TYPES:
        candidate = next((row for row in unchanged if media_type in supported_types(row)), None)
        if candidate is None:
            continue
        key = provider_id(candidate)
        if key not in sentinel_ids:
            sentinel_ids.append(key)
        sentinel_types.setdefault(key, []).append(media_type)

    selected_ids = set(mutated + sentinel_ids)
    selected_rows = [copy.deepcopy(row) for row in rows if provider_id(row) in selected_ids]
    selected_rows.sort(key=lambda row: (provider_id(row) not in mutated_set, provider_id(row)))

    output_manifest = copy.deepcopy(manifest)
    output_manifest["scrapers"] = selected_rows
    scope = {
        "schemaVersion": 1,
        "mode": "native_reader_brain_retest",
        "mutatedProviders": mutated,
        "mutationCount": len(mutated),
        "sentinelProviders": sentinel_ids,
        "sentinelTypes": sentinel_types,
        "selectedProviders": [provider_id(row) for row in selected_rows],
        "selectedCount": len(selected_rows),
        "fullCatalogueRetest": False,
        "policy": {
            "allMutatedProvidersRequired": True,
            "unchangedSentinelsSelectedDeterministically": True,
            "sentinelMediaTypes": list(MEDIA_TYPES),
            "providerSpecificExceptions": False,
        },
    }
    return output_manifest, scope


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--repair-report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--scope-output", type=Path, required=True)
    args = parser.parse_args()

    manifest, scope = build_scope(load_json(args.manifest), load_json(args.repair_report))
    write_json(args.output, manifest)
    write_json(args.scope_output, scope)
    print(
        "FIELD_NATIVE_READER_RETEST_SCOPE "
        f"mutated={scope['mutationCount']} sentinels={len(scope['sentinelProviders'])} "
        f"selected={scope['selectedCount']} full_catalogue=false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
