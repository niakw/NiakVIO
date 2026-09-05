#!/usr/bin/env python3
from __future__ import annotations

import copy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from upgrade_provider_v3_finalization_v1 import patch_finalizer  # noqa: E402
from upgrade_provider_v3_redirect_route_match_v1 import patch as patch_redirect  # noqa: E402
from upgrade_provider_v3_safe_runtime_route_promotion_v2 import patch as patch_safe_runtime  # noqa: E402

patch_finalizer()
patch_redirect()
patch_safe_runtime()

from validate_provider_v3_routes_sequential import evaluate_provider, finalize_provider, should_pass  # noqa: E402

COMMON = {
    "method": "GET",
    "status": 200,
    "content_type": "text/html; charset=UTF-8",
    "header_names": ["accept", "user-agent"],
    "body_kind": "none",
    "body_fields": [],
}

model = {
    "canonicalSupportedTypes": ["anime", "movie", "tv"],
    "knownSite": "https://query.test",
    # Deliberately stale/unexecuted legacy DATA. The real typed contract is only
    # discovered from runtime requests, matching the Animesalt failure mode.
    "routeData": [
        {"route": "/legacy/{slug}", "role": "detail"},
        {"route": "/player/index.php?data=", "role": "player"},
    ],
    "routes": ["/legacy/{slug}", "/player/index.php?data="],
    "origins": ["https://query.test"],
    "observedUrls": [],
}

def task(media_type: str, tmdb_id: str, url: str, *, season: int | None = None, episode: int | None = None) -> dict:
    fixture = {"tmdbId": tmdb_id, "mediaType": media_type, "title": media_type.title()}
    if season is not None:
        fixture["season"] = season
    if episode is not None:
        fixture["episode"] = episode
    return {
        "semantic_type": media_type,
        "fixture_slug": f"fixture-{media_type}",
        "fixture": fixture,
        "status": "no_streams",
        "fetches": [{**COMMON, "url": url, "final_url": url}],
    }

tasks = [
    task("movie", "157336", "https://query.test/?tmdbId=157336&type=movie"),
    task("tv", "1396", "https://query.test/?tmdbId=1396&type=tv&season=1&episode=1", season=1, episode=1),
    task("anime", "94664", "https://query.test/?tmdbId=94664&type=tv&season=1&episode=1", season=1, episode=1),
]

evaluation = evaluate_provider("query-provider", copy.deepcopy(model), tasks, 0.75)
assert should_pass(evaluation), evaluation
assert set(evaluation["validatedTypes"]) == {"anime", "movie", "tv"}, evaluation
assert evaluation["missingTypes"] == [], evaluation
safe_routes = {
    row["route"] for row in evaluation["candidateRouteData"]
    if row.get("liveDerived") and row.get("validationState") == "live-validated"
}
assert "/?tmdbId={tmdbId}&type=movie" in safe_routes, safe_routes
assert "/?tmdbId={tmdbId}&type=tv&season={season}&episode={episode}" in safe_routes, safe_routes

knowledge = {
    "providers": {
        "query-provider": {
            "model": copy.deepcopy(model),
            "knowledge": {"recognizedContract": {}},
        }
    }
}
overrides = {"provider_patches": {"query-provider": {}}}
finalize_provider(
    "query-provider",
    {"provider_id": "query-provider"},
    knowledge,
    overrides,
    evaluation,
    "declared-types-qualified",
    [],
)
final_model = knowledge["providers"]["query-provider"]["model"]
final_routes = set(final_model["routes"])
assert "/?tmdbId={tmdbId}&type=movie" in final_routes, final_routes
assert "/?tmdbId={tmdbId}&type=tv&season={season}&episode={episode}" in final_routes, final_routes
assert "/legacy/{slug}" not in final_routes, final_routes
assert "/player/index.php?data=" not in final_routes, final_routes
assert all("{" in route and "}" in route for route in final_routes), final_routes
assert final_model["routeRecognition"]["safeRuntimeDerivedRoutesPromoted"] == 2, final_model["routeRecognition"]

# A literal runtime/session route must remain evidence-only even with HTTP 200.
volatile_model = {
    "canonicalSupportedTypes": ["movie"],
    "knownSite": "https://query.test",
    "routeData": [{"route": "/movie/{tmdbId}", "types": ["movie"]}],
    "routes": ["/movie/{tmdbId}"],
}
volatile_task = task("movie", "157336", "https://query.test/movie/157336")
volatile_task["fetches"].append({
    **COMMON,
    "url": "https://query.test/gateway/session-837492",
    "final_url": "https://query.test/gateway/session-837492",
})
volatile_eval = evaluate_provider("volatile-provider", copy.deepcopy(volatile_model), [volatile_task], 0.75)
volatile_knowledge = {"providers": {"volatile-provider": {"model": copy.deepcopy(volatile_model), "knowledge": {"recognizedContract": {}}}}}
volatile_overrides = {"provider_patches": {"volatile-provider": {}}}
finalize_provider("volatile-provider", {"provider_id": "volatile-provider"}, volatile_knowledge, volatile_overrides, volatile_eval, "declared-types-qualified", [])
volatile_routes = set(volatile_knowledge["providers"]["volatile-provider"]["model"]["routes"])
assert not any("gateway/session-" in route for route in volatile_routes), volatile_routes

print(
    "PROVIDER_V3_SAFE_RUNTIME_ROUTE_PROMOTION_TEST_OK "
    "typed_query_promoted=true volatile_session_rejected=true"
)
