#!/usr/bin/env python3
"""Project many HTTP proof observations into at most three runtime route plans.

Route recovery is intentionally evidence-rich: routeData may contain every proven
search/detail/episode/player/source hop.  The Provider runtime is intentionally
small: normally one common plan, otherwise movie + tv, with a third anime plan
only when anime genuinely needs a distinct entry route.

This module never deletes routeData/candidate evidence.  It only constrains the
executable projections (`learned_routes` / `model.routes`).
"""
from __future__ import annotations

import argparse
import copy
import json
import urllib.parse
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OVERRIDES = ROOT / "provider-overrides.json"
KNOWLEDGE = ROOT / "automation" / "provider-v3-static-knowledge.json"
MAX_RUNTIME_ROUTE_PLANS = 3
LANES = ("movie", "tv", "anime")
ROLE_PRIORITY = {
    "search": 900,
    "api": 760,
    "detail": 700,
    "episode": 640,
    "player": 220,
    "source": 180,
}


def cid(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def semantic_lane(value: object) -> str:
    lane = str(value or "").strip().casefold()
    if lane == "series":
        lane = "tv"
    return lane if lane in LANES else ""


def unique(values: list[object], limit: int = 256) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for raw in values:
        value = str(raw or "").strip()
        if not value or value in seen:
            continue
        seen.add(value)
        out.append(value)
        if len(out) >= limit:
            break
    return out


def identity_bearing(route: str) -> bool:
    value = str(route or "").strip().casefold()
    if not value:
        return False
    if any(token in value for token in ("{query}", "{title}", "{slug}", "{id}", "{tmdbid}", "{tmdb_id}", "{imdbid}", "{imdb_id}")):
        return True
    try:
        path = urllib.parse.urlsplit(value).path
    except ValueError:
        path = value
    return bool(path and (
        "/search" in path
        or "/recherche" in path
        or "/title/" in path
        or "/movie/" in path
        or "/film/" in path
        or "/series/" in path
        or "/tv/" in path
        or "/anime/" in path
        or "/watch/" in path
    ))


def route_metadata(route_data: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    meta: dict[str, dict[str, Any]] = {}
    for row in route_data:
        if not isinstance(row, dict):
            continue
        route = str(row.get("route") or "").strip()
        if not route:
            continue
        item = meta.setdefault(route, {
            "lanes": set(),
            "roles": set(),
            "minRequestIndex": 10**9,
            "proofRows": 0,
        })
        lane = semantic_lane(row.get("semanticType"))
        if lane:
            item["lanes"].add(lane)
        role = str(row.get("role") or "").strip().casefold()
        if role:
            item["roles"].add(role)
        try:
            item["minRequestIndex"] = min(item["minRequestIndex"], int(row.get("requestIndex") or 0))
        except (TypeError, ValueError):
            pass
        item["proofRows"] += 1
    return meta


def supported_lanes(model: dict[str, Any], route_data: list[dict[str, Any]]) -> set[str]:
    lanes = {
        semantic_lane(value)
        for value in model.get("supportedTypes") or []
        if semantic_lane(value)
    }
    if lanes:
        return lanes
    return {
        semantic_lane(row.get("semanticType"))
        for row in route_data
        if isinstance(row, dict) and semantic_lane(row.get("semanticType"))
    }


def route_score(route: str, meta: dict[str, Any]) -> int:
    score = 0
    if identity_bearing(route):
        score += 2400
    lanes = meta.get("lanes") if isinstance(meta.get("lanes"), set) else set()
    score += 900 * len(lanes)
    roles = meta.get("roles") if isinstance(meta.get("roles"), set) else set()
    score += max((ROLE_PRIORITY.get(role, 0) for role in roles), default=0)
    try:
        index = int(meta.get("minRequestIndex") or 0)
    except (TypeError, ValueError):
        index = 0
    # Prefer an entry request to a terminal player/source hop when both are proven.
    score += max(0, 320 - min(max(index, 0), 320))
    score += min(int(meta.get("proofRows") or 0), 20)
    return score


def cap_runtime_routes(
    routes: list[str],
    route_data: list[dict[str, Any]],
    model: dict[str, Any] | None = None,
) -> tuple[list[str], dict[str, Any]]:
    """Return <=3 executable routes while retaining semantic coverage when known."""
    current = unique(list(routes), 256)
    model = model if isinstance(model, dict) else {}
    meta = route_metadata(route_data)
    lanes = supported_lanes(model, route_data)

    if len(current) <= MAX_RUNTIME_ROUTE_PLANS:
        covered = set().union(*(meta.get(route, {}).get("lanes", set()) for route in current)) if current else set()
        return current, {
            "before": len(current),
            "after": len(current),
            "supportedLanes": sorted(lanes),
            "coveredLanes": sorted(covered),
            "capped": False,
        }

    ranked = sorted(
        current,
        key=lambda route: (route_score(route, meta.get(route, {})), -current.index(route)),
        reverse=True,
    )
    selected: list[str] = []
    uncovered = set(lanes)

    # Greedy semantic set-cover first.  One common route proven for movie/tv/anime
    # wins over three duplicates; otherwise choose the strongest per missing lane.
    while uncovered and len(selected) < MAX_RUNTIME_ROUTE_PLANS:
        choices: list[tuple[int, int, str]] = []
        for route in ranked:
            if route in selected:
                continue
            coverage = set(meta.get(route, {}).get("lanes", set()))
            new_coverage = coverage & uncovered
            if not new_coverage:
                continue
            choices.append((len(new_coverage), route_score(route, meta.get(route, {})), route))
        if not choices:
            break
        _coverage_count, _score, best = max(choices, key=lambda item: (item[0], item[1], -current.index(item[2])))
        selected.append(best)
        uncovered -= set(meta.get(best, {}).get("lanes", set()))

    # Historical baseline routes may predate routeData.  Keep only the strongest
    # identity-bearing fallbacks needed to reach the hard cap; never re-expand.
    if not selected:
        selected = [route for route in ranked if identity_bearing(route)][:MAX_RUNTIME_ROUTE_PLANS]
    if not selected:
        selected = ranked[:MAX_RUNTIME_ROUTE_PLANS]
    elif uncovered:
        for route in ranked:
            if len(selected) >= MAX_RUNTIME_ROUTE_PLANS:
                break
            if route in selected or not identity_bearing(route):
                continue
            selected.append(route)

    selected = selected[:MAX_RUNTIME_ROUTE_PLANS]
    covered = set().union(*(meta.get(route, {}).get("lanes", set()) for route in selected)) if selected else set()
    return selected, {
        "before": len(current),
        "after": len(selected),
        "supportedLanes": sorted(lanes),
        "coveredLanes": sorted(covered),
        "capped": len(selected) < len(current),
    }


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: object required")
    return value


def write(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def enforce_runtime_route_cap(
    report: dict[str, Any] | None = None,
    *,
    overrides_path: Path = OVERRIDES,
    knowledge_path: Path = KNOWLEDGE,
) -> dict[str, Any]:
    del report  # routeData is authoritative in static knowledge after apply_recovery().
    overrides = load(overrides_path)
    knowledge = load(knowledge_path)
    patches = overrides.get("provider_patches") if isinstance(overrides.get("provider_patches"), dict) else {}
    providers = knowledge.get("providers") if isinstance(knowledge.get("providers"), dict) else {}

    changed = 0
    capped = 0
    max_before = 0
    max_after = 0
    violations: list[str] = []

    for provider_id, static_row in providers.items():
        if not isinstance(static_row, dict):
            continue
        patch = patches.get(provider_id)
        if not isinstance(patch, dict):
            continue
        model = static_row.get("model") if isinstance(static_row.get("model"), dict) else {}
        route_data = [row for row in model.get("routeData") or [] if isinstance(row, dict)]
        before_routes = unique([
            *(model.get("routes") or []),
            *(patch.get("learned_routes") or []),
        ], 256)
        selected, audit = cap_runtime_routes(before_routes, route_data, model)
        max_before = max(max_before, len(before_routes))
        max_after = max(max_after, len(selected))
        if len(selected) > MAX_RUNTIME_ROUTE_PLANS:
            violations.append(f"{provider_id}:{len(selected)}")
            continue
        if selected != unique(model.get("routes") or [], 256) or selected != unique(patch.get("learned_routes") or [], 256):
            changed += 1
        if audit["capped"]:
            capped += 1
        model["routes"] = selected
        patch["learned_routes"] = selected
        proof = model.get("routeProof") if isinstance(model.get("routeProof"), dict) else {}
        proof.update({
            "runtimeRoutePlanCap": MAX_RUNTIME_ROUTE_PLANS,
            "runtimePlanRouteCountBeforeCap": audit["before"],
            "runtimePlanRouteCount": audit["after"],
            "runtimePlanSemanticLanes": audit["coveredLanes"],
            "evidenceRouteCount": len(route_data),
            "evidenceRoutesExecutableDirectly": False,
        })
        model["routeProof"] = proof
        patch["route_proof"] = copy.deepcopy(proof)
        static_row["model"] = model
        providers[provider_id] = static_row
        patches[provider_id] = patch

    if violations:
        raise RuntimeError("runtime route plan cap violated: " + ",".join(violations[:20]))

    overrides["provider_patches"] = patches
    knowledge["providers"] = providers
    write(overrides_path, overrides)
    write(knowledge_path, knowledge)
    return {
        "providerCount": len(providers),
        "changedProviders": changed,
        "cappedProviders": capped,
        "maxBefore": max_before,
        "maxAfter": max_after,
        "cap": MAX_RUNTIME_ROUTE_PLANS,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--overrides", type=Path, default=OVERRIDES)
    parser.add_argument("--knowledge", type=Path, default=KNOWLEDGE)
    args = parser.parse_args()
    summary = enforce_runtime_route_cap(
        overrides_path=args.overrides if args.overrides.is_absolute() else ROOT / args.overrides,
        knowledge_path=args.knowledge if args.knowledge.is_absolute() else ROOT / args.knowledge,
    )
    print(
        "RUNTIME_ROUTE_PLAN_CAP_V1_OK "
        f"providers={summary['providerCount']} changed={summary['changedProviders']} "
        f"capped={summary['cappedProviders']} max_before={summary['maxBefore']} "
        f"max_after={summary['maxAfter']} cap={summary['cap']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
