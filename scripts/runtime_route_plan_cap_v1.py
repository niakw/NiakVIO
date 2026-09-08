#!/usr/bin/env python3
"""Conservatively reduce duplicate Provider entry plans without truncating real graphs.

Three executable entry plans is the normal shape (one shared plan, movie/tv, or
movie/tv/anime), not an invariant.  A provider may legitimately require a
multi-hop graph such as search -> identity verification -> detail -> several
players/sources (including language variants).  Those downstream branches are
part of one resolver path and must never be dropped merely to satisfy a number.

This policy therefore compacts only when routeData proves that the active routes
are interchangeable top-level entry alternatives.  Complex, multi-hop, fan-out,
or insufficiently modelled providers are preserved and explicitly audited.
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
NORMAL_ENTRY_PLAN_TARGET = 3
# Compatibility alias for callers/tests created during the first cap iteration.
MAX_RUNTIME_ROUTE_PLANS = NORMAL_ENTRY_PLAN_TARGET
LANES = ("movie", "tv", "anime")
ENTRY_ROLES = {"search", "api", "detail", "catalog", "catalogue", "lookup"}
DOWNSTREAM_ROLES = {"episode", "episode-index", "player", "source", "embed", "resolver", "stream"}
ROLE_PRIORITY = {
    "search": 900,
    "api": 760,
    "detail": 700,
    "catalog": 690,
    "catalogue": 690,
    "lookup": 680,
    "episode": 360,
    "episode-index": 340,
    "player": 220,
    "source": 180,
    "embed": 170,
    "resolver": 160,
    "stream": 150,
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
            "maxRequestIndex": -1,
            "proofRows": 0,
            "fixtures": set(),
        })
        lane = semantic_lane(row.get("semanticType"))
        if lane:
            item["lanes"].add(lane)
        role = str(row.get("role") or "").strip().casefold()
        if role:
            item["roles"].add(role)
        try:
            index = int(row.get("requestIndex") or 0)
            item["minRequestIndex"] = min(item["minRequestIndex"], index)
            item["maxRequestIndex"] = max(item["maxRequestIndex"], index)
        except (TypeError, ValueError):
            pass
        fixture = str(row.get("fixture") or "").strip()
        if fixture:
            item["fixtures"].add(fixture)
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
    score += max(0, 320 - min(max(index, 0), 320))
    score += min(int(meta.get("proofRows") or 0), 20)
    return score


def _fixture_graphs(route_data: list[dict[str, Any]]) -> dict[tuple[str, str], list[dict[str, Any]]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in route_data:
        if not isinstance(row, dict):
            continue
        lane = semantic_lane(row.get("semanticType"))
        fixture = str(row.get("fixture") or "").strip()
        if lane and fixture:
            grouped[(lane, fixture)].append(row)
    for rows in grouped.values():
        rows.sort(key=lambda row: int(row.get("requestIndex") or 0))
    return grouped


def complex_multihop_reason(route_data: list[dict[str, Any]]) -> str:
    """Return a reason when proof shows a real chain/fan-out that must be preserved."""
    for rows in _fixture_graphs(route_data).values():
        unique_routes = unique([row.get("route") for row in rows], 256)
        roles = [str(row.get("role") or "").strip().casefold() for row in rows]
        has_entry = any(role in ENTRY_ROLES for role in roles)
        downstream_rows = [row for row in rows if str(row.get("role") or "").strip().casefold() in DOWNSTREAM_ROLES]
        downstream_routes = unique([row.get("route") for row in downstream_rows], 256)
        if has_entry and len(downstream_routes) >= 2:
            return "multi-hop-fanout"
        if len(unique_routes) >= 4 and has_entry and downstream_routes:
            return "multi-hop-chain"
        if "episode-index" in roles and any(role in {"player", "source", "embed", "resolver"} for role in roles):
            return "episodic-fanout"
        if len(set(roles) & (ENTRY_ROLES | DOWNSTREAM_ROLES)) >= 3 and len(unique_routes) >= 3:
            return "multi-stage-chain"
    return ""


def _safe_entry_only_projection(current: list[str], meta: dict[str, dict[str, Any]]) -> bool:
    """Only collapse when every active route is proven to be a top-level alternative."""
    if not current:
        return True
    for route in current:
        item = meta.get(route)
        if not isinstance(item, dict):
            return False
        roles = item.get("roles") if isinstance(item.get("roles"), set) else set()
        if not roles or roles & DOWNSTREAM_ROLES:
            return False
        if not roles <= ENTRY_ROLES:
            return False
    return True


def cap_runtime_routes(
    routes: list[str],
    route_data: list[dict[str, Any]],
    model: dict[str, Any] | None = None,
) -> tuple[list[str], dict[str, Any]]:
    """Optimize simple duplicate entry alternatives; never truncate complex graphs."""
    current = unique(list(routes), 256)
    model = model if isinstance(model, dict) else {}
    meta = route_metadata(route_data)
    lanes = supported_lanes(model, route_data)
    covered = set().union(*(meta.get(route, {}).get("lanes", set()) for route in current)) if current else set()

    audit: dict[str, Any] = {
        "before": len(current),
        "after": len(current),
        "supportedLanes": sorted(lanes),
        "coveredLanes": sorted(covered),
        "optimized": False,
        "capped": False,
        "normalEntryPlanTarget": NORMAL_ENTRY_PLAN_TARGET,
        "targetExceeded": len(current) > NORMAL_ENTRY_PLAN_TARGET,
        "exceptionReason": "",
    }
    if len(current) <= NORMAL_ENTRY_PLAN_TARGET:
        return current, audit

    graph_reason = complex_multihop_reason(route_data)
    if graph_reason:
        audit["exceptionReason"] = graph_reason
        return current, audit
    if not route_data:
        audit["exceptionReason"] = "insufficient-proof-to-collapse"
        return current, audit
    if not _safe_entry_only_projection(current, meta):
        audit["exceptionReason"] = "mixed-entry-and-downstream-routes"
        return current, audit

    ranked = sorted(
        current,
        key=lambda route: (route_score(route, meta.get(route, {})), -current.index(route)),
        reverse=True,
    )
    selected: list[str] = []
    uncovered = set(lanes)
    while uncovered and len(selected) < NORMAL_ENTRY_PLAN_TARGET:
        choices: list[tuple[int, int, str]] = []
        for route in ranked:
            if route in selected:
                continue
            fresh = set(meta.get(route, {}).get("lanes", set())) & uncovered
            if fresh:
                choices.append((len(fresh), route_score(route, meta.get(route, {})), route))
        if not choices:
            break
        _coverage, _score, best = max(choices, key=lambda item: (item[0], item[1], -current.index(item[2])))
        selected.append(best)
        uncovered -= set(meta.get(best, {}).get("lanes", set()))

    if uncovered:
        # Do not destroy a proven fourth entry merely because the common case is 3.
        audit["exceptionReason"] = "more-than-three-distinct-required-entry-plans"
        return current, audit
    if not selected:
        audit["exceptionReason"] = "no-safe-entry-selection"
        return current, audit

    selected = unique(selected, NORMAL_ENTRY_PLAN_TARGET)
    selected_covered = set().union(*(meta.get(route, {}).get("lanes", set()) for route in selected)) if selected else set()
    audit.update({
        "after": len(selected),
        "coveredLanes": sorted(selected_covered),
        "optimized": selected != current,
        "capped": selected != current,
        "targetExceeded": len(selected) > NORMAL_ENTRY_PLAN_TARGET,
    })
    return selected, audit


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
    del report
    overrides = load(overrides_path)
    knowledge = load(knowledge_path)
    patches = overrides.get("provider_patches") if isinstance(overrides.get("provider_patches"), dict) else {}
    providers = knowledge.get("providers") if isinstance(knowledge.get("providers"), dict) else {}

    changed = 0
    optimized = 0
    exceptions = 0
    max_before = 0
    max_after = 0

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
        if selected != unique(model.get("routes") or [], 256) or selected != unique(patch.get("learned_routes") or [], 256):
            changed += 1
        if audit["optimized"]:
            optimized += 1
        if audit["targetExceeded"] and audit["exceptionReason"]:
            exceptions += 1

        model["routes"] = selected
        patch["learned_routes"] = selected
        proof = model.get("routeProof") if isinstance(model.get("routeProof"), dict) else {}
        proof.pop("runtimeRoutePlanCap", None)
        proof.update({
            "normalRuntimeEntryPlanTarget": NORMAL_ENTRY_PLAN_TARGET,
            "runtimeEntryPlanOptimization": "compact-simple-alternatives-preserve-complex-graphs",
            "runtimePlanRouteCountBeforeOptimization": audit["before"],
            "runtimePlanRouteCount": audit["after"],
            "runtimePlanSemanticLanes": audit["coveredLanes"],
            "runtimePlanTargetExceeded": audit["targetExceeded"],
            "runtimePlanExceptionReason": audit["exceptionReason"],
            "runtimeFanoutPreserved": audit["exceptionReason"] in {"multi-hop-fanout", "multi-hop-chain", "episodic-fanout", "multi-stage-chain", "mixed-entry-and-downstream-routes"},
            "evidenceRouteCount": len(route_data),
            "evidenceRoutesAreNotPlanCount": True,
        })
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
        "optimizedProviders": optimized,
        "exceptionProviders": exceptions,
        "maxBefore": max_before,
        "maxAfter": max_after,
        "target": NORMAL_ENTRY_PLAN_TARGET,
        # compatibility fields for older log consumers
        "cappedProviders": optimized,
        "cap": NORMAL_ENTRY_PLAN_TARGET,
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
        "RUNTIME_ROUTE_PLAN_POLICY_V2_OK "
        f"providers={summary['providerCount']} changed={summary['changedProviders']} "
        f"optimized={summary['optimizedProviders']} exceptions={summary['exceptionProviders']} "
        f"max_before={summary['maxBefore']} max_after={summary['maxAfter']} target={summary['target']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
