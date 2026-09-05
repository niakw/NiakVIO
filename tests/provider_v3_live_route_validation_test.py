#!/usr/bin/env python3
from __future__ import annotations

import copy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_provider_v3_routes_live import (  # noqa: E402
    recipe_is_live,
    route_matches_url,
    validate_and_promote,
)


assert route_matches_url(
    "/api/search?q={query}",
    "https://example.test/api/search?q=Interstellar",
)
assert route_matches_url(
    "/stream/{id}/episode?season={season}&episode={episode}",
    "https://example.test/stream/abc123/episode?episode=1&season=2",
)
assert not route_matches_url(
    "/stream/{id}/episode?season={season}&episode={episode}",
    "https://example.test/stream/abc123/episode?season=2",
)
assert not route_matches_url(
    "/api/search?q={query}",
    "https://example.test/api/other?q=Interstellar",
)
assert recipe_is_live(
    {"searchRoute": "/api/search?q={query}"},
    {"/api/search?q={query}"},
)
assert not recipe_is_live(
    {"searchRoute": "/api/search?q={query}", "sourceRoute": "/source/{id}"},
    {"/api/search?q={query}"},
)

providers = {}
patches = {}
for index in range(96):
    provider_id = f"fixture-{index:02d}"
    providers[provider_id] = {
        "model": {
            "strategy": "html_scraper",
            "routes": [],
            "routeData": [],
        },
        "knowledge": {"recognizedContract": {}},
    }
    patches[provider_id] = {"learned_routes": []}

providers["fixture-00"]["model"].update({
    "routes": ["/api/search?q={query}", "/source/{id}"],
    "routeData": [
        {
            "route": "/api/search?q={query}",
            "role": "search",
            "method": "POST",
            "executedEvidence": True,
            "httpUsed": True,
            "confidence": 0.99,
        },
        {
            "route": "/source/{id}",
            "role": "source",
            "method": "GET",
            "executedEvidence": True,
            "httpUsed": True,
            "confidence": 0.99,
        },
    ],
    "apiRecipe": {
        "searchRoute": "/api/search?q={query}",
        "sourceRoute": "/source/{id}",
    },
})
patches["fixture-00"] = {
    "learned_routes": ["/api/search?q={query}", "/source/{id}"],
    "api_recipe": copy.deepcopy(providers["fixture-00"]["model"]["apiRecipe"]),
}

providers["fixture-01"]["model"].update({
    "routes": ["/blocked/{id}"],
    "routeData": [{
        "route": "/blocked/{id}",
        "role": "detail",
        "method": "GET",
        "executedEvidence": True,
        "httpUsed": True,
        "confidence": 0.99,
    }],
})
patches["fixture-01"] = {"learned_routes": ["/blocked/{id}"]}

providers["fixture-02"]["model"].update({
    "routes": ["/static-only/{id}"],
    "routeData": [{
        "route": "/static-only/{id}",
        "role": "detail",
        "method": "GET",
        "executedEvidence": True,
        "httpUsed": True,
        "confidence": 0.99,
    }],
})
patches["fixture-02"] = {"learned_routes": ["/static-only/{id}"]}

knowledge = {"providers": providers}
overrides = {"provider_patches": patches}
tasks = [
    {
        "provider_id": "fixture-00",
        "provider_name": "Fixture 00",
        "semantic_type": "movie",
        "fixture_title": "Interstellar",
        "status": "no_streams",
        "fetches": [{
            "url": "https://example.test/api/search?q=Interstellar",
            "final_url": "https://example.test/api/search?q=Interstellar",
            "method": "POST",
            "status": 200,
            "content_type": "application/json",
            "header_names": ["accept", "referer"],
            "body_kind": "json",
            "body_fields": ["q"],
            "duration_ms": 12,
        }],
    },
    {
        "provider_id": "fixture-01",
        "provider_name": "Fixture 01",
        "semantic_type": "movie",
        "fixture_title": "Interstellar",
        "status": "no_streams",
        "fetches": [{
            "url": "https://blocked.test/blocked/abc",
            "final_url": "https://blocked.test/blocked/abc",
            "method": "GET",
            "status": 403,
            "content_type": "text/html",
            "header_names": ["accept"],
            "body_kind": "none",
            "body_fields": [],
            "duration_ms": 8,
        }],
    },
]

knowledge, overrides, report = validate_and_promote(knowledge, overrides, tasks)

live = knowledge["providers"]["fixture-00"]["model"]
assert live["routes"] == ["/api/search?q={query}"], live
assert len(live["routeData"]) == 1, live
assert live["routeData"][0]["validationState"] == "live-validated", live
assert live["routeData"][0]["httpUsed"] is True, live
assert live["routeData"][0]["observedContentType"] == "application/json", live
assert live["routeData"][0]["observedHeaderNames"] == ["accept", "referer"], live
assert live["routeData"][0]["observedBodyFields"] == ["q"], live
assert len(live["candidateRouteData"]) == 2, live
assert next(row for row in live["candidateRouteData"] if row["route"] == "/source/{id}")["validationState"] == "candidate-not-executed"
assert "apiRecipe" not in live, live
assert live["candidateApiRecipe"]["sourceRoute"] == "/source/{id}", live
assert overrides["provider_patches"]["fixture-00"]["learned_routes"] == ["/api/search?q={query}"], overrides
assert "api_recipe" not in overrides["provider_patches"]["fixture-00"], overrides

blocked = knowledge["providers"]["fixture-01"]["model"]
assert blocked["routes"] == [], blocked
assert blocked["routeData"] == [], blocked
assert blocked["candidateRouteData"][0]["validationState"] == "blocked-live", blocked
assert blocked["candidateRouteData"][0]["httpUsed"] is False, blocked

static_only = knowledge["providers"]["fixture-02"]["model"]
assert static_only["routes"] == [], static_only
assert static_only["routeData"] == [], static_only
candidate = static_only["candidateRouteData"][0]
assert candidate["staticCallEvidence"] is True, candidate
assert candidate["validationState"] == "candidate-not-executed", candidate
assert candidate["executedEvidence"] is False, candidate
assert candidate["httpUsed"] is False, candidate

assert report["candidateRouteCount"] == 4, report
assert report["attemptedRouteCount"] == 2, report
assert report["liveValidatedRouteCount"] == 1, report
assert report["blockedRouteCount"] == 1, report
assert report["unexecutedCandidateRouteCount"] == 2, report
assert report["providersWithLiveValidatedRouteCount"] == 1, report

print(
    "Provider v3 live route validation tests passed: static evidence stays candidate, "
    "403 stays blocked, and only successful runtime HTTP traversal is promoted."
)
