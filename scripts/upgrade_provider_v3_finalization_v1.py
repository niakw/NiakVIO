#!/usr/bin/env python3
"""Upgrade Provider v3 finalization without turning runtime observations into DATA.

Stable Provider DATA and runtime evidence are different layers:
- stable candidate routes actually traversed may remain executable;
- runtime-derived landing/gateway routes stay evidence-only;
- runtime-observed full URLs/origins stay evidence-only too;
- blocked runners preserve the complete stable candidate plan;
- explicit apiRecipe remains an atomic execution plan.

The upgrader also adds final-bundle probe diagnostics so candidate -> final drift is
visible fixture-by-fixture in Actions logs.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts" / "validate_provider_v3_routes_sequential.py"
FINAL_PROBE_TARGET = ROOT / "scripts" / "reconstruct_provider_v3_sequential_live.py"
MARKER = "PROVIDER_V3_EXECUTION_PLAN_FINALIZATION_V1"
FINAL_PROBE_MARKER = "PROVIDER_V3_FINAL_PROBE_DIAGNOSTICS_V1"


def once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise AssertionError(f"{label}: expected one exact anchor, got {count}")
    return text.replace(old, new, 1)


def patch_finalizer() -> bool:
    text = TARGET.read_text(encoding="utf-8")
    if MARKER in text:
        validate_finalizer(text)
        return False

    old_plan = '''    model["candidateRouteData"] = copy.deepcopy(evaluation["candidateRouteData"])
    model["routeData"] = copy.deepcopy(evaluation["liveRouteData"])
    model["routes"] = list(evaluation["liveRoutes"])
'''
    new_plan = '''    model["candidateRouteData"] = copy.deepcopy(evaluation["candidateRouteData"])

    # PROVIDER_V3_EXECUTION_PLAN_FINALIZATION_V1
    # Coverage proof, runtime traversal evidence and persistent Provider DATA are
    # distinct layers. Dynamic landing/gateway URLs may prove a type without
    # becoming fixed routes in the next bundle.
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
        execution_plan_rows = stable_candidate_rows
    elif completion_state == "declared-types-qualified":
        execution_plan_rows = [
            row for row in stable_candidate_rows
            if row.get("attemptEvidence")
            or row.get("validationState") == "live-validated"
        ]
    else:
        execution_plan_rows = stable_candidate_rows

    model["routeData"] = execution_plan_rows
    model["routes"] = unique(
        [row.get("route") for row in execution_plan_rows if isinstance(row, dict)],
        256,
    )
'''
    text = once(text, old_plan, new_plan, "execution-plan-retention")

    old_observations = '''    live_origins = list(model.get("origins") or [])
    observed_urls = list(model.get("observedUrls") or [])
    for row in evaluation["candidateRouteData"]:
        for item in row.get("attemptEvidence") or []:
            raw = str(item.get("finalUrl") or item.get("url") or "")
            if raw and raw not in observed_urls:
                observed_urls.append(raw)
            try:
                parsed = urllib.parse.urlsplit(raw)
                if parsed.scheme in {"http", "https"} and parsed.hostname:
                    origin = f"{parsed.scheme}://{parsed.netloc}"
                    if origin not in live_origins:
                        live_origins.append(origin)
            except ValueError:
                pass
    model["origins"] = live_origins[:64]
    model["observedUrls"] = observed_urls[:128]
'''
    new_observations = '''    # Runtime observations are diagnostics, not Provider DATA authority. Preserve
    # the stable candidate origins/URLs exactly; collect traversal observations
    # separately for the report so signed/session URLs cannot alter the final build.
    stable_origins = list(model.get("origins") or [])
    stable_observed_urls = list(model.get("observedUrls") or [])
    runtime_observed_urls = []
    runtime_observed_origins = []
    for row in evaluation["candidateRouteData"]:
        for item in row.get("attemptEvidence") or []:
            raw = str(item.get("finalUrl") or item.get("url") or "")
            if raw and raw not in runtime_observed_urls:
                runtime_observed_urls.append(raw)
            try:
                parsed = urllib.parse.urlsplit(raw)
                if parsed.scheme in {"http", "https"} and parsed.hostname:
                    origin = f"{parsed.scheme}://{parsed.netloc}"
                    if origin not in runtime_observed_origins:
                        runtime_observed_origins.append(origin)
            except ValueError:
                pass
    model["origins"] = stable_origins[:64]
    model["observedUrls"] = stable_observed_urls[:128]
'''
    text = once(text, old_observations, new_observations, "runtime-observation-separation")

    old_recipe = '''    live_set = set(evaluation["liveRoutes"])
    if isinstance(model.get("apiRecipe"), dict) and not recipe_is_live(model["apiRecipe"], live_set):
        model.pop("apiRecipe", None)
'''
    new_recipe = '''    live_set = set(evaluation["liveRoutes"])
    execution_plan_set = set(model.get("routes") or [])
    candidate_model_recipe = model.get("candidateApiRecipe")
    if isinstance(candidate_model_recipe, dict):
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
        "runtimeObservedUrlCount": len(runtime_observed_urls),
        "runtimeObservedOriginCount": len(runtime_observed_origins),
        "runtimeObservationsPersistedAsProviderData": False,
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
    recognized["runtimeObservedUrls"] = runtime_observed_urls[:80]
    recognized["runtimeObservedOrigins"] = runtime_observed_origins[:40]
    recognized["runtimeObservationsPersistedAsProviderData"] = False
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
            "runtime_observed_url_count": len(runtime_observed_urls),
            "runtime_observed_origin_count": len(runtime_observed_origins),
            "runtime_observations_persisted_as_provider_data": False,
            "blocked_plan_preserved": completion_state in {"terminal-blocked", "terminal-unreachable"},
            "declared_types_are_gate_denominator": True,
            "sequential": True,
'''
    text = once(text, old_gate, new_gate, "patch-gate-plan-fields")

    TARGET.write_text(text, encoding="utf-8")
    validate_finalizer(text)
    return True


def patch_final_probe_diagnostics() -> bool:
    text = FINAL_PROBE_TARGET.read_text(encoding="utf-8")
    if FINAL_PROBE_MARKER in text:
        return False
    old = '''    for task in used_tasks:
        final_task = copy.deepcopy(task)
        final_task["filename"] = final_filename
        result = run_task(final_task, timeout)
        result["fixture_slug"] = final_task.get("fixture_slug")
        result["fixture"] = copy.deepcopy(final_task.get("fixture") or {})
        rows.append(result)
        evaluation = evaluate_provider(provider["provider_id"], live_model, rows, minimum)
'''
    new = '''    # PROVIDER_V3_FINAL_PROBE_DIAGNOSTICS_V1
    print(
        "FIELD_PROVIDER_FINAL_MODEL "
        f"provider={provider['provider_id']} routes={len(live_model.get('routes') or [])} "
        f"route_data={len(live_model.get('routeData') or [])} "
        f"origins={len(live_model.get('origins') or [])} "
        f"observed_urls={len(live_model.get('observedUrls') or [])} "
        f"api_recipe={str(isinstance(live_model.get('apiRecipe'), dict)).lower()}",
        flush=True,
    )
    for task_index, task in enumerate(used_tasks, start=1):
        final_task = copy.deepcopy(task)
        final_task["filename"] = final_filename
        result = run_task(final_task, timeout)
        result["fixture_slug"] = final_task.get("fixture_slug")
        result["fixture"] = copy.deepcopy(final_task.get("fixture") or {})
        rows.append(result)
        evaluation = evaluate_provider(provider["provider_id"], live_model, rows, minimum)
        http_counts = Counter(int(fetch.get("status") or 0) for fetch in result.get("fetches") or [])
        http_summary = ",".join(f"{status}:{count}" for status, count in sorted(http_counts.items())) or "none"
        print(
            "FIELD_PROVIDER_FINAL_PROBE "
            f"provider={provider['provider_id']} fixture={final_task.get('fixture_slug')} "
            f"step={task_index}/{len(used_tasks)} task_status={result.get('status')} "
            f"http_statuses={http_summary} "
            f"validated_types={','.join(evaluation.get('validatedTypes') or []) or 'none'} "
            f"missing_types={','.join(evaluation.get('missingTypes') or []) or 'none'} "
            f"requests={evaluation.get('providerRequestCount', 0)} "
            f"live={evaluation.get('liveValidatedRouteCount', 0)}",
            flush=True,
        )
'''
    text = once(text, old, new, "final-probe-diagnostics")
    FINAL_PROBE_TARGET.write_text(text, encoding="utf-8")
    return True


def validate_finalizer(text: str) -> None:
    required = (
        MARKER,
        'stable_candidate_rows = [',
        'and not row.get("liveDerived")',
        'runtime_derived_rows = [',
        'and row.get("liveDerived")',
        'model["routeData"] = execution_plan_rows',
        'model["origins"] = stable_origins[:64]',
        'model["observedUrls"] = stable_observed_urls[:128]',
        'runtimeObservationsPersistedAsProviderData": False',
        'execution_plan_set = set(model.get("routes") or [])',
        'model["apiRecipe"] = copy.deepcopy(candidate_model_recipe)',
        'patch["api_recipe"] = copy.deepcopy(candidate_recipe)',
    )
    for needle in required:
        if needle not in text:
            raise AssertionError(f"Provider v3 finalization v1 missing: {needle}")
    forbidden = (
        'model["routeData"] = copy.deepcopy(evaluation["liveRouteData"])',
        'model["routes"] = list(evaluation["liveRoutes"])',
        'model["origins"] = live_origins[:64]',
        'model["observedUrls"] = observed_urls[:128]',
        'not recipe_is_live(model["apiRecipe"], live_set)',
    )
    for needle in forbidden:
        if needle in text:
            raise AssertionError(f"Provider v3 finalization retained destructive/polluting rule: {needle}")


def main() -> int:
    changed = patch_finalizer()
    diagnostics_changed = patch_final_probe_diagnostics()
    print(
        "PROVIDER_V3_FINALIZATION_V1_OK "
        f"changed={str(changed).lower()} diagnostics_changed={str(diagnostics_changed).lower()} "
        "attempted_non2xx=preserved runtime_derived=pure-evidence "
        "runtime_observations=pure-evidence blocked_plan=preserved api_recipe=atomic"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
