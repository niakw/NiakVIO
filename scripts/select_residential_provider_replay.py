#!/usr/bin/env python3
"""Select current harness/network symptoms for full residential provider replay.

The transport differential is useful diagnosis, but it is not a prerequisite
for the authoritative replay: some providers fail before a safe exact GET can
be extracted, or require POST/player/session behavior only the real provider
runtime can reproduce. Once the private residential exit is confirmed active,
replay every *current* provider whose census status is environment/network
blocked and whose provider address/backend still has authority. Domain/lifecycle-
blocked providers stay out of this transport queue. The replay itself remains
the only functional authority.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ELIGIBLE_STATUSES = {
    "HARNESS MISMATCH",
    "CLIENT TRANSPORT GAP",
    "HARNESS/ENV BLOCKED",
    "PROVIDER NETWORK BLOCKED",
}


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(path)
    return value


def select(
    report: dict[str, Any],
    status: dict[str, Any],
    explicit_providers: list[str] | None = None,
) -> list[str]:
    residential = (
        report.get("residentialExitNodeEvidence")
        if isinstance(report.get("residentialExitNodeEvidence"), dict)
        else {}
    )
    if residential.get("available") is not True:
        return []

    rows = [
        row for row in status.get("providers") or []
        if isinstance(row, dict) and str(row.get("provider") or "").strip()
    ]
    providers = {
        str(row.get("provider") or "").strip().casefold()
        for row in rows
        if str(row.get("status") or "") in ELIGIBLE_STATUSES
        and row.get("authorityRepairEligible") is not False
    }

    explicit = {
        str(value or "").strip().casefold()
        for value in (explicit_providers or [])
        if str(value or "").strip()
    }
    if explicit:
        authority_allowed = {
            str(row.get("provider") or "").strip().casefold()
            for row in rows
            if row.get("authorityRepairEligible") is not False
        }
        # An explicit transport qualification is itself the symptom request.
        # Allow the named current provider to full-replay through residential
        # transport even when canonical status is FULL/PARTIAL/ROUTE, while
        # still respecting current provider/address authority.
        providers.update(explicit & authority_allowed)

    return sorted(providers)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--waf", type=Path, required=True)
    ap.add_argument("--status", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--providers", default="", help="Optional comma-separated explicit current providers to full-replay regardless of canonical status")
    args = ap.parse_args()

    explicit = [value.strip() for value in str(args.providers or "").split(",") if value.strip()]
    providers = select(load(args.waf), load(args.status), explicit)
    payload = {
        "schemaVersion": 2,
        "selection": "current-census-harness-network-residential-full-replay",
        "eligibleStatuses": sorted(ELIGIBLE_STATUSES),
        "providers": providers,
        "providerCount": len(providers),
        "explicitProviders": explicit,
    }
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"FIELD_RESIDENTIAL_PROVIDER_REPLAY_SELECTION providers={len(providers)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
