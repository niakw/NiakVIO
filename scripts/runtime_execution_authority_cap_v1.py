#!/usr/bin/env python3
"""Select at most one canonical executable authority per semantic lane.

Priority follows the ProviderBase proof authority:
provider-value correlation > API recipe > external-id > structured search > flat route.
A lower-priority plan remains active only when it covers a semantic lane not
covered by a stronger executable plan. Evidence is retained in routeData and
route-proof metadata, so suppressed alternatives can be re-derived later.
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

from runtime_route_plan_cap_v1 import route_metadata, semantic_lane, unique

ROOT = Path(__file__).resolve().parents[1]
OVERRIDES = ROOT / "provider-overrides.json"
KNOWLEDGE = ROOT / "automation" / "provider-v3-static-knowledge.json"
MAX_AUTHORITIES = 3
LANES = {"movie", "tv", "anime"}
PRIORITY = {
    "providerValuePlan": 500,
    "apiRecipe": 450,
    "externalIdentityPlan": 400,
    "searchRequestPlan": 350,
    "route": 250,
}


def lanes_from_values(values: object) -> set[str]:
    return {semantic_lane(value) for value in values or [] if semantic_lane(value)}


def supported_lanes(model: dict[str, Any], route_data: list[dict[str, Any]]) -> set[str]:
    lanes = lanes_from_values(model.get("supportedTypes") or [])
    if lanes:
        return lanes
    return {
        semantic_lane(row.get("semanticType"))
        for row in route_data
        if isinstance(row, dict) and semantic_lane(row.get("semanticType"))
    } or {"movie"}


def recipe_lanes(recipe: dict[str, Any], supported: set[str]) -> set[str]:
    lanes: set[str] = set()
    if recipe.get("movieRoute"):
        lanes.add("movie")
    if recipe.get("episodeRoute"):
        lanes.add("tv")
        if "anime" in supported:
            lanes.add("anime")
    if recipe.get("directRoute"):
        lanes |= set(supported)
    return lanes & supported


def candidate_rows(model: dict[str, Any], route_data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    supported = supported_lanes(model, route_data)
    out: list[dict[str, Any]] = []
    order = 0

    for field in ("providerValuePlan", "externalIdentityPlan", "searchRequestPlan"):
        for index, plan in enumerate(model.get(field) or []):
            if not isinstance(plan, dict):
                continue
            lanes = lanes_from_values(plan.get("semanticTypes") or []) or set(supported)
            lanes &= supported
            if not lanes:
                continue
            out.append({"owner": field, "index": index, "lanes": lanes, "priority": PRIORITY[field], "order": order})
            order += 1

    recipe = model.get("apiRecipe") if isinstance(model.get("apiRecipe"), dict) else None
    if recipe:
        lanes = recipe_lanes(recipe, supported)
        if lanes:
            out.append({"owner": "apiRecipe", "index": 0, "lanes": lanes, "priority": PRIORITY["apiRecipe"], "order": order})
            order += 1

    meta = route_metadata(route_data)
    for index, route in enumerate(unique(model.get("routes") or [], 256)):
        lanes = set(meta.get(route, {}).get("lanes", set())) & supported
        if not lanes:
            # Historical active route without routeData is a lowest-priority
            # generic candidate; it may fill a lane only when no proof-owned
            # structured authority covers it.
            lanes = set(supported)
        out.append({"owner": "route", "index": index, "route": route, "lanes": lanes, "priority": PRIORITY["route"], "order": order})
        order += 1
    return out


def select_authorities(model: dict[str, Any], route_data: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    supported = supported_lanes(model, route_data)
    candidates = candidate_rows(model, route_data)
    selected: list[dict[str, Any]] = []
    covered: set[str] = set()

    # Proof authority first, then semantic coverage, then stable source order.
    ranked = sorted(
        candidates,
        key=lambda row: (int(row["priority"]), len(row["lanes"]), -int(row["order"])),
        reverse=True,
    )
    for candidate in ranked:
        fresh = set(candidate["lanes"]) - covered
        if not fresh:
            continue
        selected.append(candidate)
        covered |= set(candidate["lanes"])
        if covered >= supported or len(selected) >= MAX_AUTHORITIES:
            break

    # At most three semantic lanes exist, so missing coverage after three means
    # the DATA is internally inconsistent and must fail closed.
    missing = supported - covered
    return selected, {
        "candidateCount": len(candidates),
        "selectedCount": len(selected),
        "supportedLanes": sorted(supported),
        "coveredLanes": sorted(covered),
        "missingLanes": sorted(missing),
        "owners": [row["owner"] for row in selected],
    }


def apply_selection(model: dict[str, Any], patch: dict[str, Any], selected: list[dict[str, Any]]) -> None:
    selected_by_owner: dict[str, list[dict[str, Any]]] = {}
    for row in selected:
        selected_by_owner.setdefault(str(row["owner"]), []).append(row)

    field_pairs = (
        ("providerValuePlan", "provider_value_plan"),
        ("externalIdentityPlan", "external_identity_plan"),
        ("searchRequestPlan", "search_request_plan"),
    )
    for model_key, patch_key in field_pairs:
        current = [row for row in model.get(model_key) or [] if isinstance(row, dict)]
        keep_indices = {int(row["index"]) for row in selected_by_owner.get(model_key, [])}
        kept = [copy.deepcopy(row) for index, row in enumerate(current) if index in keep_indices]
        if kept:
            model[model_key] = kept
            patch[patch_key] = copy.deepcopy(kept)
        else:
            model.pop(model_key, None)
            patch.pop(patch_key, None)

    if selected_by_owner.get("apiRecipe"):
        if isinstance(model.get("apiRecipe"), dict):
            patch["api_recipe"] = copy.deepcopy(model["apiRecipe"])
    else:
        model.pop("apiRecipe", None)
        patch.pop("api_recipe", None)

    routes = unique(model.get("routes") or [], 256)
    keep_route_indices = {int(row["index"]) for row in selected_by_owner.get("route", [])}
    kept_routes = [route for index, route in enumerate(routes) if index in keep_route_indices]
    model["routes"] = kept_routes
    patch["learned_routes"] = kept_routes


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: object required")
    return value


def write(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def enforce_execution_authority_cap(
    *, overrides_path: Path = OVERRIDES, knowledge_path: Path = KNOWLEDGE
) -> dict[str, Any]:
    overrides = load(overrides_path)
    knowledge = load(knowledge_path)
    patches = overrides.get("provider_patches") if isinstance(overrides.get("provider_patches"), dict) else {}
    providers = knowledge.get("providers") if isinstance(knowledge.get("providers"), dict) else {}
    changed = 0
    max_candidates = 0
    max_selected = 0
    missing: list[str] = []

    for provider_id, static_row in providers.items():
        if not isinstance(static_row, dict):
            continue
        patch = patches.get(provider_id)
        if not isinstance(patch, dict):
            continue
        model = static_row.get("model") if isinstance(static_row.get("model"), dict) else {}
        route_data = [row for row in model.get("routeData") or [] if isinstance(row, dict)]
        before = json.dumps({
            "routes": model.get("routes"),
            "providerValuePlan": model.get("providerValuePlan"),
            "apiRecipe": model.get("apiRecipe"),
            "externalIdentityPlan": model.get("externalIdentityPlan"),
            "searchRequestPlan": model.get("searchRequestPlan"),
        }, sort_keys=True, default=str)
        selected, audit = select_authorities(model, route_data)
        max_candidates = max(max_candidates, audit["candidateCount"])
        max_selected = max(max_selected, audit["selectedCount"])
        if audit["selectedCount"] > MAX_AUTHORITIES:
            raise RuntimeError(f"{provider_id}: selected authorities={audit['selectedCount']}")
        if audit["missingLanes"] and audit["candidateCount"]:
            missing.append(f"{provider_id}:{','.join(audit['missingLanes'])}")
        apply_selection(model, patch, selected)
        after = json.dumps({
            "routes": model.get("routes"),
            "providerValuePlan": model.get("providerValuePlan"),
            "apiRecipe": model.get("apiRecipe"),
            "externalIdentityPlan": model.get("externalIdentityPlan"),
            "searchRequestPlan": model.get("searchRequestPlan"),
        }, sort_keys=True, default=str)
        if before != after:
            changed += 1
        proof = model.get("routeProof") if isinstance(model.get("routeProof"), dict) else {}
        proof["canonicalExecutionAuthorityCap"] = MAX_AUTHORITIES
        proof["canonicalExecutionAuthority"] = audit
        model["routeProof"] = proof
        patch["route_proof"] = copy.deepcopy(proof)
        static_row["model"] = model
        providers[provider_id] = static_row
        patches[provider_id] = patch

    overrides["provider_patches"] = patches
    knowledge["providers"] = providers
    write(overrides_path, overrides)
    write(knowledge_path, knowledge)
    return {
        "providerCount": len(providers),
        "changedProviders": changed,
        "maxCandidates": max_candidates,
        "maxSelected": max_selected,
        "missingCoverageProviders": missing,
        "cap": MAX_AUTHORITIES,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--overrides", type=Path, default=OVERRIDES)
    parser.add_argument("--knowledge", type=Path, default=KNOWLEDGE)
    args = parser.parse_args()
    summary = enforce_execution_authority_cap(
        overrides_path=args.overrides if args.overrides.is_absolute() else ROOT / args.overrides,
        knowledge_path=args.knowledge if args.knowledge.is_absolute() else ROOT / args.knowledge,
    )
    print(
        "RUNTIME_EXECUTION_AUTHORITY_CAP_V1_OK "
        f"providers={summary['providerCount']} changed={summary['changedProviders']} "
        f"max_candidates={summary['maxCandidates']} max_selected={summary['maxSelected']} cap={summary['cap']} "
        f"missing_coverage={len(summary['missingCoverageProviders'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
