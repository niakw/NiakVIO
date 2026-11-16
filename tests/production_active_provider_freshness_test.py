#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from provider_production_freshness import ProductionFreshnessAuthority, load

authority = ProductionFreshnessAuthority(ROOT)
offline_seen = 0
reactivated_seen = 0
pending_seen = 0

for manifest_path, projection in (
    (ROOT / "manifest.json", "global"),
    (ROOT / "vf" / "manifest.json", "france"),
):
    manifest = load(manifest_path)
    active = [
        row
        for row in manifest.get("scrapers") or []
        if isinstance(row, dict) and row.get("enabled") is not False
    ]
    for row in active:
        provider = str(row.get("id") or "").strip().casefold().replace("_", "-")
        assert provider, (manifest_path, row)
        allowed, proof_authority = authority.authorize(row, projection)
        assert allowed, (
            f"{manifest_path}: active {provider} lacks fresh FULL proof or "
            f"exact-byte production exception proof ({proof_authority})"
        )
        if proof_authority == "offline-contract-exact-byte":
            offline_seen += 1
        elif proof_authority == "disabled-recovery-exact-byte":
            reactivated_seen += 1
        elif proof_authority == "pending-full-exact-byte":
            pending_seen += 1

assert int(authority.all_scope_state.get("artifactHashSchemaVersion") or 0) >= 1, (
    "missing byte-bound all-scope freshness ledger"
)
print(
    "Production active providers require shared byte-bound all-scope FULL OK or exact-byte "
    "activation authority; "
    f"offline_live_unverified_checks={offline_seen} "
    f"reactivation_checks={reactivated_seen} pending_checks={pending_seen}"
)
