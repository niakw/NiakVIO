#!/usr/bin/env python3
"""Rank Provider execution authorities without deleting evidence-backed paths.

Provider-value correlation, API recipes, external-id plans, structured search, and
flat routes do not always represent mutually exclusive alternatives. A real
provider may require several of them in sequence or as fallbacks/fan-out within
the same semantic lane. Therefore this module records preferred authorities for
ordering/latency only; it never removes another proven authority merely because a
higher-priority one covers the same movie/tv/anime lane.
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
NORMAL_SEMANTIC_LANE_COUNT = 3
MAX_AUTHORITIES = NORMAL_SEMANTIC_LANE_COUNT  # compatibility alias; no longer a destructive cap
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
    if recipe.get("searchRoute") and not lanes:
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
            lanes = set(supported)
        out.append({"owner": "route", "index": index, "route": route, "lanes": lanes, "priority": PRIORITY["route"], "order": order})
        order += 1
    return out


def select_authorities(model: dict[str, Any], route_data: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Return preferred authorities per lane for ordering, not a destructive selection."""
    supported = supported_lanes(model, route_data)
    candidates = candidate_rows(model, route_data)
    ranked = sorted(
        candidates,
        key=lambda row: (int(row["priority"]), len(row["lanes"]), -int(row["order"])),
        reverse=True,
    )
    preferred: list[dict[str, Any]] = []
    covered: set[str] = set()
    for candidate in ranked:
        fresh = set(candidate["lanes"]) - covered
        if not fresh:
            continue
        preferred.append(candidate)
        covered |= set(candidate["lanes"])
        if covered >= supported:
            break
    missing = supported - covered
    return preferred, {
        "candidateCount": len(candidates),
        "preferredCount": len(preferred),
        "selectedCount": len(preferred),  # compatibility field
        "supportedLanes": sorted(supported),
        "coveredLanes": sorted(covered),
        "missingLanes": sorted(missing),
        "preferredOwners": [row["owner"] for row in preferred],
        "owners": [row["owner"] for row in preferred],
        "destructiveFiltering": False,
        "allEvidenceBackedAuthoritiesPreserved": True,
    }


def apply_selection(model: dict[str, Any], patch: dict[str, Any], selected: list[dict[str, Any]]) -> None:
    """Compatibility no-op: authority ranking must not delete valid runtime paths."""
    del model, patch, selected


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
    max_candidates = 0
    max_preferred = 0
    missing: list[str] = []
    multi_authority_providers = 0

    for provider_id, static_row in providers.items():
        if not isinstance(static_row, dict):
            continue
        patch = patches.get(provider_id)
        if not isinstance(patch, dict):
            continue
        model = static_row.get("model") if isinstance(static_row.get("model"), dict) else {}
        route_data = [row for row in model.get("routeData") or [] if isinstance(row, dict)]
        preferred, audit = select_authorities(model, route_data)
        max_candidates = max(max_candidates, audit["candidateCount"])
        max_preferred = max(max_preferred, audit["preferredCount"])
        if audit["candidateCount"] > audit["preferredCount"]:
            multi_authority_providers += 1
        if audit["missingLanes"] and audit["candidateCount"]:
            missing.append(f"{provider_id}:{','.join(audit['missingLanes'])}")

        proof = model.get("routeProof") if isinstance(model.get("routeProof"), dict) else {}
        proof.pop("canonicalExecutionAuthorityCap", None)
        proof["canonicalExecutionAuthorityPolicy"] = "preferred-order-only-preserve-all-proven-authorities"
        proof["canonicalExecutionAuthority"] = audit
        proof["canonicalExecutionPreference"] = [
            {
                "owner": row["owner"],
                "index": int(row["index"]),
                "lanes": sorted(row["lanes"]),
                **({"route": row["route"]} if row.get("route") else {}),
            }
            for row in preferred
        ]
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
        "changedProviders": 0,
        "maxCandidates": max_candidates,
        "maxPreferred": max_preferred,
        "maxSelected": max_preferred,
        "multiAuthorityProviders": multi_authority_providers,
        "missingCoverageProviders": missing,
        "target": NORMAL_SEMANTIC_LANE_COUNT,
        "cap": NORMAL_SEMANTIC_LANE_COUNT,
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
        "RUNTIME_EXECUTION_AUTHORITY_POLICY_V2_OK "
        f"providers={summary['providerCount']} max_candidates={summary['maxCandidates']} "
        f"max_preferred={summary['maxPreferred']} multi_authority={summary['multiAuthorityProviders']} "
        f"missing_coverage={len(summary['missingCoverageProviders'])} target={summary['target']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
