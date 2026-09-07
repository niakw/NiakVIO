#!/usr/bin/env python3
"""Apply one already-produced Provider route-proof census without re-running network probes."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import recover_provider_routes_from_upstreams as recovery  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("report", type=Path, nargs="?", default=recovery.OUT)
    args = parser.parse_args()
    path = args.report if args.report.is_absolute() else ROOT / args.report
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit("route recovery report must be an object")
    if int(value.get("schemaVersion") or 0) != recovery.PROOF_VERSION:
        raise SystemExit(f"route recovery proof version={value.get('schemaVersion')}, expected={recovery.PROOF_VERSION}")
    if int(value.get("providerCount") or 0) != recovery.EXPECTED:
        raise SystemExit(f"route recovery providerCount={value.get('providerCount')}, expected={recovery.EXPECTED}")
    providers = value.get("providers") if isinstance(value.get("providers"), list) else []
    if len(providers) != recovery.EXPECTED:
        raise SystemExit(f"route recovery providers rows={len(providers)}, expected={recovery.EXPECTED}")
    summary = recovery.apply_recovery(value)
    value["applied"] = summary
    recovery.write(path, value)
    print(
        "FIELD_ROUTE_RECOVERY_REPORT_APPLIED "
        f"providers={summary['patchedProviders']} routes={summary['provenRoutes']} recipes={summary['apiRecipes']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
