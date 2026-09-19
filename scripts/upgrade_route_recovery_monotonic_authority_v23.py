#!/usr/bin/env python3
"""Make route recovery monotone for already proof-v5 execution authorities.

A targeted upstream probe is evidence about the probed upstream at that instant.
A zero-result probe must not erase an independently live-proven execution authority
already stored with route-proof v5 + recipe-proof v5. Fresh positive evidence may
still replace/enrich it. Candidate/static recipes remain ineligible.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts" / "recover_provider_routes_from_upstreams.py"
MARKER = "ROUTE_RECOVERY_MONOTONIC_PROOF_V23"

ANCHOR = '''def apply_recovery(report: dict[str, Any]) -> dict[str, Any]:\n'''
HELPER = r'''# ROUTE_RECOVERY_MONOTONIC_PROOF_V23
def _existing_proof_v5_authority(patch: dict[str, Any], model: dict[str, Any]) -> dict[str, Any] | None:
    """Return an existing executable authority only when BOTH proof gates are v5.

    Candidate/static recipes are deliberately excluded. This is execution LKG,
    not recognition knowledge.
    """
    patch_route_v = int(patch.get("route_proof_version") or 0)
    model_route_v = int(model.get("routeProofVersion") or 0)
    recipe = patch.get("api_recipe") if isinstance(patch.get("api_recipe"), dict) else None
    if recipe is None and isinstance(model.get("apiRecipe"), dict):
        recipe = model.get("apiRecipe")
    recipe_v = int((recipe or {}).get("proofModelVersion") or 0)
    if max(patch_route_v, model_route_v) < PROOF_VERSION or recipe_v < PROOF_VERSION:
        return None
    return {
        "apiRecipe": copy.deepcopy(recipe),
        "proofSearchBases": copy.deepcopy(patch.get("proof_search_bases") or model.get("proofSearchBases") or []),
        "proofDetailBases": copy.deepcopy(patch.get("proof_detail_bases") or model.get("proofDetailBases") or []),
        "proofProtectedHosts": copy.deepcopy(patch.get("proof_protected_hosts") or model.get("proofProtectedHosts") or []),
        "searchRequestPlan": copy.deepcopy(patch.get("search_request_plan") or model.get("searchRequestPlan") or []),
        "providerValuePlan": copy.deepcopy(patch.get("provider_value_plan") or model.get("providerValuePlan") or []),
        "externalIdentityPlan": copy.deepcopy(patch.get("external_identity_plan") or model.get("externalIdentityPlan") or []),
        "routeProof": copy.deepcopy(patch.get("route_proof") or model.get("routeProof") or {}),
    }


def _recovered_has_positive_execution_evidence(recovered: dict[str, Any]) -> bool:
    if isinstance(recovered.get("apiRecipe"), dict):
        return True
    if recovered.get("routes") or recovered.get("executionRoutes"):
        return True
    for row in recovered.get("routeData") or []:
        if not isinstance(row, dict):
            continue
        if int(row.get("taskStreamCount") or 0) > 0 or int(row.get("taskRawStreamCount") or 0) > 0:
            return True
        status = int(row.get("status") or row.get("httpStatus") or 0)
        if 200 <= status < 400 and row.get("requestSpecReusable") is True:
            return True
    return False

'''

MODEL_ANCHOR = '''        model = static_row.get("model") if isinstance(static_row.get("model"), dict) else {}\n        existing_routes = unique([\n'''
MODEL_REPL = '''        model = static_row.get("model") if isinstance(static_row.get("model"), dict) else {}\n        existing_authority = _existing_proof_v5_authority(patch, model)\n        recovered_positive = _recovered_has_positive_execution_evidence(recovered)\n        preserve_existing_authority = existing_authority is not None and not recovered_positive\n        existing_routes = unique([\n'''

SEARCH_ELSE = '''        else:\n            patch.pop("proof_search_bases", None)\n            model.pop("proofSearchBases", None)\n'''
SEARCH_REPL = '''        elif preserve_existing_authority and existing_authority.get("proofSearchBases"):\n            patch["proof_search_bases"] = copy.deepcopy(existing_authority["proofSearchBases"])\n            model["proofSearchBases"] = copy.deepcopy(existing_authority["proofSearchBases"])\n        else:\n            patch.pop("proof_search_bases", None)\n            model.pop("proofSearchBases", None)\n'''

DETAIL_ELSE = '''        else:\n            patch.pop("proof_detail_bases", None)\n            model.pop("proofDetailBases", None)\n'''
DETAIL_REPL = '''        elif preserve_existing_authority and existing_authority.get("proofDetailBases"):\n            patch["proof_detail_bases"] = copy.deepcopy(existing_authority["proofDetailBases"])\n            model["proofDetailBases"] = copy.deepcopy(existing_authority["proofDetailBases"])\n        else:\n            patch.pop("proof_detail_bases", None)\n            model.pop("proofDetailBases", None)\n'''

HOST_ELSE = '''        else:\n            patch.pop("proof_protected_hosts", None)\n            model.pop("proofProtectedHosts", None)\n'''
HOST_REPL = '''        elif preserve_existing_authority and existing_authority.get("proofProtectedHosts"):\n            patch["proof_protected_hosts"] = copy.deepcopy(existing_authority["proofProtectedHosts"])\n            model["proofProtectedHosts"] = copy.deepcopy(existing_authority["proofProtectedHosts"])\n        else:\n            patch.pop("proof_protected_hosts", None)\n            model.pop("proofProtectedHosts", None)\n'''

SEARCH_PLAN_ELSE = '''        else:\n            patch.pop("search_request_plan", None)\n            model.pop("searchRequestPlan", None)\n'''
SEARCH_PLAN_REPL = '''        elif preserve_existing_authority and existing_authority.get("searchRequestPlan"):\n            patch["search_request_plan"] = copy.deepcopy(existing_authority["searchRequestPlan"])\n            model["searchRequestPlan"] = copy.deepcopy(existing_authority["searchRequestPlan"])\n        else:\n            patch.pop("search_request_plan", None)\n            model.pop("searchRequestPlan", None)\n'''

VALUE_ELSE = '''        else:\n            patch.pop("provider_value_plan", None)\n            model.pop("providerValuePlan", None)\n'''
VALUE_REPL = '''        elif preserve_existing_authority and existing_authority.get("providerValuePlan"):\n            patch["provider_value_plan"] = copy.deepcopy(existing_authority["providerValuePlan"])\n            model["providerValuePlan"] = copy.deepcopy(existing_authority["providerValuePlan"])\n        else:\n            patch.pop("provider_value_plan", None)\n            model.pop("providerValuePlan", None)\n'''

EXTERNAL_ELSE = '''        else:\n            patch.pop("external_identity_plan", None)\n            model.pop("externalIdentityPlan", None)\n        recipe = recovered.get("apiRecipe") if isinstance(recovered.get("apiRecipe"), dict) else None\n'''
EXTERNAL_REPL = '''        elif preserve_existing_authority and existing_authority.get("externalIdentityPlan"):\n            patch["external_identity_plan"] = copy.deepcopy(existing_authority["externalIdentityPlan"])\n            model["externalIdentityPlan"] = copy.deepcopy(existing_authority["externalIdentityPlan"])\n        else:\n            patch.pop("external_identity_plan", None)\n            model.pop("externalIdentityPlan", None)\n        recipe = recovered.get("apiRecipe") if isinstance(recovered.get("apiRecipe"), dict) else None\n'''

PROOF_ANCHOR = '''        model["routeProofVersion"] = PROOF_VERSION\n        model["routeProof"] = {\n            "version": PROOF_VERSION,\n            "authority": "observed-provider-http-request",\n            "staticCandidatesExecutable": False,\n            "providerSource": copy.deepcopy(recovered.get("source") or {}),\n            "provenRouteCount": len(proven_routes),\n            "genericExecutionRouteCount": len(execution_routes),\n            "runtimePlanPreserved": preserved_baseline_plan,\n            "runtimePlanRouteCount": len(runtime_routes),\n        }\n        patch["route_proof_version"] = PROOF_VERSION\n        patch["route_proof"] = copy.deepcopy(model["routeProof"])\n        if recipe:\n            patch["api_recipe"] = copy.deepcopy(recipe)\n            model["apiRecipe"] = copy.deepcopy(recipe)\n            recipes += 1\n        else:\n            patch.pop("api_recipe", None)\n            model.pop("apiRecipe", None)\n'''
PROOF_REPL = '''        model["routeProofVersion"] = PROOF_VERSION\n        if preserve_existing_authority and isinstance(existing_authority.get("routeProof"), dict) and existing_authority.get("routeProof"):\n            model["routeProof"] = copy.deepcopy(existing_authority["routeProof"])\n            model["routeProof"]["lastRepairProbe"] = {\n                "status": str(recovered.get("status") or "unknown"),\n                "positiveExecutionEvidence": False,\n                "source": copy.deepcopy(recovered.get("source") or {}),\n            }\n            model["routeProof"]["executionAuthorityPreserved"] = True\n        else:\n            model["routeProof"] = {\n                "version": PROOF_VERSION,\n                "authority": "observed-provider-http-request",\n                "staticCandidatesExecutable": False,\n                "providerSource": copy.deepcopy(recovered.get("source") or {}),\n                "provenRouteCount": len(proven_routes),\n                "genericExecutionRouteCount": len(execution_routes),\n                "runtimePlanPreserved": preserved_baseline_plan,\n                "runtimePlanRouteCount": len(runtime_routes),\n            }\n        patch["route_proof_version"] = PROOF_VERSION\n        patch["route_proof"] = copy.deepcopy(model["routeProof"])\n        if recipe:\n            patch["api_recipe"] = copy.deepcopy(recipe)\n            model["apiRecipe"] = copy.deepcopy(recipe)\n            recipes += 1\n        elif preserve_existing_authority:\n            patch["api_recipe"] = copy.deepcopy(existing_authority["apiRecipe"])\n            model["apiRecipe"] = copy.deepcopy(existing_authority["apiRecipe"])\n            recipes += 1\n        else:\n            patch.pop("api_recipe", None)\n            model.pop("apiRecipe", None)\n'''


def once(text: str, old: str, new: str, label: str) -> str:
    n = text.count(old)
    if n != 1:
        raise AssertionError(f"{label}: expected one anchor, got {n}")
    return text.replace(old, new, 1)


def validate(text: str) -> None:
    for needle in (
        MARKER,
        "def _existing_proof_v5_authority",
        "def _recovered_has_positive_execution_evidence",
        "preserve_existing_authority = existing_authority is not None and not recovered_positive",
        'model["routeProof"]["executionAuthorityPreserved"] = True',
        'patch["api_recipe"] = copy.deepcopy(existing_authority["apiRecipe"])',
    ):
        if needle not in text:
            raise AssertionError(f"missing {needle}")


def main() -> int:
    text = TARGET.read_text(encoding="utf-8")
    if MARKER in text:
        validate(text)
        print("ROUTE_RECOVERY_MONOTONIC_PROOF_V23_OK changed=false")
        return 0
    text = once(text, ANCHOR, HELPER + ANCHOR, "helper")
    text = once(text, MODEL_ANCHOR, MODEL_REPL, "model")
    text = once(text, SEARCH_ELSE, SEARCH_REPL, "search bases")
    text = once(text, DETAIL_ELSE, DETAIL_REPL, "detail bases")
    text = once(text, HOST_ELSE, HOST_REPL, "protected hosts")
    text = once(text, SEARCH_PLAN_ELSE, SEARCH_PLAN_REPL, "search plan")
    text = once(text, VALUE_ELSE, VALUE_REPL, "value plan")
    text = once(text, EXTERNAL_ELSE, EXTERNAL_REPL, "external plan")
    text = once(text, PROOF_ANCHOR, PROOF_REPL, "proof recipe")
    validate(text)
    TARGET.write_text(text, encoding="utf-8")
    print("ROUTE_RECOVERY_MONOTONIC_PROOF_V23_OK changed=true negative_probe_destructive=0 candidate_authority=0 proof_v5_preserved=1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
