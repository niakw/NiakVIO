#!/usr/bin/env python3
"""Promote only reusable, live-proven runtime-derived routes into Provider v3 DATA.

V1 intentionally kept every runtime-derived URL evidence-only to prevent session,
signed, and fixture-specific URLs from polluting final DATA. That rule is too broad
for providers whose stable API contract is discovered at runtime (for example
`/?tmdbId={tmdbId}&type=movie`).

V2 keeps the safety boundary: a runtime-derived row is promotable only when it is
live-validated, explicitly reusable, has no fixture-specific residue, and contains
at least one placeholder proving it is a template rather than a captured literal URL.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts" / "validate_provider_v3_routes_sequential.py"
MARKER = "PROVIDER_V3_SAFE_RUNTIME_ROUTE_PROMOTION_V2"


def once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise AssertionError(f"{label}: expected one exact anchor, got {count}")
    return text.replace(old, new, 1)


def patch() -> bool:
    text = TARGET.read_text(encoding="utf-8")
    if MARKER in text:
        validate(text)
        return False

    old_rows = '''    runtime_derived_rows = [
        copy.deepcopy(row)
        for row in evaluation["candidateRouteData"]
        if isinstance(row, dict)
        and str(row.get("route") or "").strip()
        and row.get("liveDerived")
    ]
    if completion_state in {"terminal-blocked", "terminal-unreachable"}:
'''
    new_rows = '''    runtime_derived_rows = [
        copy.deepcopy(row)
        for row in evaluation["candidateRouteData"]
        if isinstance(row, dict)
        and str(row.get("route") or "").strip()
        and row.get("liveDerived")
    ]
    # PROVIDER_V3_SAFE_RUNTIME_ROUTE_PROMOTION_V2
    # Runtime-derived does not automatically mean volatile. A route template may
    # be discovered from live execution and still be safe Provider DATA when its
    # derivation proves that all fixture-specific values were abstracted away.
    safe_runtime_derived_rows = [
        copy.deepcopy(row)
        for row in runtime_derived_rows
        if row.get("validationState") == "live-validated"
        and isinstance(row.get("derivation"), dict)
        and row["derivation"].get("reusable") is True
        and not (row["derivation"].get("fixtureSpecificValues") or [])
        and "{" in str(row.get("route") or "")
        and "}" in str(row.get("route") or "")
    ]
    if completion_state in {"terminal-blocked", "terminal-unreachable"}:
'''
    text = once(text, old_rows, new_rows, "safe-runtime-derived-classification")

    old_plan = '''    elif completion_state == "declared-types-qualified":
        execution_plan_rows = [
            row for row in stable_candidate_rows
            if row.get("attemptEvidence")
            or row.get("validationState") == "live-validated"
        ]
    else:
'''
    new_plan = '''    elif completion_state == "declared-types-qualified":
        execution_plan_rows = [
            row for row in stable_candidate_rows
            if row.get("attemptEvidence")
            or row.get("validationState") == "live-validated"
        ]
        execution_plan_routes = {
            str(row.get("route") or "") for row in execution_plan_rows if isinstance(row, dict)
        }
        for row in safe_runtime_derived_rows:
            route = str(row.get("route") or "")
            if route and route not in execution_plan_routes:
                execution_plan_rows.append(row)
                execution_plan_routes.add(route)
    else:
'''
    text = once(text, old_plan, new_plan, "qualified-safe-runtime-plan")

    old_meta = '''        "runtimeDerivedRouteCount": len(runtime_derived_rows),
        "runtimeDerivedRoutesPersisted": False,
        "runtimeObservedUrlCount": len(runtime_observed_urls),
'''
    new_meta = '''        "runtimeDerivedRouteCount": len(runtime_derived_rows),
        "runtimeDerivedRoutesPersisted": False,
        "safeRuntimeDerivedRouteCount": len(safe_runtime_derived_rows),
        "safeRuntimeDerivedRoutesPromoted": (
            len(safe_runtime_derived_rows) if completion_state == "declared-types-qualified" else 0
        ),
        "runtimeObservedUrlCount": len(runtime_observed_urls),
'''
    text = once(text, old_meta, new_meta, "safe-runtime-recognition-metadata")

    old_recognized = '''    recognized["runtimeDerivedRequests"] = copy.deepcopy(runtime_derived_rows[:80])
    recognized["runtimeDerivedRoutesPersisted"] = False
    recognized["runtimeObservedUrls"] = runtime_observed_urls[:80]
'''
    new_recognized = '''    recognized["runtimeDerivedRequests"] = copy.deepcopy(runtime_derived_rows[:80])
    recognized["runtimeDerivedRoutesPersisted"] = False
    recognized["safeRuntimeDerivedRequests"] = copy.deepcopy(safe_runtime_derived_rows[:80])
    recognized["safeRuntimeDerivedRoutesPromoted"] = (
        len(safe_runtime_derived_rows) if completion_state == "declared-types-qualified" else 0
    )
    recognized["runtimeObservedUrls"] = runtime_observed_urls[:80]
'''
    text = once(text, old_recognized, new_recognized, "safe-runtime-recognized-metadata")

    old_gate = '''            "runtime_derived_route_count": len(runtime_derived_rows),
            "runtime_derived_routes_persisted": False,
            "runtime_observed_url_count": len(runtime_observed_urls),
'''
    new_gate = '''            "runtime_derived_route_count": len(runtime_derived_rows),
            "runtime_derived_routes_persisted": False,
            "safe_runtime_derived_route_count": len(safe_runtime_derived_rows),
            "safe_runtime_derived_routes_promoted": (
                len(safe_runtime_derived_rows) if completion_state == "declared-types-qualified" else 0
            ),
            "runtime_observed_url_count": len(runtime_observed_urls),
'''
    text = once(text, old_gate, new_gate, "safe-runtime-patch-metadata")

    TARGET.write_text(text, encoding="utf-8")
    validate(text)
    return True


def validate(text: str) -> None:
    required = (
        MARKER,
        'safe_runtime_derived_rows = [',
        'row["derivation"].get("reusable") is True',
        'not (row["derivation"].get("fixtureSpecificValues") or [])',
        'and "{" in str(row.get("route") or "")',
        'for row in safe_runtime_derived_rows:',
        '"safeRuntimeDerivedRoutesPromoted": (',
        'recognized["safeRuntimeDerivedRequests"]',
        '"safe_runtime_derived_routes_promoted": (',
    )
    for needle in required:
        if needle not in text:
            raise AssertionError(f"safe runtime promotion missing: {needle}")


def main() -> int:
    changed = patch()
    print(
        "PROVIDER_V3_SAFE_RUNTIME_ROUTE_PROMOTION_V2_OK "
        f"changed={str(changed).lower()} live_validated=true reusable=true "
        "fixture_residue=false placeholder_template=true"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
