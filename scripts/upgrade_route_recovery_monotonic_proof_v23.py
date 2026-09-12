#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts" / "recover_provider_routes_from_upstreams.py"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one anchor, found {count}")
    return text.replace(old, new, 1)


def main() -> int:
    text = TARGET.read_text(encoding="utf-8")
    if "ROUTE_RECOVERY_MONOTONIC_PROOF_V23" in text:
        print("ROUTE_RECOVERY_MONOTONIC_PROOF_V23_OK changed=false")
        return 0

    anchor = "\ndef apply_recovery(report: dict[str, Any]) -> dict[str, Any]:\n"
    helper = r'''
# ROUTE_RECOVERY_MONOTONIC_PROOF_V23
def _proof_v5_execution_authority(patch: dict[str, Any], model: dict[str, Any]) -> tuple[bool, dict[str, Any] | None]:
    """Return an independently executable proof-v5 recipe, never a candidate.

    A later repair probe that yields zero routes is negative evidence about that
    probe only. It cannot erase a previously live-proven execution authority.
    Candidate/static recipes remain fail-closed because they never enter here.
    """
    versions = []
    for raw in (patch.get("route_proof_version"), model.get("routeProofVersion")):
        try:
            versions.append(int(raw or 0))
        except (TypeError, ValueError):
            versions.append(0)
    recipe = patch.get("api_recipe") if isinstance(patch.get("api_recipe"), dict) else None
    if recipe is None and isinstance(model.get("apiRecipe"), dict):
        recipe = model.get("apiRecipe")
    recipe_version = 0
    if isinstance(recipe, dict):
        try:
            recipe_version = int(recipe.get("proofModelVersion") or 0)
        except (TypeError, ValueError):
            recipe_version = 0
    if max(versions or [0]) < PROOF_VERSION or recipe_version < PROOF_VERSION:
        return False, None
    return True, copy.deepcopy(recipe)


def _preserved_string_list(patch_value: object, model_value: object, limit: int) -> list[str]:
    rows = patch_value if isinstance(patch_value, list) else model_value if isinstance(model_value, list) else []
    return unique([str(value).strip() for value in rows if str(value).strip()], limit)

'''
    text = replace_once(text, anchor, "\n" + helper + "def apply_recovery(report: dict[str, Any]) -> dict[str, Any]:\n", "helper")

    old = '''        model = static_row.get("model") if isinstance(static_row.get("model"), dict) else {}\n        existing_routes = unique([\n'''
    new = '''        model = static_row.get("model") if isinstance(static_row.get("model"), dict) else {}\n        preserve_existing_execution_authority, existing_proven_recipe = _proof_v5_execution_authority(patch, model)\n        existing_proof_search_bases = _preserved_string_list(patch.get("proof_search_bases"), model.get("proofSearchBases"), 6)\n        existing_proof_detail_bases = _preserved_string_list(patch.get("proof_detail_bases"), model.get("proofDetailBases"), 6)\n        existing_proof_protected_hosts = _preserved_string_list(patch.get("proof_protected_hosts"), model.get("proofProtectedHosts"), 24)\n        existing_routes = unique([\n'''
    text = replace_once(text, old, new, "authority snapshot")

    replacements = [
        (
'''        else:\n            patch.pop("proof_search_bases", None)\n            model.pop("proofSearchBases", None)\n''',
'''        elif preserve_existing_execution_authority and existing_proof_search_bases:\n            patch["proof_search_bases"] = copy.deepcopy(existing_proof_search_bases)\n            model["proofSearchBases"] = copy.deepcopy(existing_proof_search_bases)\n        else:\n            patch.pop("proof_search_bases", None)\n            model.pop("proofSearchBases", None)\n''', "search bases"),
        (
'''        else:\n            patch.pop("proof_detail_bases", None)\n            model.pop("proofDetailBases", None)\n''',
'''        elif preserve_existing_execution_authority and existing_proof_detail_bases:\n            patch["proof_detail_bases"] = copy.deepcopy(existing_proof_detail_bases)\n            model["proofDetailBases"] = copy.deepcopy(existing_proof_detail_bases)\n        else:\n            patch.pop("proof_detail_bases", None)\n            model.pop("proofDetailBases", None)\n''', "detail bases"),
        (
'''        else:\n            patch.pop("proof_protected_hosts", None)\n            model.pop("proofProtectedHosts", None)\n''',
'''        elif preserve_existing_execution_authority and existing_proof_protected_hosts:\n            patch["proof_protected_hosts"] = copy.deepcopy(existing_proof_protected_hosts)\n            model["proofProtectedHosts"] = copy.deepcopy(existing_proof_protected_hosts)\n        else:\n            patch.pop("proof_protected_hosts", None)\n            model.pop("proofProtectedHosts", None)\n''', "protected hosts"),
    ]
    for old, new, label in replacements:
        text = replace_once(text, old, new, label)

    old = '''        model["routeProof"] = {\n            "version": PROOF_VERSION,\n            "authority": "observed-provider-http-request",\n            "staticCandidatesExecutable": False,\n            "providerSource": copy.deepcopy(recovered.get("source") or {}),\n            "provenRouteCount": len(proven_routes),\n            "genericExecutionRouteCount": len(execution_routes),\n            "runtimePlanPreserved": preserved_baseline_plan,\n            "runtimePlanRouteCount": len(runtime_routes),\n        }\n'''
    new = '''        fresh_positive_execution = bool(recipe or execution_routes or proven_routes)\n        model["routeProof"] = {\n            "version": PROOF_VERSION,\n            "authority": "observed-provider-http-request",\n            "staticCandidatesExecutable": False,\n            "providerSource": copy.deepcopy(recovered.get("source") or {}),\n            "provenRouteCount": len(proven_routes),\n            "genericExecutionRouteCount": len(execution_routes),\n            "runtimePlanPreserved": preserved_baseline_plan,\n            "runtimePlanRouteCount": len(runtime_routes),\n            "lastRepairProbe": {\n                "status": str(recovered.get("status") or "unknown"),\n                "positiveExecutionEvidence": fresh_positive_execution,\n            },\n        }\n        if preserve_existing_execution_authority and recipe is None:\n            model["routeProof"]["executionAuthorityPreserved"] = True\n'''
    text = replace_once(text, old, new, "route proof annotation")

    old = '''        if recipe:\n            patch["api_recipe"] = copy.deepcopy(recipe)\n            model["apiRecipe"] = copy.deepcopy(recipe)\n            recipes += 1\n        else:\n            patch.pop("api_recipe", None)\n            model.pop("apiRecipe", None)\n'''
    new = '''        if recipe:\n            patch["api_recipe"] = copy.deepcopy(recipe)\n            model["apiRecipe"] = copy.deepcopy(recipe)\n            recipes += 1\n        elif preserve_existing_execution_authority and isinstance(existing_proven_recipe, dict):\n            patch["api_recipe"] = copy.deepcopy(existing_proven_recipe)\n            model["apiRecipe"] = copy.deepcopy(existing_proven_recipe)\n            recipes += 1\n        else:\n            patch.pop("api_recipe", None)\n            model.pop("apiRecipe", None)\n'''
    text = replace_once(text, old, new, "recipe preservation")

    # route_proof is copied to the patch after the model object is complete.
    # Preserve the V23 annotations in both owners.
    TARGET.write_text(text, encoding="utf-8")
    print("ROUTE_RECOVERY_MONOTONIC_PROOF_V23_OK changed=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
