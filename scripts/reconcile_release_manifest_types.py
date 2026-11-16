#!/usr/bin/env python3
"""Reassert authoritative semantic/transport types after release rematerialization.

This step is intentionally projection-authority-only: provider bytes and proof ledgers are not
rewritten. Global manifest rows receive transport projection while provider_catalog keeps semantic-only capabilities. It closes release-order drift where deterministic rebuild/minimizer/proof
steps can leave a manifest row with stale transport aliases even though
provider-overrides.json still owns the accepted published_types contract.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from reapply_published_overrides import (
    apply_manifest_type_projection,
    configured_authoritative_types,
)

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manifest.json"
OVERRIDES = ROOT / "provider-overrides.json"
CATALOG = ROOT / "provider_catalog.json"


def reconcile_document(manifest: dict[str, Any], config: dict[str, Any]) -> list[str]:
    changed: list[str] = []
    for row in manifest.get("scrapers") or []:
        if not isinstance(row, dict):
            continue
        provider_id = str(row.get("id") or "").strip().casefold()
        if not provider_id:
            continue
        authoritative = configured_authoritative_types(config, provider_id)
        if authoritative and apply_manifest_type_projection(row, authoritative):
            changed.append(provider_id)
    return sorted(set(changed))


def apply_catalog_semantic_types(entry: dict[str, Any], semantic_types: object) -> bool:
    """Store canonical capability in catalog without client transport aliases."""
    semantic: list[str] = []
    for value in semantic_types if isinstance(semantic_types, list) else []:
        item = str(value or "").strip().casefold()
        if item in {"movie", "tv", "anime"} and item not in semantic:
            semantic.append(item)
    before_supported = entry.get("supportedTypes")
    had_canonical = "canonicalSupportedTypes" in entry
    entry["supportedTypes"] = semantic
    entry.pop("canonicalSupportedTypes", None)
    return before_supported != semantic or had_canonical


def reconcile_catalog(catalog: dict[str, Any], config: dict[str, Any]) -> list[str]:
    """Apply authoritative semantic capability to every catalog scraper.

    Global and strict France-only catalog rows are source capability authority.
    Transport-only aliases such as anime->tv belong only to rendered manifests.
    """
    changed: list[str] = []
    for record in catalog.get("providers") or []:
        if not isinstance(record, dict):
            continue
        scraper = record.get("scraper")
        if not isinstance(scraper, dict):
            continue
        provider_id = str(record.get("canonicalId") or scraper.get("id") or "").strip().casefold()
        if not provider_id:
            continue
        authoritative = configured_authoritative_types(config, provider_id)
        if authoritative and apply_catalog_semantic_types(scraper, authoritative):
            changed.append(provider_id)
    return sorted(set(changed))


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    config = json.loads(OVERRIDES.read_text(encoding="utf-8"))
    manifest_changed = reconcile_document(manifest, config)
    catalog_changed = reconcile_catalog(catalog, config)
    if manifest_changed:
        MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if catalog_changed:
        CATALOG.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # Reproject Global transport rows plus strict France-only semantic catalog rows
    # only after both primary authorities consume the same type contract.
    from sync_manifest_projection_rows import sync
    sync(check=False)

    changed = sorted(set(manifest_changed) | set(catalog_changed))
    print(
        "FIELD_RELEASE_MANIFEST_TYPE_RECONCILE "
        f"changed={len(changed)} providers={','.join(changed) if changed else 'none'} "
        f"manifest={len(manifest_changed)} catalog={len(catalog_changed)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
