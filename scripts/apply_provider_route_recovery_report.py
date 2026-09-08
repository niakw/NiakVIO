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
import runtime_route_plan_cap_v1 as route_cap  # noqa: E402
import runtime_structured_plan_cap_v1 as structured_cap  # noqa: E402
import runtime_execution_authority_cap_v1 as authority_cap  # noqa: E402


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
    route_summary = route_cap.enforce_runtime_route_cap(value)
    structured_summary = structured_cap.enforce_structured_plan_cap()
    authority_summary = authority_cap.enforce_execution_authority_cap()
    value["applied"] = summary
    value["runtimeRoutePlanCap"] = route_summary
    value["runtimeStructuredPlanCap"] = structured_summary
    value["runtimeExecutionAuthorityCap"] = authority_summary
    recovery.write(path, value)

    print(
        "FIELD_ROUTE_RECOVERY_REPORT_APPLIED "
        f"providers={summary['patchedProviders']} evidence_routes={summary['provenRoutes']} recipes={summary['apiRecipes']} "
        f"runtime_route_cap={route_summary['cap']} runtime_route_max={route_summary['maxAfter']} "
        f"runtime_route_capped_providers={route_summary['cappedProviders']} "
        f"structured_cap={structured_summary['cap']} structured_max={structured_summary['maxAfter']} "
        f"structured_capped_fields={structured_summary['cappedFields']} structured_merged_fields={structured_summary['mergedFields']} "
        f"authority_cap={authority_summary['cap']} authority_max={authority_summary['maxSelected']} "
        f"authority_changed={authority_summary['changedProviders']}"
    )
    if int(route_summary.get("maxAfter") or 0) > route_cap.MAX_RUNTIME_ROUTE_PLANS:
        raise SystemExit(
            f"runtime route plan cap exceeded: max={route_summary['maxAfter']} cap={route_cap.MAX_RUNTIME_ROUTE_PLANS}"
        )
    if int(structured_summary.get("maxAfter") or 0) > structured_cap.MAX_STRUCTURED_PLANS:
        raise SystemExit(
            f"structured runtime plan cap exceeded: max={structured_summary['maxAfter']} cap={structured_cap.MAX_STRUCTURED_PLANS}"
        )
    if int(authority_summary.get("maxSelected") or 0) > authority_cap.MAX_AUTHORITIES:
        raise SystemExit(
            f"runtime execution authority cap exceeded: max={authority_summary['maxSelected']} cap={authority_cap.MAX_AUTHORITIES}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
