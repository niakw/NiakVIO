#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_provider_v3_routes_sequential import (  # noqa: E402
    coverage_target,
    derive_observed_route,
    evaluate_provider,
    should_pass,
)

fixture = {
    "tmdbId": "157336",
    "mediaType": "movie",
    "title": "Interstellar",
    "year": 2014,
}
task = {"fixture": fixture, "semantic_type": "movie", "fixture_title": "Interstellar"}
fetch = {
    "url": "https://example.test/api/search?q=Interstellar&id=157336",
    "final_url": "https://example.test/api/search?q=Interstellar&id=157336",
    "method": "GET",
    "status": 200,
    "content_type": "application/json",
    "header_names": ["accept"],
    "body_kind": "none",
    "body_fields": [],
}
route, meta = derive_observed_route(fetch, task)
assert route == "/api/search?q={query}&id={tmdbId}", (route, meta)
assert meta["reusable"] is True, meta

# Legacy percentage helper remains diagnostic only.
assert coverage_target(1, 0.75) == 1.0
assert coverage_target(2, 0.75) == 1.0
assert coverage_target(5, 0.75) == 0.75

# The actual gate is now binary over all declared semantic types.
base = {
    "typeComplete": True,
    "declaredTypeCoverageRatio": 1.0,
    "effectiveCoverageRatio": 1.0,
    "requiredCoverageRatio": 1.0,
}
assert should_pass(base) is True, base
assert should_pass({**base, "declaredTypeCoverageRatio": 0.5}) is False
assert should_pass({**base, "typeComplete": False}) is False
# Internal unresolved request counts can no longer make a complete typed provider fail.
assert should_pass({
    **base,
    "unresolvedObservedRequestCount": 999,
    "observedRequestShapeCount": 1000,
}) is True

# Purstream-shaped regression: [movie,tv] means exactly movie + tv route proof.
# Search/status traffic is chain evidence only and cannot validate a missing type.
model = {
    "canonicalSupportedTypes": ["movie", "tv"],
    "knownSite": "https://purstream.test",
    "officialApi": "https://api.purstream.test/api/v1",
    "apiRecipe": {
        "base": "https://api.purstream.test/api/v1",
        "searchRoute": "/search-bar/search/{query}",
        "movieRoute": "/stream/{id}",
        "episodeRoute": "/stream/{id}/episode?season={season}&episode={episode}",
    },
    "routeData": [
        {"route": "/search-bar/search/{query}", "role": "search"},
        {"route": "/stream/{id}", "role": "detail"},
        {"route": "/stream/{id}/episode?season={season}&episode={episode}", "role": "detail"},
        {"route": "/api/status", "role": "api"},
    ],
}
common = {
    "method": "GET",
    "status": 200,
    "content_type": "application/json",
    "header_names": ["accept"],
    "body_kind": "none",
    "body_fields": [],
}
movie_task = {
    "semantic_type": "movie",
    "fixture_slug": "interstellar",
    "fixture": {"tmdbId": "157336", "mediaType": "movie", "title": "Interstellar"},
    "status": "playable_verified",
    "fetches": [
        {**common, "url": "https://api.purstream.test/api/v1/search-bar/search/Interstellar", "final_url": "https://api.purstream.test/api/v1/search-bar/search/Interstellar"},
        {**common, "url": "https://api.purstream.test/api/v1/stream/525", "final_url": "https://api.purstream.test/api/v1/stream/525"},
    ],
}
tv_search_only = {
    "semantic_type": "tv",
    "fixture_slug": "breaking-bad-s01e01",
    "fixture": {"tmdbId": "1396", "mediaType": "tv", "title": "Breaking Bad", "season": 1, "episode": 1},
    "status": "no_streams",
    "fetches": [
        {**common, "url": "https://api.purstream.test/api/v1/search-bar/search/Breaking%20Bad", "final_url": "https://api.purstream.test/api/v1/search-bar/search/Breaking%20Bad"},
        {**common, "url": "https://purstream.test/api/status", "final_url": "https://purstream.test/api/status"},
    ],
}
evaluation = evaluate_provider("purstream", model, [movie_task, tv_search_only], 0.75)
assert evaluation["validatedTypes"] == ["movie"], evaluation["declaredTypeRouteEvidence"]
assert evaluation["missingTypes"] == ["tv"], evaluation
assert evaluation["declaredTypeCoverageRatio"] == 0.5, evaluation
assert should_pass(evaluation) is False

# Once the tv episode route itself answers, both declared types are proven.
tv_complete = {
    **tv_search_only,
    "status": "playable_verified",
    "fetches": [
        *tv_search_only["fetches"],
        {**common, "url": "https://api.purstream.test/api/v1/stream/525/episode?season=1&episode=1", "final_url": "https://api.purstream.test/api/v1/stream/525/episode?season=1&episode=1"},
    ],
}
evaluation = evaluate_provider("purstream", model, [movie_task, tv_complete], 0.75)
assert evaluation["validatedTypes"] == ["movie", "tv"], evaluation["declaredTypeRouteEvidence"]
assert evaluation["missingTypes"] == [], evaluation
assert evaluation["declaredTypeCoverageRatio"] == 1.0, evaluation
assert should_pass(evaluation) is True

source = (ROOT / "scripts" / "validate_provider_v3_routes_sequential.py").read_text(encoding="utf-8")
assert "ThreadPoolExecutor" not in source
assert "as_completed" not in source
assert "for index, provider in enumerate(queue, start=1):" in source
assert "declaredTypesAreGateDenominator" in source
assert "internalRequestsAreGateDenominator" in source
assert "missing live route proof for declared types" in source
assert "write(knowledge_path, knowledge)" in source

reconstruct = (ROOT / "scripts" / "reconstruct_provider_v3_sequential_live.py").read_text(encoding="utf-8")
assert 'completion_state = "declared-types-qualified"' in reconstruct
assert "validated_types=" in reconstruct
assert "missing_types=" in reconstruct
assert "requiredDeclaredTypeCoverageRatio" in reconstruct

probe = (ROOT / "scripts" / "nuvio_tv_probe_route_validation.cjs").read_text(encoding="utf-8")
assert "function requestPhase()" in probe
assert "inspectStream|inspectHlsChild" in probe
assert "network_phase: phase" in probe
assert "if (phase === 'playback') playbackRequestCount += 1;" in probe
assert "else routeTrace.push(evidence);" in probe
assert "playback_request_count: playbackRequestCount" in probe
assert "schema_version: 2" in probe

print(
    "Provider v3 sequential live gate tests passed: declared semantic types are the only gate denominator, "
    "Purstream movie+tv requires both typed routes, search/status/playback traffic cannot inflate coverage, "
    "and providers still advance strictly one at a time."
)
