#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
p = ROOT / 'scripts/build_hub46_blocker_inventory.py'
s = p.read_text(encoding='utf-8')

old = '''def mechanism_for(*, strategy: str, recipe: dict[str, Any], legos: list[str], route_kinds: set[str], authorities: list[str]) -> str:
    recipe_kind = str(recipe.get("recipeKind") or recipe.get("recipe_kind") or "").strip().casefold()
    if recipe:
        if recipe_kind == "typed-resolver-api":
            return "typed-resolver-api"
        return "api-recipe"
    if legos:
        return "provider-lego"
'''
new = '''def mechanism_for(*, strategy: str, recipe: dict[str, Any], legos: list[str], route_kinds: set[str], authorities: list[str], search_plan_count: int = 0, value_plan_count: int = 0, external_identity_count: int = 0) -> str:
    recipe_kind = str(recipe.get("recipeKind") or recipe.get("recipe_kind") or "").strip().casefold()
    if recipe:
        if recipe_kind == "typed-resolver-api":
            return "typed-resolver-api"
        return "api-recipe"
    if legos:
        return "provider-lego"
    if search_plan_count and value_plan_count:
        return "structured-search-value-plan"
    if value_plan_count:
        return "provider-value-plan"
    if search_plan_count:
        return "structured-search-plan"
    if external_identity_count:
        return "external-identity-plan"
'''
assert old in s, 'mechanism_for anchor missing'
s = s.replace(old, new, 1)

old = '''        legos = uniq(list(patch.get("provider_lego_scripts") or []))

        routes = uniq(
'''
new = '''        legos = uniq(list(patch.get("provider_lego_scripts") or []))
        search_plan = [row for row in (patch.get("search_request_plan") or model.get("searchRequestPlan") or []) if isinstance(row, dict)]
        value_plan = [row for row in (patch.get("provider_value_plan") or model.get("providerValuePlan") or []) if isinstance(row, dict)]
        external_identity_plan = [row for row in (patch.get("external_identity_plan") or model.get("externalIdentityPlan") or []) if isinstance(row, dict)]

        routes = uniq(
'''
assert old in s, 'lego/routes anchor missing'
s = s.replace(old, new, 1)

old = '''            route_kinds=route_kinds,
            authorities=authorities,
        )
'''
new = '''            route_kinds=route_kinds,
            authorities=authorities,
            search_plan_count=len(search_plan),
            value_plan_count=len(value_plan),
            external_identity_count=len(external_identity_plan),
        )
'''
assert old in s, 'mechanism call anchor missing'
s = s.replace(old, new, 1)

old = '''            if not (route_kinds & EXEC_ROUTE_KINDS):
                opaque_reasons.append("no_executable_route_shape")
'''
new = '''            if not (route_kinds & EXEC_ROUTE_KINDS) and not search_plan and not value_plan and not external_identity_plan:
                opaque_reasons.append("no_executable_route_shape_or_structured_plan")
'''
assert old in s, 'opaque route anchor missing'
s = s.replace(old, new, 1)

old = '''            "providerLegos": legos,
            "routeDataState": disposition.get("routeDataState"),
'''
new = '''            "providerLegos": legos,
            "searchRequestPlanCount": len(search_plan),
            "providerValuePlanCount": len(value_plan),
            "externalIdentityPlanCount": len(external_identity_plan),
            "routeDataState": disposition.get("routeDataState"),
'''
assert old in s, 'output plan-count anchor missing'
s = s.replace(old, new, 1)

p.write_text(s, encoding='utf-8')
print('HUB46_INVENTORY_STRUCTURED_PLAN_PATCHED search_plan=1 value_plan=1 external_identity=1')
