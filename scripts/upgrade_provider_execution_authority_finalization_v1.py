#!/usr/bin/env python3
"""Keep final Provider DATA bounded by the candidate bundle's actual execution authority.

The strict sequential gate may observe many successful provider-internal requests while
executing a good candidate bundle. Those observations are valuable evidence, but stale
candidateRouteData rows must not silently become top-level executable routes during
finalization when Proof-v5 provider-overrides already defines a narrower execution plan.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts" / "validate_provider_v3_routes_sequential.py"
MARKER = "PROVIDER_V3_CANDIDATE_EXECUTION_AUTHORITY_FINALIZATION_V1"

OLD = '''    stable_candidate_rows = [
        copy.deepcopy(row)
        for row in evaluation["candidateRouteData"]
        if isinstance(row, dict)
        and str(row.get("route") or "").strip()
        and not row.get("liveDerived")
    ]
'''

NEW = '''    # PROVIDER_V3_CANDIDATE_EXECUTION_AUTHORITY_FINALIZATION_V1
    # Finalization must start from the routes that the candidate bundle actually
    # executed, not from every historical/static candidateRouteData row. Proof-v5
    # provider overrides are the current execution authority used by the materializer;
    # widening from stale/internal candidate rows here can make a playable candidate
    # turn into wrong_content after rematerialization (AnimeKai class regression).
    patch_route_proof = int(patch.get("route_proof_version") or 0) if isinstance(patch, dict) else 0
    patch_execution_routes = unique(
        patch.get("learned_routes") or [] if isinstance(patch, dict) else [],
        256,
    )
    candidate_execution_order = (
        patch_execution_routes
        if patch_route_proof >= 5
        else unique(model.get("routes") or [], 256)
    )
    candidate_execution_set = set(candidate_execution_order)
    candidate_execution_rank = {
        route: index for index, route in enumerate(candidate_execution_order)
    }
    stable_candidate_rows = [
        copy.deepcopy(row)
        for row in evaluation["candidateRouteData"]
        if isinstance(row, dict)
        and str(row.get("route") or "").strip() in candidate_execution_set
        and not row.get("liveDerived")
    ]
    stable_candidate_rows.sort(
        key=lambda row: candidate_execution_rank.get(str(row.get("route") or "").strip(), 10**9)
    )
'''


def patch() -> bool:
    text = TARGET.read_text(encoding="utf-8")
    if MARKER in text:
        validate()
        return False
    if text.count(OLD) != 1:
        raise AssertionError("candidate stable-row finalization owner not found exactly once")
    TARGET.write_text(text.replace(OLD, NEW, 1), encoding="utf-8")
    validate()
    return True


def validate() -> None:
    text = TARGET.read_text(encoding="utf-8")
    required = (
        MARKER,
        'patch_route_proof = int(patch.get("route_proof_version") or 0)',
        'candidate_execution_set = set(candidate_execution_order)',
        'str(row.get("route") or "").strip() in candidate_execution_set',
        'candidate_execution_rank.get(',
    )
    missing = [item for item in required if item not in text]
    if missing:
        raise AssertionError("execution-authority finalization migration missing: " + ",".join(missing))


def main() -> int:
    changed = patch()
    print(
        "PROVIDER_V3_EXECUTION_AUTHORITY_FINALIZATION_V1_OK "
        f"changed={str(changed).lower()} proof_v5_candidate_plan=upper-bound "
        "runtime_internal_rows=evidence-only-unless-safe-derived"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
