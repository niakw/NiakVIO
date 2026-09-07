#!/usr/bin/env python3
"""Migrate Provider v3 reconstruction to proof-v5 route authority.

This migration is deterministic and fail-closed. Static discovery may retain route
knowledge as candidates, but only route-proof v5 data may become executable
Provider DATA. It also removes `year` from generic catalogue preflight fields;
movie-year identity remains a Core identity concern, while episodic identity never
requires year merely to launch the provider.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DISCOVER = ROOT / "scripts" / "discover_candidates.py"
MATERIALIZE = ROOT / "scripts" / "materialize_provider_v3_all.py"
BASE = ROOT / "scripts" / "provider_base_store.py"
SEQUENTIAL = ROOT / "scripts" / "validate_provider_v3_routes_sequential.py"
MARKER = "PROVIDER_V3_ROUTE_PROOF_AUTHORITY_V5"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise AssertionError(f"{label}: expected one anchor, got {count}")
    return text.replace(old, new, 1)


def patch_discover() -> bool:
    text = DISCOVER.read_text(encoding="utf-8")
    if f"# {MARKER}" in text:
        return False
    old = '''    return {
        "knownSite": str(known_site or "").strip() or None,
        "strategy": strategy,
        "officialSite": str(patch.get("official_site") or "").strip() or None,
        "officialHub": str(patch.get("official_hub") or "").strip() or None,
        "officialApi": str(patch.get("official_api") or "").strip() or None,
        "fixedApi": str(fixed.get("api") or "").strip() or None,
        "origins": origins[:32],
        "observedUrls": learned_urls[:48],
        "routes": learned_routes[:64],
        "apiRecipe": recipe,
        "sourceRuntimeFamily": str(knowledge.get("runtimeFamily") or "unknown"),
        "knowledgeRole": "structured-static-observation-only",
        "legacyCodeEmbedded": False,
        "legacyCodeExecuted": False,
    }'''
    new = f'''    # {MARKER}
    # Static strings are candidate knowledge only. Executable route DATA is born
    # exclusively from the proof-v5 runtime tracer/bootstrap.
    return {{
        "knownSite": str(known_site or "").strip() or None,
        "strategy": strategy,
        "officialSite": str(patch.get("official_site") or "").strip() or None,
        "officialHub": str(patch.get("official_hub") or "").strip() or None,
        "officialApi": str(patch.get("official_api") or "").strip() or None,
        "fixedApi": str(fixed.get("api") or "").strip() or None,
        "origins": origins[:32],
        "observedUrls": learned_urls[:48],
        "candidateRoutes": learned_routes[:64],
        "routes": [],
        "candidateApiRecipe": recipe,
        "apiRecipe": None,
        "routeProofVersion": 0,
        "sourceRuntimeFamily": str(knowledge.get("runtimeFamily") or "unknown"),
        "knowledgeRole": "structured-static-observation-only",
        "legacyCodeEmbedded": False,
        "legacyCodeExecuted": False,
    }}'''
    text = replace_once(text, old, new, "discover-static-candidate-only")
    DISCOVER.write_text(text, encoding="utf-8")
    return True


def patch_materialize() -> bool:
    text = MATERIALIZE.read_text(encoding="utf-8")
    if f"# {MARKER}" not in text:
        old = '''    routes: list[str] = []
    for value in [*(patch.get("learned_routes") or []), *(static_model.get("routes") or [])]:
        item = str(value).strip()
        if item and item != "/" and item not in routes:
            routes.append(item)

    api_recipe = (
        patch.get("api_recipe")
        if isinstance(patch.get("api_recipe"), dict)
        else static_model.get("apiRecipe") if isinstance(static_model.get("apiRecipe"), dict) else None
    )'''
        new = f'''    # {MARKER}
    patch_proof = int(patch.get("route_proof_version") or 0)
    static_proof = int(static_model.get("routeProofVersion") or 0)
    proof_version = max(patch_proof, static_proof)
    routes: list[str] = []
    if proof_version >= 5:
        for value in [*(patch.get("learned_routes") or []), *(static_model.get("routes") or [])]:
            item = str(value).strip()
            if item and item != "/" and item not in routes:
                routes.append(item)

    patch_recipe = patch.get("api_recipe") if isinstance(patch.get("api_recipe"), dict) else None
    static_recipe = static_model.get("apiRecipe") if isinstance(static_model.get("apiRecipe"), dict) else None
    candidate_recipe = patch_recipe or static_recipe
    recipe_proof = int(candidate_recipe.get("proofModelVersion") or 0) if isinstance(candidate_recipe, dict) else 0
    api_recipe = candidate_recipe if proof_version >= 5 and recipe_proof >= 5 else None'''
        text = replace_once(text, old, new, "materialize-proof-v5-only")

        old_return = '''        "routes": routes,
        "apiRecipe": api_recipe,
        "sourceRuntimeFamily": str(static_model.get("sourceRuntimeFamily") or "unknown"),'''
        new_return = '''        "routes": routes,
        "apiRecipe": api_recipe,
        "routeProofVersion": proof_version,
        "sourceRuntimeFamily": str(static_model.get("sourceRuntimeFamily") or "unknown"),'''
        text = replace_once(text, old_return, new_return, "materialize-proof-version-model")

    text = text.replace('["title", "year", "mediaType"]', '["title", "mediaType"]')
    MATERIALIZE.write_text(text, encoding="utf-8")
    return True


def patch_base() -> bool:
    text = BASE.read_text(encoding="utf-8")
    changed = False
    if '["title", "year", "mediaType"]' in text:
        text = text.replace('["title", "year", "mediaType"]', '["title", "mediaType"]')
        changed = True
    if '"routeProofVersion": int(incoming_model.get("routeProofVersion") or 0),' not in text:
        old = '''        "apiRecipe": (
            incoming_model.get("apiRecipe")
            if isinstance(incoming_model.get("apiRecipe"), dict)
            else None
        ),
        "sourceRuntimeFamily": str(incoming_model.get("sourceRuntimeFamily") or "unknown"),'''
        new = '''        "apiRecipe": (
            incoming_model.get("apiRecipe")
            if isinstance(incoming_model.get("apiRecipe"), dict)
            else None
        ),
        "routeProofVersion": int(incoming_model.get("routeProofVersion") or 0),
        "sourceRuntimeFamily": str(incoming_model.get("sourceRuntimeFamily") or "unknown"),'''
        text = replace_once(text, old, new, "provider-data-proof-version")
        changed = True
    BASE.write_text(text, encoding="utf-8")
    return changed


def patch_sequential() -> bool:
    text = SEQUENTIAL.read_text(encoding="utf-8")
    changed = False
    if "from provider_route_proof import filter_recipe_by_live_routes" not in text:
        anchor = "from typing import Any\n"
        if anchor not in text:
            raise AssertionError("sequential import anchor missing")
        text = text.replace(anchor, anchor + "\nfrom provider_route_proof import filter_recipe_by_live_routes\n", 1)
        changed = True

    old_model = '''    live_set = set(evaluation["liveRoutes"])
    execution_plan_set = set(model.get("routes") or [])
    candidate_model_recipe = model.get("candidateApiRecipe")
    if isinstance(candidate_model_recipe, dict):
        model["apiRecipe"] = copy.deepcopy(candidate_model_recipe)
'''
    new_model = f'''    live_set = set(evaluation["liveRoutes"])
    execution_plan_set = set(model.get("routes") or [])
    # {MARKER}
    candidate_model_recipe = model.get("candidateApiRecipe")
    filtered_model_recipe = (
        filter_recipe_by_live_routes(candidate_model_recipe, live_set)
        if isinstance(candidate_model_recipe, dict)
        else None
    )
    if isinstance(filtered_model_recipe, dict):
        filtered_model_recipe["proofModelVersion"] = 5
        model["apiRecipe"] = filtered_model_recipe
    else:
        model.pop("apiRecipe", None)
    model["routeProofVersion"] = 5
'''
    if old_model in text:
        text = replace_once(text, old_model, new_model, "sequential-filter-model-recipe")
        changed = True

    old_patch = '''        candidate_recipe = patch.get("candidate_api_recipe") if isinstance(patch.get("candidate_api_recipe"), dict) else patch.get("api_recipe")
        if isinstance(candidate_recipe, dict):
            patch["api_recipe"] = copy.deepcopy(candidate_recipe)
        patch["live_route_gate"] = {'''
    new_patch = '''        candidate_recipe = patch.get("candidate_api_recipe") if isinstance(patch.get("candidate_api_recipe"), dict) else patch.get("api_recipe")
        filtered_patch_recipe = (
            filter_recipe_by_live_routes(candidate_recipe, live_set)
            if isinstance(candidate_recipe, dict)
            else None
        )
        if isinstance(filtered_patch_recipe, dict):
            filtered_patch_recipe["proofModelVersion"] = 5
            patch["api_recipe"] = filtered_patch_recipe
        else:
            patch.pop("api_recipe", None)
        patch["route_proof_version"] = 5
        patch["live_route_gate"] = {'''
    if old_patch in text:
        text = replace_once(text, old_patch, new_patch, "sequential-filter-patch-recipe")
        changed = True

    SEQUENTIAL.write_text(text, encoding="utf-8")
    return changed


def validate() -> None:
    discover = DISCOVER.read_text(encoding="utf-8")
    materialize = MATERIALIZE.read_text(encoding="utf-8")
    base = BASE.read_text(encoding="utf-8")
    sequential = SEQUENTIAL.read_text(encoding="utf-8")
    if f"# {MARKER}" not in discover or '"candidateRoutes": learned_routes[:64]' not in discover or '"routes": []' not in discover:
        raise AssertionError("static discovery still exposes executable routes")
    if '"candidateApiRecipe": recipe' not in discover or '"apiRecipe": None' not in discover:
        raise AssertionError("static discovery still exposes executable apiRecipe")
    for needle in (
        "proof_version >= 5",
        "recipe_proof >= 5",
        '"routeProofVersion": proof_version',
    ):
        if needle not in materialize:
            raise AssertionError(f"materializer proof-v5 guard missing: {needle}")
    if '["title", "year", "mediaType"]' in materialize or '["title", "year", "mediaType"]' in base:
        raise AssertionError("generic catalogue preflight still requires year")
    if '"routeProofVersion": int(incoming_model.get("routeProofVersion") or 0)' not in base:
        raise AssertionError("Provider DATA drops route proof version")
    for needle in (
        "filter_recipe_by_live_routes(candidate_model_recipe, live_set)",
        "filter_recipe_by_live_routes(candidate_recipe, live_set)",
        'patch["route_proof_version"] = 5',
        'model["routeProofVersion"] = 5',
    ):
        if needle not in sequential:
            raise AssertionError(f"sequential finalizer proof-v5 guard missing: {needle}")


def main() -> int:
    changed = [patch_discover(), patch_materialize(), patch_base(), patch_sequential()]
    validate()
    print(
        "PROVIDER_V3_ROUTE_PROOF_AUTHORITY_V5_OK "
        f"changed={str(any(changed)).lower()} static_candidates_only=1 proof_v5_runtime_only=1 "
        "api_recipe_field_filtered=1 catalogue_preflight_year_required=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
