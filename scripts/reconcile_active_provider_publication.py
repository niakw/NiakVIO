#!/usr/bin/env python3
"""Reconcile final Global publication and Global+France materialization authority.

The release finalizer minimizes content-addressed provider bytes after the canonical
materialization ledger is built. Global rows are rebound through the canonical
publication reconciler, then the complete executable Global+France union is rebound
to the exact final bytes before version/cache finalization.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from reconcile_targeted_provider_publication import reconcile
from reconcile_provider_static_authority import reconcile_materialization_from_active_bundles
from sync_manifest_projection_rows import sync as sync_projection_rows

ROOT = Path(__file__).resolve().parents[1]


def active_global_ids(root: Path = ROOT) -> list[str]:
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    return [
        str(row.get("id") or "").strip().casefold().replace("_", "-")
        for row in manifest.get("scrapers") or []
        if isinstance(row, dict)
        and row.get("enabled") is not False
        and str(row.get("id") or "").strip()
    ]


def main() -> int:
    providers = active_global_ids()
    if not providers:
        raise RuntimeError("no active Global providers to reconcile")
    updates = reconcile(ROOT, providers, sync_projections=sync_projection_rows)
    materialization = reconcile_materialization_from_active_bundles(apply=True)
    print(
        "FIELD_ACTIVE_PUBLICATION_FIXED_POINT "
        f"providers={len(providers)} updates={len(updates)} "
        f"union_recovered={materialization['recoveredCount']} "
        f"union_rebound={materialization['reboundCount']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
