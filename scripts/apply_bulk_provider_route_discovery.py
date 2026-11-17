#!/usr/bin/env python3
"""Merge sanitized bulk route-discovery shards into the next activation wave."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REQUEST = ROOT / ".github/provider-onboarding/batch.json"
DEFAULT_EVIDENCE = ROOT / "automation/provider-bulk-route-discovery-latest.json"
RESERVE_GLOB = "provider-intake-reserve-*.json"


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def norm(value: Any) -> str:
    return re.sub(r"[^a-z0-9._-]+", "-", str(value or "").strip().casefold()).strip("-")


def write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


LANES = ("movie", "tv", "anime")
TARGET_ACTIVE = 60
TARGET_LANE = 20


def defer_missing_probe_result(
    row: dict[str, Any], pid: str, active_ids: set[str]
) -> dict[str, Any] | None:
    if pid in active_ids:
        return None
    deferred = dict(row)
    deferred["routeDiscoveryLastReason"] = "probe_shard_missing_or_timeout"
    return deferred


ROUTE_DISCOVERY_REASON_STRENGTH = {
    "observed_identity_executable_routes": 30,
    "retained_identity_route_plan_host_matched": 20,
    "existing_identity_executable_route_plan": 10,
}
ROUTE_DISCOVERY_TRANSPORT_STRENGTH = {
    "residential-exit": 30,
    "github-hosted": 20,
    "retained-v3-rag": 10,
    "request-existing": 5,
}


def _normalized_routes(values: Any) -> list[str]:
    out: list[str] = []
    for value in values or []:
        route = str(value or "").strip()
        if route and route not in out:
            out.append(route)
    return out[:24]


def merge_route_discovery_evidence(
    row: dict[str, Any],
    result: dict[str, Any],
    patterns: list[str],
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    """Keep stronger same-plan discovery evidence while recording the latest replay.

    A request-existing result proves only that the route plan was already present;
    it must not erase an earlier causal residential observation of the exact same
    provider-owned routes. This preserves experience, not health: neither result
    grants playback proof or production activation.
    """
    current = {
        "transport": result.get("transport"),
        "reason": result.get("reason"),
        "routeCount": len(patterns),
    }
    previous = row.get("routeDiscoveryEvidence")
    if not isinstance(previous, dict):
        return current, None
    previous_routes = _normalized_routes(row.get("routes"))
    if previous_routes != _normalized_routes(patterns):
        return current, None
    previous_reason = str(previous.get("reason") or "")
    current_reason = str(current.get("reason") or "")
    previous_rank = (
        ROUTE_DISCOVERY_REASON_STRENGTH.get(previous_reason, 0),
        ROUTE_DISCOVERY_TRANSPORT_STRENGTH.get(str(previous.get("transport") or ""), 0),
    )
    current_rank = (
        ROUTE_DISCOVERY_REASON_STRENGTH.get(current_reason, 0),
        ROUTE_DISCOVERY_TRANSPORT_STRENGTH.get(str(current.get("transport") or ""), 0),
    )
    if previous_rank > current_rank:
        preserved = {
            "transport": previous.get("transport"),
            "reason": previous.get("reason"),
            "routeCount": int(previous.get("routeCount") or len(previous_routes)),
        }
        replay = {
            **current,
            "authorityPreserved": True,
            "preservedReason": "same_route_plan_stronger_prior_observation",
        }
        return preserved, replay
    return current, None


def current_active_ids() -> set[str]:
    ids: set[str] = set()
    for path in (ROOT / "manifest.json", ROOT / "vf" / "manifest.json"):
        payload = load(path)
        for row in payload.get("scrapers") or []:
            if not isinstance(row, dict) or row.get("enabled") is False:
                continue
            pid = norm(row.get("id"))
            if pid:
                ids.add(pid)
    return ids


def current_active_state() -> dict[str, dict[str, Any]]:
    state: dict[str, dict[str, Any]] = {}
    for scope, path in (("global", ROOT / "manifest.json"), ("france", ROOT / "vf/manifest.json")):
        manifest = load(path)
        active = [
            row for row in manifest.get("scrapers") or []
            if isinstance(row, dict) and row.get("enabled") is not False
        ]
        lanes = {lane: 0 for lane in LANES}
        for row in active:
            values = row.get("canonicalSupportedTypes") or row.get("supportedTypes") or []
            for lane in LANES:
                if lane in values:
                    lanes[lane] += 1
        state[scope] = {"active": len(active), "lanes": lanes}
    return state


def projects_to_vf(row: dict[str, Any]) -> bool:
    scope = str(row.get("scope") or "global").strip().casefold()
    if scope == "france":
        return True
    raw_vf = row.get("vf")
    if isinstance(raw_vf, bool):
        return raw_vf
    if str(raw_vf or "").strip().casefold() in {"1","true","yes","on","oui"}:
        return True
    languages = row.get("languages") or row.get("contentLanguage") or []
    return any(str(value or "").strip().casefold().startswith("fr") for value in languages)


def state_after_shared_global(current: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    next_state = {
        "active": int(current.get("active") or 0),
        "lanes": {lane: int((current.get("lanes") or {}).get(lane) or 0) for lane in LANES},
    }
    for row in rows:
        if not projects_to_vf(row):
            continue
        next_state["active"] += 1
        for lane in _types(row):
            next_state["lanes"][lane] += 1
    return next_state


def _types(row: dict[str, Any]) -> set[str]:
    return {
        str(value).strip().casefold()
        for value in (row.get("types") or row.get("supportedTypes") or [])
        if str(value).strip().casefold() in LANES
    }


def select_to_target(
    rows: list[dict[str, Any]],
    *,
    scope: str,
    current: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Choose at most the remaining slots to 60, covering 20/20/20 first."""
    capacity = max(0, TARGET_ACTIVE - int(current.get("active") or 0))
    if capacity <= 0:
        return [], list(rows)
    lane_counts = {
        lane: int((current.get("lanes") or {}).get(lane) or 0)
        for lane in LANES
    }
    pool = list(rows)
    selected: list[dict[str, Any]] = []
    while pool and len(selected) < capacity:
        def key(row: dict[str, Any]) -> tuple[Any, ...]:
            types = _types(row)
            deficits = {
                lane: max(0, TARGET_LANE - lane_counts[lane])
                for lane in LANES
            }
            deficit_gain = sum(1 for lane in types if deficits[lane] > 0)
            deficit_weight = sum(deficits[lane] for lane in types)
            score = int(row.get("inventory_score") or 0)
            rank = int(row.get("inventory_rank") or 10**9)
            return (-deficit_gain, -deficit_weight, -score, rank, norm(row.get("id")))
        pool.sort(key=key)
        chosen = pool.pop(0)
        selected.append(chosen)
        for lane in _types(chosen):
            lane_counts[lane] += 1
    return selected, pool


def source_rows(request: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    seen: set[str] = set()

    def add(values: Any) -> None:
        for row in values or []:
            if not isinstance(row, dict):
                continue
            pid = norm(row.get("id") or row.get("provider"))
            if not pid or pid in seen:
                continue
            seen.add(pid)
            out.append(dict(row))

    for section in ("providers", "deferredProviders"):
        add(request.get(section))
    for path in sorted((ROOT / "automation").glob(RESERVE_GLOB)):
        try:
            reserve = load(path)
        except Exception:
            continue
        if isinstance(reserve, dict):
            add(reserve.get("providers"))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("shards", nargs="+", type=Path)
    ap.add_argument("--request", type=Path, default=DEFAULT_REQUEST)
    ap.add_argument("--evidence", type=Path, default=DEFAULT_EVIDENCE)
    ap.add_argument("--output-request", type=Path, default=DEFAULT_REQUEST)
    ap.add_argument("--expected-shards", type=int, default=8)
    args = ap.parse_args()

    request = load(args.request)
    if not isinstance(request, dict):
        raise SystemExit("bulk route discovery request must be an object")
    version = request.get("requestVersion")
    rows = source_rows(request)
    by_id = {norm(row.get("id") or row.get("provider")): row for row in rows}
    active_ids = current_active_ids()

    merged: dict[str, dict[str, Any]] = {}
    transports: set[str] = set()
    for path in args.shards:
        payload = load(path)
        if payload.get("requestVersion") != version:
            raise SystemExit(f"route discovery shard requestVersion mismatch: {path}")
        transports.add(str(payload.get("transport") or "unknown"))
        for result in payload.get("providers") or []:
            if not isinstance(result, dict):
                continue
            pid = norm(result.get("provider"))
            if not pid or pid not in by_id:
                continue
            if pid in merged:
                raise SystemExit(f"duplicate route-discovery provider result: {pid}")
            merged[pid] = result

    qualified: list[dict[str, Any]] = []
    deferred: list[dict[str, Any]] = []
    evidence_rows: list[dict[str, Any]] = []
    for row in rows:
        pid = norm(row.get("id") or row.get("provider"))
        result = merged.get(pid)
        if result is None:
            # Active rows are intentionally omitted by the probe. Missing inactive
            # rows, however, may belong to a shard that timed out/cancelled; keep
            # them in the next wave instead of silently dropping the candidate.
            deferred_row = defer_missing_probe_result(row, pid, active_ids)
            if deferred_row is not None:
                deferred.append(deferred_row)
            continue
        patterns = [
            str(value).strip()
            for value in result.get("routePatterns") or []
            if str(value).strip()
        ]
        patterns = list(dict.fromkeys(patterns))[:24]
        evidence_rows.append(result)
        if result.get("qualified") is True and patterns:
            updated = dict(row)
            updated["routes"] = patterns
            evidence, replay = merge_route_discovery_evidence(updated, result, patterns)
            updated["routeDiscoveryEvidence"] = evidence
            if replay is not None:
                updated["routeDiscoveryReplay"] = replay
            else:
                updated.pop("routeDiscoveryReplay", None)
            qualified.append(updated)
        else:
            deferred_row = dict(row)
            deferred_row["routeDiscoveryLastReason"] = str(result.get("reason") or "unqualified")
            deferred.append(deferred_row)

    active_state = current_active_state()
    qualified_global = [row for row in qualified if str(row.get("scope") or "global").casefold() == "global"]
    qualified_france = [row for row in qualified if str(row.get("scope") or "global").casefold() == "france"]
    selected_global, standby_global = select_to_target(
        qualified_global, scope="global", current=active_state["global"]
    )
    france_after_shared_global = state_after_shared_global(active_state["france"], selected_global)
    selected_france, standby_france = select_to_target(
        qualified_france, scope="france", current=france_after_shared_global
    )
    selected = selected_global + selected_france
    standby = standby_global + standby_france
    for row in standby:
        held = dict(row)
        held["routeDiscoveryLastReason"] = "qualified_standby_target_60"
        deferred.append(held)

    global_add = len(selected_global)
    shared_global_vf = [row for row in selected_global if projects_to_vf(row)]
    france_only_add = len(selected_france)
    france_add = len(shared_global_vf) + france_only_add
    current_global = int(active_state["global"]["active"])
    current_france = int(active_state["france"]["active"])

    evidence = {
        "schemaVersion": 1,
        "requestVersion": version,
        "source": request.get("source"),
        "transportProfiles": sorted(transports),
        "shardArtifactCount": len(args.shards),
        "expectedShardCount": int(args.expected_shards),
        "completeShardSet": len(args.shards) == int(args.expected_shards),
        "candidateCount": len(evidence_rows),
        "qualifiedCount": len(qualified),
        "selectedCount": len(selected),
        "standbyQualifiedCount": len(standby),
        "deferredCount": len(deferred),
        "qualifiedScopes": {
            "observedGlobal": len(qualified_global),
            "observedFrance": len(qualified_france),
            "selectedGlobal": global_add,
            "selectedGlobalSharedToFrance": len(shared_global_vf),
            "selectedFranceOnly": france_only_add,
            "selectedFrance": france_add,
        },
        "currentActiveBeforeWave": {
            "global": current_global,
            "france": current_france,
            "globalLanes": active_state["global"]["lanes"],
            "franceLanes": active_state["france"]["lanes"],
        },
        "providers": evidence_rows,
    }
    write(args.evidence, evidence)

    if not selected:
        print(
            f"PROVIDER_BULK_ROUTE_DISCOVERY_MERGE selected=0 qualified={len(qualified)} deferred={len(deferred)} "
            f"requestVersion={version}; batch_not_changed=true"
        )
        return 0

    next_request = dict(request)
    next_request["requestVersion"] = int(version or 0) + 1
    next_request["providers"] = selected
    next_request["deferredProviders"] = deferred
    # targetActive is a publication ceiling, not the expected cardinality of
    # this micro-wave. Keep the product target stable at exact 60/60 so a
    # shared Global->VF addition cannot consume the temporary France ceiling
    # before France-only candidates in the same batch are evaluated.
    next_request["targetActive"] = {
        "global": TARGET_ACTIVE,
        "france": TARGET_ACTIVE,
    }
    next_request["routeDiscoveryWave"] = {
        "sourceRequestVersion": version,
        "qualified": len(qualified),
        "selected": len(selected),
        "standbyQualified": len(standby),
        "deferred": len(deferred),
        "transports": sorted(transports),
        "shardArtifactCount": len(args.shards),
        "expectedShardCount": int(args.expected_shards),
        "completeShardSet": len(args.shards) == int(args.expected_shards),
        "activationRequiresExecutablePlan": True,
    }
    write(args.output_request, next_request)
    print(
        f"PROVIDER_BULK_ROUTE_DISCOVERY_MERGE qualified={len(qualified)} selected={len(selected)} deferred={len(deferred)} "
        f"global_target={next_request['targetActive']['global']} "
        f"france_target={next_request['targetActive']['france']} "
        f"next_request_version={next_request['requestVersion']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
