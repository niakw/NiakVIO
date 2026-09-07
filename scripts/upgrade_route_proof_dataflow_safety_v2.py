#!/usr/bin/env python3
"""Harden proof-v5 against lossy dynamic-value generalization.

Applied after the v1 request-spec/recovery migrations in a reconstruction workspace.
This migration is intentionally generic: arbitrary headers are never rewritten from
fixture substrings, blank signed/identity query parameters are not executable routes,
and a weaker observational route subset cannot replace a richer already-published
runtime plan.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROOF = ROOT / "scripts" / "provider_route_proof.py"
RECOVERY = ROOT / "scripts" / "recover_provider_routes_from_upstreams.py"
MARKER = "ROUTE_PROOF_DATAFLOW_SAFETY_V2"


def once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise AssertionError(f"{label}: expected one anchor, got {count}")
    return text.replace(old, new, 1)


def patch_proof() -> bool:
    text = PROOF.read_text(encoding="utf-8")
    if MARKER in text:
        return False

    old = '''    for key, raw in raw_headers.items():
        value = str(raw or "")
        if value == sensitive_marker:
            residue.append({"location": f"header:{key}", "value": sensitive_marker})
            continue
        replaced = value
        for body_key, raw_fixture in (
            ("tmdbId", fixture.get("tmdbId")),
            ("query", fixture.get("title")),
            ("season", fixture.get("season")),
            ("episode", fixture.get("episode")),
            ("year", fixture.get("year")),
        ):
            token = str(raw_fixture or "")
            if token and token in replaced:
                replaced = replaced.replace(token, "{" + body_key + "}")
        for provider_value in provider_values:
            if provider_value and provider_value in replaced:
                replaced = replaced.replace(provider_value, "{id}")
        if any(token and str(token) in replaced for token in fixture_tokens):
            residue.append({"location": f"header:{key}", "value": value[:160]})
            continue
        headers[str(key)] = replaced
'''
    new = '''    # ROUTE_PROOF_DATAFLOW_SAFETY_V2
    # Headers are not semantic identity fields. In particular a fixture season
    # such as 3 must never rewrite a literal User-Agent like NiakVIO/3.
    # Preserve known static request headers literally. For arbitrary headers,
    # fail closed when a meaningful fixture/provider token is embedded rather
    # than freezing a fixture-specific value into executable DATA.
    static_header_keys = {"accept", "accept-language", "user-agent", "content-type"}
    header_dynamic_tokens = unique([
        fixture.get("tmdbId"), fixture.get("title"), fixture.get("year"),
        *provider_values,
    ], 32)
    header_dynamic_tokens = [str(token) for token in header_dynamic_tokens if len(str(token)) >= 4]
    for key, raw in raw_headers.items():
        value = str(raw or "")
        key_l = canonical(key)
        if value == sensitive_marker:
            residue.append({"location": f"header:{key}", "value": sensitive_marker})
            continue
        if key_l not in static_header_keys and any(token in value for token in header_dynamic_tokens):
            residue.append({"location": f"header:{key}", "value": value[:160]})
            continue
        headers[str(key)] = value
'''
    text = once(text, old, new, "request-header-semantic-safety")
    PROOF.write_text(text, encoding="utf-8")
    return True


def patch_recovery() -> bool:
    text = RECOVERY.read_text(encoding="utf-8")
    if MARKER in text:
        return False

    old = '''def generic_execution_route(record: dict[str, Any]) -> bool:
    """Whether routes[] may replay this call without losing HTTP semantics."""
    spec = request_spec(record) or {"method": str(record.get("method") or "GET").upper()}
    if str(spec.get("method") or "GET").upper() != "GET":
        return False
    if spec.get("body"):
        return False
    headers = spec.get("headers") if isinstance(spec.get("headers"), dict) else {}
    nontrivial = {
        str(key).casefold() for key in headers
        if str(key).casefold() not in {"accept", "accept-language", "user-agent"}
    }
    return not nontrivial
'''
    new = '''# ROUTE_PROOF_DATAFLOW_SAFETY_V2
_BLANK_DYNAMIC_QUERY_KEYS = {
    "id", "_id", "media_id", "post_id", "content_id", "movie_id", "series_id", "show_id", "slug",
    "k", "key", "token", "access_token", "auth", "signature", "sig", "hash", "nonce", "session", "session_id",
    "season", "season_number", "seasonid", "season_id", "episode", "episode_number", "episodeid", "episode_id",
}


def generic_execution_route(record: dict[str, Any]) -> bool:
    """Whether routes[] may replay this call without losing HTTP/dataflow semantics."""
    spec = request_spec(record) or {"method": str(record.get("method") or "GET").upper()}
    if str(spec.get("method") or "GET").upper() != "GET":
        return False
    if spec.get("body"):
        return False
    headers = spec.get("headers") if isinstance(spec.get("headers"), dict) else {}
    nontrivial = {
        str(key).casefold() for key in headers
        if str(key).casefold() not in {"accept", "accept-language", "user-agent"}
    }
    if nontrivial:
        return False
    route = str(record.get("route") or "").strip()
    try:
        query = urllib.parse.parse_qsl(urllib.parse.urlsplit(route).query, keep_blank_values=True)
    except ValueError:
        return False
    if any(str(key).casefold() in _BLANK_DYNAMIC_QUERY_KEYS and value == "" for key, value in query):
        return False
    return True


def _identity_bearing_runtime_route(value: object) -> bool:
    route = str(value or "").strip().casefold()
    if not route:
        return False
    if any(token in route for token in ("{query}", "{title}", "{slug}", "{id}", "{tmdbid}", "{tmdb_id}")):
        return True
    path = urllib.parse.urlsplit(route).path
    return bool(path and (
        path.rstrip("/").endswith("/player")
        or "/search" in path
        or "/recherche" in path
        or "/title/" in path
        or "/movie/" in path
        or "/series/" in path
        or "/tv/" in path
    ))


def select_runtime_routes(
    existing_routes: list[str],
    candidate_routes: list[str],
    execution_routes: list[str],
) -> tuple[list[str], bool]:
    """Do not demote a richer published runtime plan to weak observations."""
    execution = unique(execution_routes, 192)
    if any(_identity_bearing_runtime_route(route) for route in execution):
        return execution, False
    for baseline in (existing_routes, candidate_routes):
        current = unique(baseline, 192)
        if any(_identity_bearing_runtime_route(route) for route in current):
            return current, True
    return execution, False
'''
    text = once(text, old, new, "generic-execution-dataflow-safety")

    old_apply = '''        proven_routes = unique(recovered.get("routes") or [], 192)
        execution_routes = unique(recovered.get("executionRoutes") or [], 192)
        route_data = copy.deepcopy(recovered.get("routeData") or [])
        recipe = recovered.get("apiRecipe") if isinstance(recovered.get("apiRecipe"), dict) else None
        patch["learned_routes"] = execution_routes
        model["routes"] = execution_routes
'''
    new_apply = '''        proven_routes = unique(recovered.get("routes") or [], 192)
        execution_routes = unique(recovered.get("executionRoutes") or [], 192)
        route_data = copy.deepcopy(recovered.get("routeData") or [])
        recipe = recovered.get("apiRecipe") if isinstance(recovered.get("apiRecipe"), dict) else None
        existing_routes = unique(patch.get("learned_routes") or [], 192)
        candidate_routes = unique(patch.get("candidate_learned_routes") or [], 192)
        runtime_routes, preserved_baseline_plan = select_runtime_routes(
            existing_routes, candidate_routes, execution_routes
        )
        patch["learned_routes"] = runtime_routes
        model["routes"] = runtime_routes
'''
    text = once(text, old_apply, new_apply, "preserve-richer-runtime-plan")
    text = once(
        text,
        '            "genericExecutionRouteCount": len(execution_routes),',
        '            "genericExecutionRouteCount": len(execution_routes),\n            "runtimePlanPreserved": preserved_baseline_plan,\n            "runtimePlanRouteCount": len(runtime_routes),',
        "record-runtime-plan-preservation",
    )
    RECOVERY.write_text(text, encoding="utf-8")
    return True


def validate() -> None:
    proof = PROOF.read_text(encoding="utf-8")
    recovery = RECOVERY.read_text(encoding="utf-8")
    for needle in (
        MARKER,
        "static_header_keys",
        "header_dynamic_tokens",
        "headers[str(key)] = value",
    ):
        if needle not in proof:
            raise AssertionError(f"route-proof safety missing in proof: {needle}")
    for needle in (
        MARKER,
        "_BLANK_DYNAMIC_QUERY_KEYS",
        "def select_runtime_routes(",
        "runtimePlanPreserved",
        "patch[\"learned_routes\"] = runtime_routes",
    ):
        if needle not in recovery:
            raise AssertionError(f"route-proof safety missing in recovery: {needle}")


def main() -> int:
    changed = patch_proof()
    changed = patch_recovery() or changed
    validate()
    print(f"ROUTE_PROOF_DATAFLOW_SAFETY_V2_OK changed={str(changed).lower()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
