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
import provider_live_request_contract_bridge_v19 as live_request_bridge  # noqa: E402
import runtime_route_plan_cap_v1 as route_policy  # noqa: E402
import runtime_structured_plan_cap_v1 as structured_policy  # noqa: E402
import runtime_execution_authority_cap_v1 as authority_policy  # noqa: E402
from current_provider_scope import active_provider_ids  # noqa: E402


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

    # Provider cardinality is current repository DATA, never a historical constant.
    # The merged repair report consumed here is authoritative only when it covers
    # every currently active provider exactly once. Targeted reports are merged
    # into that full active scope before reaching this apply step.
    expected_ids = active_provider_ids()
    expected = len(expected_ids)
    provider_count = int(value.get("providerCount") or 0)
    if provider_count != expected:
        raise SystemExit(f"route recovery providerCount={provider_count}, expected_active={expected}")
    providers = value.get("providers") if isinstance(value.get("providers"), list) else []
    if len(providers) != expected:
        raise SystemExit(f"route recovery providers rows={len(providers)}, expected_active={expected}")
    report_ids = {
        str((row or {}).get("providerId") or (row or {}).get("provider") or (row or {}).get("id") or "")
        .strip().casefold().replace("_", "-")
        for row in providers if isinstance(row, dict)
    }
    report_ids.discard("")
    if report_ids != expected_ids:
        missing = sorted(expected_ids - report_ids)
        extra = sorted(report_ids - expected_ids)
        raise SystemExit(
            "route recovery active provider identity mismatch "
            f"missing={','.join(missing) or '-'} extra={','.join(extra) or '-'}"
        )

    summary = recovery.apply_recovery(value)
    # V19 cannot invent authority: it runs only after the exact HTTP recovery has
    # been applied and can bridge only a current live-positive request to an exact
    # observed/reviewed request shape.
    bridge_summary = live_request_bridge.apply_recovery_bridge(value)
    route_summary = route_policy.enforce_runtime_route_cap(value)
    structured_summary = structured_policy.enforce_structured_plan_cap()
    authority_summary = authority_policy.enforce_execution_authority_cap()
    value["applied"] = summary
    value["liveRequestContractBridgeV19"] = bridge_summary
    value["runtimeRoutePlanPolicy"] = route_summary
    value["runtimeStructuredPlanPolicy"] = structured_summary
    value["runtimeExecutionAuthorityPolicy"] = authority_summary
    # Remove the old wording so reports cannot imply a universal hard cap.
    value.pop("runtimeRoutePlanCap", None)
    value.pop("runtimeStructuredPlanCap", None)
    value.pop("runtimeExecutionAuthorityCap", None)
    recovery.write(path, value)

    print(
        "FIELD_ROUTE_RECOVERY_REPORT_APPLIED "
        f"active_scope={expected} providers={summary['patchedProviders']} evidence_routes={summary['provenRoutes']} recipes={summary['apiRecipes']} "
        f"v19_bridged_providers={bridge_summary['bridgedProviders']} v19_bridged_plans={bridge_summary['bridgedPlans']} "
        f"normal_entry_target={route_summary['target']} runtime_route_max={route_summary['maxAfter']} "
        f"runtime_optimized={route_summary['optimizedProviders']} runtime_exceptions={route_summary['exceptionProviders']} "
        f"structured_target={structured_summary['target']} structured_max={structured_summary['maxAfter']} "
        f"structured_merged_fields={structured_summary['mergedFields']} structured_exceptions={structured_summary['targetExceededFields']} "
        f"authority_preference_target={authority_summary['target']} authority_candidates_max={authority_summary['maxCandidates']} "
        f"authority_preferred_max={authority_summary['maxPreferred']} multi_authority={authority_summary['multiAuthorityProviders']}"
    )
    # Correctness failures remain strict (invalid report/catalogue/proof), but a
    # provider is never rejected merely because its proven protocol needs >3
    # distinct top-level plans or more downstream player/source branches.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
