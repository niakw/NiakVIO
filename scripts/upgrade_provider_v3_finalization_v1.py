#!/usr/bin/env python3
"""Upgrade Provider v3 finalization to preserve the stable executable plan.

Declared semantic types are the publication gate denominator. Internal
search/detail/player/API requests are chain evidence, not extra coverage items.
Runtime-discovered landing/gateway URLs are evidence too: they must never become
persistent provider route DATA merely because a crawler traversed them.

Rules:
- normally qualified providers retain stable candidate routes actually traversed
  by the successful candidate, including non-2xx fallback/control hops;
- runtime-derived routes (``liveDerived``) stay diagnostic/type evidence only and
  are never promoted automatically into executable DATA;
- never-executed non-recipe route candidates are pruned after normal proof;
- terminal-blocked / terminal-unreachable providers retain the whole *stable*
  candidate plan because CI could not traverse far enough to safely prune it;
- an explicit apiRecipe is an atomic executable plan and is retained. Optional
  recipe branches need not all return 2xx for the recipe to survive.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts" / "validate_provider_v3_routes_sequential.py"
MARKER = "PROVIDER_V3_EXECUTION_PLAN_FINALIZATION_V1"


def once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise AssertionError(f"{label}: expected one exact anchor, got {count}")
    return text.replace(old, new, 1)


def patch() -> bool:
    text = TARGET.read_text(encoding="utf-8")
    if MARKER in text:
        validate_text(text)
        return False

    old_plan = '''    model["candidateRouteData"] = copy.deepcopy(evaluation["candidateRouteData"])
    model["routeData"] = copy.deepcopy(evaluation["liveRouteData"])
    model["routes"] = list(evaluation["liveRoutes"])
'''
    new_plan = '''    model["candidateRouteData"] = copy.deepcopy(evaluation["candidateRouteData"])

    # PROVIDER_V3_EXECUTION_PLAN_FINALIZATION_V1
    # Gate coverage, runtime traversal evidence and persistent route DATA are
    # deliberately different things. Runtime-discovered landing/gateway URLs
    # may prove a declared type without becoming fixed routes in the next build.
    stable_candidate_rows = [
        copy.deepcopy(row)
        for row in evaluation["candidateRouteData"]
        if isinstance(row, dict)
        and str(row.get("route") or "").strip()
        and not row.get("liveDerived")
    ]
    runtime_derived_rows = [
        copy.deepcopy(row)
        for row in evaluation["candidateRouteData"]
        if isinstance(row, dict)
        and str(row.get("route") or "").strip()
        and row.get("liveDerived")
    ]
    if completion_state in {"terminal-blocked", "terminal-unreachable"}:
        # CI could not traverse the stable plan far enough to prove safe pruning.
        # Preserve it verbatim so another network/client can still reach routes
        # that occur after the blocked first hop. Dynamic crawl URLs stay evidence.
        execution_plan_rows = stable_candidate_rows
    elif completion_state == "declared-types-qualified":
        # Keep every stable route that the working candidate actually attempted.
        # This includes failed/blocked fallback hops but excludes untouched guesses
        # and excludes live-derived landing/gateway URLs which the runtime already
        # discovers from the returned document/response.
        execution_plan_rows = [
            row for row in stable_candidate_rows
            if row.get("attemptEvidence")
            or row.get("validationState") == "live-validated"
        ]
    else:
        # Direct-output and other exceptional verified states have no stronger
        # evidence for destructive pruning than the stable candidate plan itself.
        execution_plan_rows = stable_candidate_rows

    # If a provider had no durable route DATA at all, do not manufacture one from
    # runtime crawl URLs. Its verified direct output / provider Lego remains the
    # executable authority and the derived calls remain diagnostics only.
    model["routeData"] = execution_plan_rows
    model["routes"] = unique(
        [row.get("route") for row in execution_plan_rows if isinstance(row, dict)],
        256,
    )
'''
    text = once(text, old_plan, new_plan, "execution-plan-retention")

    old_recipe = '''    live_set = set(evaluation["liveRoutes"])
    if isinstance(model.get("apiRecipe"), dict) and not recipe_is_live(model["apiRecipe"], live_set):
        model.pop("apiRecipe", None)
'''
    new_recipe = '''    live_set = set(evaluation["liveRoutes"])
    execution_plan_set = set(model.get("routes") or [])
    candidate_model_recipe = model.get("candidateApiRecipe")
    if isinstance(candidate_model_recipe, dict):
        # The recipe is one bounded execution plan. Type proof validates the
        # declared outputs; optional status/fallback branches are not individual
        # gate requirements. Blocked CI runs preserve the current plan as well.
        model["apiRecipe"] = copy.deepcopy(candidate_model_recipe)
'''
    text = once(text, old_recipe, new_recipe, "atomic-api-recipe")

    old_patch_routes = '''        candidate_learned = patch.get("candidate_learned_routes") if isinstance(patch.get("candidate_learned_routes"), list) else patch.get("learned_routes") or []
        patch["learned_routes"] = [str(route) for route in candidate_learned if str(route) in live_set]
        for route in evaluation["liveRoutes"]:
            if route not in patch["learned_routes"]:
                patch["learned_routes"].append(route)
        if isinstance(patch.get("api_recipe"), dict) and not isinstance(patch.get("candidate_api_recipe"), dict):
            patch["candidate_api_recipe"] = copy.deepcopy(patch["api_recipe"])
        candidate_recipe = patch.get("candidate_api_recipe") if isinstance(patch.get("candidate_api_recipe"), dict) else patch.get("api_recipe")
        if isinstance(candidate_recipe, dict) and recipe_is_live(candidate_recipe, live_set):
            patch["api_recipe"] = copy.deepcopy(candidate_recipe)
        else:
            patch.pop("api_recipe", None)
'''
    new_patch_routes = '''        candidate_learned = patch.get("candidate_learned_routes") if isinstance(patch.get("candidate_learned_routes"), list) else patch.get("learned_routes") or []
        patch["learned_routes"] = [
            str(route) for route in candidate_learned
            if str(route) in execution_plan_set
        ]
        for route in model.get("routes") or []:
            if route not in patch["learned_routes"]:
                patch["learned_routes"].append(route)
        if isinstance(patch.get("api_recipe"), dict) and not isinstance(patch.get("candidate_api_recipe"), dict):
            patch["candidate_api_recipe"] = copy.deepcopy(patch["api_recipe"])
        candidate_recipe = patch.get("candidate_api_recipe") if isinstance(patch.get("candidate_api_recipe"), dict) else patch.get("api_recipe")
        if isinstance(candidate_recipe, dict):
            patch["api_recipe"] = copy.deepcopy(candidate_recipe)
'''
    text = once(text, old_patch_routes, new_patch_routes, "override-plan-retention")

    old_recognition = '''        "internalRequestsAreNotGateDenominator": True,
        "sequentialProviderGate": True,
'''
    new_recognition = '''        "internalRequestsAreNotGateDenominator": True,
        "executionPlanRouteCount": len(model.get("routes") or []),
        "executionPlanRetainsAttemptedNon2xx": True,
        "runtimeDerivedRouteCount": len(runtime_derived_rows),
        "runtimeDerivedRoutesPersisted": False,
        "blockedPlanPreserved": completion_state in {"terminal-blocked", "terminal-unreachable"},
        "sequentialProviderGate": True,
'''
    text = once(text, old_recognition, new_recognition, "route-recognition-plan-fields")

    old_recognized = '''    recognized["declaredTypesAreGateDenominator"] = True
    recognized["sequentialProviderGate"] = True
'''
    new_recognized = '''    recognized["declaredTypesAreGateDenominator"] = True
    recognized["executionPlanRequests"] = copy.deepcopy(model.get("routeData") or [])
    recognized["executionPlanRouteCount"] = len(model.get("routes") or [])
    recognized["runtimeDerivedRequests"] = copy.deepcopy(runtime_derived_rows[:80])
    recognized["runtimeDerivedRoutesPersisted"] = False
    recognized["sequentialProviderGate"] = True
'''
    text = once(text, old_recognized, new_recognized, "recognized-plan-fields")

    old_gate = '''            "live_validated_route_count": evaluation["liveValidatedRouteCount"],
            "declared_types_are_gate_denominator": True,
            "sequential": True,
'''
    new_gate = '''            "live_validated_route_count": evaluation["liveValidatedRouteCount"],
            "execution_plan_route_count": len(model.get("routes") or []),
            "runtime_derived_route_count": len(runtime_derived_rows),
            "runtime_derived_routes_persisted": False,
            "blocked_plan_preserved": completion_state in {"terminal-blocked", "terminal-unreachable"},
            "declared_types_are_gate_denominator": True,
            "sequential": True,
'''
    text = once(text, old_gate, new_gate, "patch-gate-plan-fields")

    TARGET.write_text(text, encoding="utf-8")
    validate_text(text)
    return True


def validate_text(text: str) -> None:
    if text.count(MARKER) != 1:
        raise AssertionError(f"finalization marker count={text.count(MARKER)}")
    required = (
        'stable_candidate_rows = [',
        'and not row.get("liveDerived")',
        'runtime_derived_rows = [',
        'and row.get("liveDerived")',
        'if completion_state in {"terminal-blocked", "terminal-unreachable"}:',
        'elif completion_state == "declared-types-qualified":',
        'if row.get("attemptEvidence")',
        'model["routeData"] = execution_plan_rows',
        'execution_plan_set = set(model.get("routes") or [])',
        'model["apiRecipe"] = copy.deepcopy(candidate_model_recipe)',
        'patch["api_recipe"] = copy.deepcopy(candidate_recipe)',
        '"executionPlanRetainsAttemptedNon2xx": True',
        '"runtimeDerivedRoutesPersisted": False',
        '"blockedPlanPreserved": completion_state in {"terminal-blocked", "terminal-unreachable"}',
    )
    for needle in required:
        if needle not in text:
            raise AssertionError(f"Provider v3 finalization v1 missing: {needle}")
    forbidden = (
        'model["routeData"] = copy.deepcopy(evaluation["liveRouteData"])',
        'model["routes"] = list(evaluation["liveRoutes"])',
        'execution_plan_rows = copy.deepcopy(evaluation["liveRouteData"])',
        'not recipe_is_live(model["apiRecipe"], live_set)',
        'candidate_recipe, live_set',
    )
    for needle in forbidden:
        if needle in text:
            raise AssertionError(f"Provider v3 finalization v1 retained destructive/polluting rule: {needle}")


def main() -> int:
    changed = patch()
    print(
        "PROVIDER_V3_FINALIZATION_V1_OK "
        f"changed={str(changed).lower()} attempted_non2xx=preserved "
        "runtime_derived=pure-evidence blocked_plan=preserved api_recipe=atomic"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
