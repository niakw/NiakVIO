#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Build native Nuvio lab cases from the currently published manifest.

Static provider lists hide coverage regressions as the curated manifest evolves.
For push-triggered validation, every fixture must exercise every enabled
provider that declares support for that catalogue category.
"""
from __future__ import annotations

import copy
from typing import Any


def _supported_types(row: dict[str, Any]) -> set[str]:
    return {
        str(value).casefold().strip()
        for value in row.get("supportedTypes") or []
        if str(value).strip()
    }


def _required_type(fixture_row: dict[str, Any]) -> str:
    fixture = fixture_row.get("fixture") if isinstance(fixture_row.get("fixture"), dict) else {}
    category = str(fixture.get("category") or "").casefold().strip()
    media_type = str(fixture.get("mediaType") or "").casefold().strip()
    if category == "anime":
        return "anime"
    if media_type in {"movie", "tv", "anime"}:
        return media_type
    if category in {"movie", "tv", "anime"}:
        return category
    return "movie"


def enabled_provider_ids_for_type(manifest: dict[str, Any], required_type: str) -> list[str]:
    rows = [
        row
        for row in manifest.get("scrapers") or []
        if isinstance(row, dict)
        and row.get("enabled") is True
        and required_type in _supported_types(row)
        and str(row.get("id") or "").strip()
    ]
    return [str(row["id"]) for row in rows]


def expand_push_source(source: dict[str, Any], manifest: dict[str, Any]) -> dict[str, Any]:
    output = copy.deepcopy(source)
    fixtures = []
    for index, row in enumerate(output.get("fixtures") or []):
        if not isinstance(row, dict):
            continue
        item = copy.deepcopy(row)
        required_type = _required_type(item)
        providers = enabled_provider_ids_for_type(manifest, required_type)
        if not providers:
            slug = str(item.get("slug") or f"fixture-{index + 1}")
            raise ValueError(f"fixture {slug}: no enabled providers for type {required_type}")
        item["providers"] = providers
        item["provider_selection"] = "all_enabled_compatible"
        item["provider_count"] = len(providers)
        fixtures.append(item)
    if not fixtures:
        raise ValueError("at least one fixture is required")
    output["fixtures"] = fixtures
    output["provider_selection"] = "all_enabled_compatible"
    return output
