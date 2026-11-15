#!/usr/bin/env python3
"""Reassert authoritative semantic/transport types after release rematerialization.

This step is intentionally manifest-only: provider bytes and proof ledgers are not
rewritten. It closes release-order drift where deterministic rebuild/minimizer/proof
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


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    config = json.loads(OVERRIDES.read_text(encoding="utf-8"))
    changed = reconcile_document(manifest, config)
    if changed:
        MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # Reproject Global-owned rows into VF/no-anime views without inventing any
    # France-only authority.
    from sync_manifest_projection_rows import sync
    sync(check=False)

    print(
        "FIELD_RELEASE_MANIFEST_TYPE_RECONCILE "
        f"changed={len(changed)} providers={','.join(changed) if changed else 'none'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
