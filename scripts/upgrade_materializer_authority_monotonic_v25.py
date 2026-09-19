#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALL = ROOT / 'scripts' / 'materialize_provider_v3_all.py'
ONE = ROOT / 'scripts' / 'materialize_provider_v3_one.py'
MARKER = '# MATERIALIZER_EXECUTION_AUTHORITY_MONOTONIC_V25'


def patch_one() -> bool:
    text = ONE.read_text(encoding='utf-8')
    if MARKER in text:
        return False
    old = '''    recipe = model.get("apiRecipe")\n    if isinstance(recipe, dict) and recipe:\n        canonical_recipe = copy.deepcopy(recipe)\n        if patch.get("api_recipe") != canonical_recipe:\n            patch["api_recipe"] = canonical_recipe\n            changed = True\n\n    # Historical replacement graphs may contain the reverse of the current\n'''
    new = '''    # MATERIALIZER_EXECUTION_AUTHORITY_MONOTONIC_V25\n    # Static knowledge may reconcile address metadata, but it must never promote\n    # or replace executable route/API authority. Runtime authority is written by\n    # proof/repair and remains monotonic until fresh positive proof supersedes it.\n\n    # Historical replacement graphs may contain the reverse of the current\n'''
    if old not in text:
        raise SystemExit('materialize_provider_v3_one.py authority anchor not found')
    ONE.write_text(text.replace(old, new, 1), encoding='utf-8')
    return True


def patch_all() -> bool:
    text = ALL.read_text(encoding='utf-8')
    if MARKER in text:
        return False
    old = '''    # PROVIDER_V3_ROUTE_PROOF_AUTHORITY_V5\n    patch_proof = int(patch.get("route_proof_version") or 0)\n    static_proof = int(static_model.get("routeProofVersion") or 0)\n    proof_version = max(patch_proof, static_proof)\n    routes: list[str] = []\n    if proof_version >= 5:\n        for value in [*(patch.get("learned_routes") or []), *(static_model.get("routes") or [])]:\n            item = str(value).strip()\n            if item and item != "/" and item not in routes:\n                routes.append(item)\n\n    patch_recipe = patch.get("api_recipe") if isinstance(patch.get("api_recipe"), dict) else None\n    static_recipe = static_model.get("apiRecipe") if isinstance(static_model.get("apiRecipe"), dict) else None\n    candidate_recipe = patch_recipe or static_recipe\n    recipe_proof = int(candidate_recipe.get("proofModelVersion") or 0) if isinstance(candidate_recipe, dict) else 0\n    api_recipe = candidate_recipe if proof_version >= 5 and recipe_proof >= 5 else None\n\n    return {\n'''
    new = '''    # PROVIDER_V3_ROUTE_PROOF_AUTHORITY_V5\n    patch_proof = int(patch.get("route_proof_version") or 0)\n    static_proof = int(static_model.get("routeProofVersion") or 0)\n\n    def proof5_rows(value: object) -> list[dict[str, Any]]:\n        return [\n            dict(row) for row in (value or [])\n            if isinstance(row, dict) and int(row.get("proofModelVersion") or 0) >= 5\n        ] if isinstance(value, list) else []\n\n    patch_routes = [\n        str(value).strip() for value in (patch.get("learned_routes") or [])\n        if str(value).strip() and str(value).strip() != "/"\n    ]\n    patch_recipe = patch.get("api_recipe") if isinstance(patch.get("api_recipe"), dict) else None\n    patch_recipe_proof = int(patch_recipe.get("proofModelVersion") or 0) if isinstance(patch_recipe, dict) else 0\n    patch_search_plan = proof5_rows(patch.get("search_request_plan"))\n    patch_provider_value_plan = proof5_rows(patch.get("provider_value_plan"))\n    patch_external_identity_plan = proof5_rows(patch.get("external_identity_plan"))\n    # MATERIALIZER_EXECUTION_AUTHORITY_MONOTONIC_V25\n    patch_has_execution_authority = bool(\n        patch_proof >= 5 and (\n            patch_routes\n            or (patch_recipe is not None and patch_recipe_proof >= 5)\n            or patch_search_plan\n            or patch_provider_value_plan\n            or patch_external_identity_plan\n        )\n    )\n    proof_version = max(patch_proof, static_proof)\n    routes: list[str] = []\n    route_values = patch_routes if patch_has_execution_authority else [\n        *(patch.get("learned_routes") or []), *(static_model.get("routes") or [])\n    ]\n    if proof_version >= 5:\n        for value in route_values:\n            item = str(value).strip()\n            if item and item != "/" and item not in routes:\n                routes.append(item)\n\n    static_recipe = static_model.get("apiRecipe") if isinstance(static_model.get("apiRecipe"), dict) else None\n    candidate_recipe = patch_recipe if patch_recipe is not None else (None if patch_has_execution_authority else static_recipe)\n    recipe_proof = int(candidate_recipe.get("proofModelVersion") or 0) if isinstance(candidate_recipe, dict) else 0\n    api_recipe = candidate_recipe if proof_version >= 5 and recipe_proof >= 5 else None\n\n    def execution_list(patch_key: str, static_key: str) -> list[dict[str, Any]]:\n        if patch_has_execution_authority:\n            value = patch.get(patch_key)\n        else:\n            value = patch.get(patch_key) or static_model.get(static_key)\n        return [dict(row) for row in (value or []) if isinstance(row, dict)] if isinstance(value, list) else []\n\n    def execution_strings(patch_key: str, static_key: str, limit: int) -> list[str]:\n        if patch_has_execution_authority:\n            value = patch.get(patch_key)\n        else:\n            value = patch.get(patch_key) or static_model.get(static_key)\n        return [str(item).strip() for item in (value or []) if str(item).strip()][:limit] if isinstance(value, list) else []\n\n    return {\n'''
    if old not in text:
        raise SystemExit('materialize_provider_v3_all.py proof authority anchor not found')
    text = text.replace(old, new, 1)
    replacements = {
'''        "proofSearchBases": [\n            str(value).strip()\n            for value in (patch.get("proof_search_bases") or static_model.get("proofSearchBases") or [])\n            if str(value).strip()\n        ][:6],''': '''        "proofSearchBases": execution_strings("proof_search_bases", "proofSearchBases", 6),''',
'''        "proofDetailBases": [\n            str(value).strip()\n            for value in (patch.get("proof_detail_bases") or static_model.get("proofDetailBases") or [])\n            if str(value).strip()\n        ][:6],''': '''        "proofDetailBases": execution_strings("proof_detail_bases", "proofDetailBases", 6),''',
'''        "proofProtectedHosts": [\n            str(value).strip().casefold()\n            for value in (patch.get("proof_protected_hosts") or static_model.get("proofProtectedHosts") or [])\n            if str(value).strip()\n        ][:24],''': '''        "proofProtectedHosts": [value.casefold() for value in execution_strings("proof_protected_hosts", "proofProtectedHosts", 24)],''',
'''        "searchRequestPlan": [\n            dict(row)\n            for row in (patch.get("search_request_plan") or static_model.get("searchRequestPlan") or [])\n            if isinstance(row, dict)\n        ][:6],''': '''        "searchRequestPlan": execution_list("search_request_plan", "searchRequestPlan")[:6],''',
'''        "providerValuePlan": [\n            dict(row)\n            for row in (patch.get("provider_value_plan") or static_model.get("providerValuePlan") or [])\n            if isinstance(row, dict)\n        ][:12],''': '''        "providerValuePlan": execution_list("provider_value_plan", "providerValuePlan")[:12],''',
'''        "externalIdentityPlan": [\n            dict(row)\n            for row in (patch.get("external_identity_plan") or static_model.get("externalIdentityPlan") or [])\n            if isinstance(row, dict)\n        ][:4],''': '''        "externalIdentityPlan": execution_list("external_identity_plan", "externalIdentityPlan")[:4],''',
    }
    for before, after in replacements.items():
        if before not in text:
            raise SystemExit('materialize_provider_v3_all.py return authority anchor not found')
        text = text.replace(before, after, 1)
    ALL.write_text(text, encoding='utf-8')
    return True


if __name__ == '__main__':
    changed = [name for name, value in [('one', patch_one()), ('all', patch_all())] if value]
    print('MATERIALIZER_AUTHORITY_MONOTONIC_V25 changed=' + (','.join(changed) if changed else 'none'))
