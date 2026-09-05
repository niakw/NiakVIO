#!/usr/bin/env python3
from __future__ import annotations

import copy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_provider_v3_routes_sequential import evaluate_provider, finalize_provider, should_pass  # noqa: E402

COMMON = {
    "method": "GET",
    "content_type": "application/json",
    "header_names": ["accept"],
    "body_kind": "none",
    "body_fields": [],
}


def fetch(url: str, status: int) -> dict[str, object]:
    return {**COMMON, "url": url, "final_url": url, "status": status}


base_model = {
    "canonicalSupportedTypes": ["movie", "tv"],
    "knownSite": "https://plan.test",
    "officialApi": "https://api.plan.test/v1",
    "fixedApi": "https://api.plan.test/v1",
    "apiRecipe": {
        "base": "https://api.plan.test/v1",
        "searchRoute": "/search/{query}",
        "movieRoute": "/movie/{tmdbId}",
        "episodeRoute": "/tv/{tmdbId}?season={season}&episode={episode}",
        # Optional fallback/control branch: absence of a live call must not delete
        # the whole recipe after movie+tv have been proven.
        "statusUrl": "https://plan.test/status",
    },
    "routes": [
        "/search/{query}",
        "/fallback/{tmdbId}",
        "/movie/{tmdbId}",
        "/tv/{tmdbId}?season={season}&episode={episode}",
        "/unused/{tmdbId}",
    ],
    "routeData": [
        {"route": "/search/{query}", "role": "search"},
        {"route": "/fallback/{tmdbId}", "role": "detail"},
        {"route": "/movie/{tmdbId}", "role": "detail", "types": ["movie"]},
        {"route": "/tv/{tmdbId}?season={season}&episode={episode}", "role": "detail", "types": ["tv"]},
        {"route": "/unused/{tmdbId}", "role": "detail"},
    ],
}

movie = {
    "semantic_type": "movie",
    "fixture_slug": "movie",
    "fixture": {"tmdbId": "10", "mediaType": "movie", "title": "Movie"},
    "status": "playable_verified",
    "fetches": [
        fetch("https://api.plan.test/v1/search/Movie", 200),
        fetch("https://api.plan.test/v1/fallback/10", 404),
        fetch("https://api.plan.test/v1/movie/10", 200),
    ],
}
tv = {
    "semantic_type": "tv",
    "fixture_slug": "tv",
    "fixture": {"tmdbId": "20", "mediaType": "tv", "title": "Series", "season": 1, "episode": 1},
    "status": "playable_verified",
    "fetches": [
        fetch("https://api.plan.test/v1/search/Series", 200),
        fetch("https://api.plan.test/v1/fallback/20", 404),
        fetch("https://api.plan.test/v1/tv/20?season=1&episode=1", 200),
    ],
}

evaluation = evaluate_provider("plan-provider", copy.deepcopy(base_model), [movie, tv], 0.75)
assert should_pass(evaluation), evaluation
assert evaluation["validatedTypes"] == ["movie", "tv"], evaluation

knowledge = {
    "providers": {
        "plan-provider": {
            "model": copy.deepcopy(base_model),
            "knowledge": {"recognizedContract": {}},
        }
    }
}
overrides = {
    "provider_patches": {
        "plan-provider": {
            "learned_routes": list(base_model["routes"]),
            "api_recipe": copy.deepcopy(base_model["apiRecipe"]),
        }
    }
}
finalize_provider(
    "plan-provider",
    {"provider_id": "plan-provider"},
    knowledge,
    overrides,
    evaluation,
    "declared-types-qualified",
    [],
)
final_model = knowledge["providers"]["plan-provider"]["model"]
final_routes = set(final_model["routes"])
assert "/search/{query}" in final_routes, final_routes
assert "/fallback/{tmdbId}" in final_routes, final_routes
assert "/movie/{tmdbId}" in final_routes, final_routes
assert "/tv/{tmdbId}?season={season}&episode={episode}" in final_routes, final_routes
assert "/unused/{tmdbId}" not in final_routes, final_routes
fallback = next(row for row in final_model["routeData"] if row["route"] == "/fallback/{tmdbId}")
assert fallback["validationState"] == "failed-live", fallback
assert fallback.get("attemptEvidence"), fallback
assert final_model["apiRecipe"]["statusUrl"] == "https://plan.test/status", final_model["apiRecipe"]
patch = overrides["provider_patches"]["plan-provider"]
assert "/fallback/{tmdbId}" in patch["learned_routes"], patch
assert "/unused/{tmdbId}" not in patch["learned_routes"], patch
assert patch["api_recipe"]["statusUrl"] == "https://plan.test/status", patch
assert final_model["routeRecognition"]["executionPlanRetainsAttemptedNon2xx"] is True
assert final_model["routeRecognition"]["blockedPlanPreserved"] is False

# A runner-level block is not evidence that downstream typed routes are invalid.
# Preserve the complete current candidate plan so another network/client can use it.
blocked_model = copy.deepcopy(base_model)
blocked_evaluation = evaluate_provider(
    "blocked-provider",
    blocked_model,
    [{
        "semantic_type": "movie",
        "fixture_slug": "movie",
        "fixture": {"tmdbId": "10", "mediaType": "movie", "title": "Movie"},
        "status": "no_streams",
        "fetches": [fetch("https://api.plan.test/v1/search/Movie", 403)],
    }],
    0.75,
)
assert blocked_evaluation["providerBlockedOnly"] is True, blocked_evaluation
blocked_knowledge = {
    "providers": {
        "blocked-provider": {
            "model": copy.deepcopy(blocked_model),
            "knowledge": {"recognizedContract": {}},
        }
    }
}
blocked_overrides = {
    "provider_patches": {
        "blocked-provider": {
            "learned_routes": list(blocked_model["routes"]),
            "api_recipe": copy.deepcopy(blocked_model["apiRecipe"]),
        }
    }
}
finalize_provider(
    "blocked-provider",
    {"provider_id": "blocked-provider"},
    blocked_knowledge,
    blocked_overrides,
    blocked_evaluation,
    "terminal-blocked",
    [],
)
blocked_final = blocked_knowledge["providers"]["blocked-provider"]["model"]
assert set(blocked_final["routes"]) == set(base_model["routes"]), blocked_final["routes"]
assert blocked_final["apiRecipe"] == base_model["apiRecipe"], blocked_final["apiRecipe"]
assert blocked_final["routeRecognition"]["blockedPlanPreserved"] is True
assert set(blocked_overrides["provider_patches"]["blocked-provider"]["learned_routes"]) == set(base_model["routes"])
assert blocked_overrides["provider_patches"]["blocked-provider"]["api_recipe"] == base_model["apiRecipe"]

print(
    "PROVIDER_V3_FINALIZATION_PLAN_OK qualified_attempted_non2xx=preserved "
    "unexecuted_guess=pruned blocked_plan=preserved api_recipe=atomic"
)
