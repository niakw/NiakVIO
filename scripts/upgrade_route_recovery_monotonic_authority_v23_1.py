#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / 'scripts' / 'recover_provider_routes_from_upstreams.py'
MARKER = '# ROUTE_RECOVERY_MONOTONIC_STRUCTURED_AUTHORITY_V23_1'


def once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{label}: expected one anchor, got {count}')
    return text.replace(old, new, 1)


def patch() -> bool:
    text = TARGET.read_text(encoding='utf-8')
    if MARKER in text:
        return False
    if '# ROUTE_RECOVERY_MONOTONIC_PROOF_V23' not in text:
        raise SystemExit('V23 prerequisite missing')

    anchor = '''def _preserved_string_list(patch_value: object, model_value: object, limit: int) -> list[str]:\n    rows = patch_value if isinstance(patch_value, list) else model_value if isinstance(model_value, list) else []\n    return unique([str(value).strip() for value in rows if str(value).strip()], limit)\n\ndef apply_recovery(report: dict[str, Any]) -> dict[str, Any]:\n'''
    replacement = '''def _preserved_string_list(patch_value: object, model_value: object, limit: int) -> list[str]:\n    rows = patch_value if isinstance(patch_value, list) else model_value if isinstance(model_value, list) else []\n    return unique([str(value).strip() for value in rows if str(value).strip()], limit)\n\n# ROUTE_RECOVERY_MONOTONIC_STRUCTURED_AUTHORITY_V23_1\ndef _proof_v5_plan_rows(patch_value: object, model_value: object, limit: int) -> list[dict[str, Any]]:\n    rows = patch_value if isinstance(patch_value, list) else model_value if isinstance(model_value, list) else []\n    return [\n        copy.deepcopy(row)\n        for row in rows\n        if isinstance(row, dict) and int(row.get("proofModelVersion") or 0) >= PROOF_VERSION\n    ][:limit]\n\ndef _proof_v5_structured_authority(patch: dict[str, Any], model: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:\n    versions: list[int] = []\n    for raw in (patch.get("route_proof_version"), model.get("routeProofVersion")):\n        try:\n            versions.append(int(raw or 0))\n        except (TypeError, ValueError):\n            versions.append(0)\n    if max(versions or [0]) < PROOF_VERSION:\n        return {}\n    out = {\n        "search": _proof_v5_plan_rows(patch.get("search_request_plan"), model.get("searchRequestPlan"), 6),\n        "providerValue": _proof_v5_plan_rows(patch.get("provider_value_plan"), model.get("providerValuePlan"), 12),\n        "externalIdentity": _proof_v5_plan_rows(patch.get("external_identity_plan"), model.get("externalIdentityPlan"), 4),\n    }\n    return {key: value for key, value in out.items() if value}\n\ndef apply_recovery(report: dict[str, Any]) -> dict[str, Any]:\n'''
    text = once(text, anchor, replacement, 'v23.1-helper')

    old = '''        preserve_existing_execution_authority, existing_proven_recipe = _proof_v5_execution_authority(patch, model)\n        existing_proof_search_bases = _preserved_string_list(patch.get("proof_search_bases"), model.get("proofSearchBases"), 6)\n'''
    new = '''        preserve_existing_execution_authority, existing_proven_recipe = _proof_v5_execution_authority(patch, model)\n        existing_structured_authority = _proof_v5_structured_authority(patch, model)\n        preserve_existing_execution_authority = bool(preserve_existing_execution_authority or existing_structured_authority)\n        existing_search_request_plan = copy.deepcopy(existing_structured_authority.get("search") or [])\n        existing_provider_value_plan = copy.deepcopy(existing_structured_authority.get("providerValue") or [])\n        existing_external_identity_plan = copy.deepcopy(existing_structured_authority.get("externalIdentity") or [])\n        existing_proof_search_bases = _preserved_string_list(patch.get("proof_search_bases"), model.get("proofSearchBases"), 6)\n'''
    text = once(text, old, new, 'v23.1-snapshot')

    old = '''        else:\n            patch.pop("search_request_plan", None)\n            model.pop("searchRequestPlan", None)\n\n        provider_value_plan = _positive_provider_value_plans(route_data)\n'''
    new = '''        elif preserve_existing_execution_authority and existing_search_request_plan:\n            patch["search_request_plan"] = copy.deepcopy(existing_search_request_plan)\n            model["searchRequestPlan"] = copy.deepcopy(existing_search_request_plan)\n        else:\n            patch.pop("search_request_plan", None)\n            model.pop("searchRequestPlan", None)\n\n        provider_value_plan = _positive_provider_value_plans(route_data)\n'''
    text = once(text, old, new, 'v23.1-search')

    old = '''        else:\n            patch.pop("provider_value_plan", None)\n            model.pop("providerValuePlan", None)\n\n        external_identity_plan = _positive_external_identity_plan(route_data, patch)\n'''
    new = '''        elif preserve_existing_execution_authority and existing_provider_value_plan:\n            patch["provider_value_plan"] = copy.deepcopy(existing_provider_value_plan)\n            model["providerValuePlan"] = copy.deepcopy(existing_provider_value_plan)\n        else:\n            patch.pop("provider_value_plan", None)\n            model.pop("providerValuePlan", None)\n\n        external_identity_plan = _positive_external_identity_plan(route_data, patch)\n'''
    text = once(text, old, new, 'v23.1-provider-value')

    old = '''        else:\n            patch.pop("external_identity_plan", None)\n            model.pop("externalIdentityPlan", None)\n        recipe = recovered.get("apiRecipe") if isinstance(recovered.get("apiRecipe"), dict) else None\n'''
    new = '''        elif preserve_existing_execution_authority and existing_external_identity_plan:\n            patch["external_identity_plan"] = copy.deepcopy(existing_external_identity_plan)\n            model["externalIdentityPlan"] = copy.deepcopy(existing_external_identity_plan)\n        else:\n            patch.pop("external_identity_plan", None)\n            model.pop("externalIdentityPlan", None)\n        recipe = recovered.get("apiRecipe") if isinstance(recovered.get("apiRecipe"), dict) else None\n'''
    text = once(text, old, new, 'v23.1-external')

    TARGET.write_text(text, encoding='utf-8')
    return True


if __name__ == '__main__':
    changed = patch()
    print(f'ROUTE_RECOVERY_MONOTONIC_STRUCTURED_AUTHORITY_V23_1 changed={str(changed).lower()}')
