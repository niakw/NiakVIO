#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

# Keep this contract test standalone: apply the durable migration before importing
# the runtime under test. The full reconstruction source-plan applies it earlier.
from upgrade_provider_terminal_media_block_v1 import patch as patch_terminal_media_block  # noqa: E402

patch_terminal_media_block()

from validate_provider_v3_routes_sequential import (  # noqa: E402
    coverage_target,
    derive_observed_route,
    evaluate_provider,
    should_pass,
)
from reconstruct_provider_v3_sequential_live import terminal_state  # noqa: E402

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
assert should_pass({
    **base,
    "unresolvedObservedRequestCount": 999,
    "observedRequestShapeCount": 1000,
}) is True

# Purstream-shaped regression: [movie,tv] means exactly movie + tv route proof.
# Search/status traffic is chain evidence only and cannot validate a missing type.
# Routes are relative to the API base, so /stream/{id} must match /api/v1/stream/525
# without ever promoting the literal provider-internal id 525 as a reusable route.
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
movie_evidence = evaluation["declaredTypeRouteEvidence"]["movie"]
assert movie_evidence and movie_evidence[0]["route"] == "/stream/{id}", movie_evidence
assert movie_evidence[0]["source"] == "declared-type-template-live-match", movie_evidence
assert all("/stream/525" != str(row.get("route")) for row in movie_evidence), movie_evidence
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
assert evaluation["declaredTypeRouteEvidence"]["tv"][0]["route"] == "/stream/{id}/episode?season={season}&episode={episode}", evaluation["declaredTypeRouteEvidence"]
assert should_pass(evaluation) is True

# Cineby-shaped regression: exact typed identity resolves to concrete HLS URLs, but
# the runner is denied on every resolved media request. This is terminal transport
# evidence only; movie/tv remain unvalidated and no blocked HLS is promoted.
def request(url: str, status: int, content_type: str = "text/plain") -> dict:
    return {
        "url": url,
        "final_url": url,
        "method": "GET",
        "status": status,
        "content_type": content_type,
        "header_names": ["accept"],
        "body_kind": "none",
        "body_fields": [],
    }

cineby_model = {
    "canonicalSupportedTypes": ["movie", "tv"],
    "routeData": [],
}
cineby_movie = {
    "semantic_type": "movie",
    "fixture_slug": "interstellar",
    "fixture": {"tmdbId": "157336", "mediaType": "movie", "title": "Interstellar", "year": 2014},
    "status": "no_streams",
    "fetches": [
        request("https://api.example.test/cdn/sources-with-title?title=Interstellar&mediaType=movie&tmdbId=157336", 200),
        request("https://media.example.test/x/index-s1080p-v1-a1.m3u8", 403, "text/html"),
        request("https://media.example.test/x/index-s720p-v1-a1.m3u8", 403, "text/html"),
    ],
}
cineby_tv = {
    "semantic_type": "tv",
    "fixture_slug": "breaking-bad-s01e01",
    "fixture": {"tmdbId": "1396", "mediaType": "tv", "title": "Breaking Bad", "season": 1, "episode": 1},
    "status": "no_streams",
    "fetches": [
        request("https://api.example.test/cdn/sources-with-title?mediaType=tv&tmdbId=1396&seasonId=1&episodeId=1", 200),
        request("https://media.example.test/y/playlist.m3u8", 403, "text/html"),
    ],
}
media_blocked = evaluate_provider("cineby", cineby_model, [cineby_movie, cineby_tv], 0.75)
assert media_blocked["validatedTypes"] == [], media_blocked
assert media_blocked["missingTypes"] == ["movie", "tv"], media_blocked
assert media_blocked["providerMediaBlockedTypes"] == ["movie", "tv"], media_blocked
assert media_blocked["providerMediaBlockedComplete"] is True, media_blocked
assert media_blocked["providerMediaBlockClassification"] == "exact-identity-resolved-media-blocked", media_blocked
assert terminal_state(media_blocked, cineby_model, {}, 3)[0] == "terminal-blocked"
assert should_pass(media_blocked) is False
assert all(
    row.get("validationState") != "live-validated"
    for row in media_blocked["candidateRouteData"]
    if str(row.get("route") or "").endswith(".m3u8")
), media_blocked["candidateRouteData"]

search_only = {
    **cineby_movie,
    "fetches": [
        request("https://api.example.test/search?q=Interstellar", 200, "application/json"),
        request("https://media.example.test/unrelated/master.m3u8", 403, "text/html"),
    ],
}
search_eval = evaluate_provider("search-only", {"canonicalSupportedTypes": ["movie"], "routeData": []}, [search_only], 0.75)
assert search_eval["providerMediaBlockedComplete"] is False, search_eval

media_404 = {
    **cineby_movie,
    "fetches": [
        request("https://api.example.test/cdn/sources-with-title?mediaType=movie&tmdbId=157336", 200),
        request("https://media.example.test/missing/master.m3u8", 404, "text/html"),
    ],
}
media_404_eval = evaluate_provider("media-404", {"canonicalSupportedTypes": ["movie"], "routeData": []}, [media_404], 0.75)
assert media_404_eval["providerMediaBlockedComplete"] is False, media_404_eval

tv_control_only = {
    **cineby_tv,
    "fetches": [
        request("https://api.example.test/cdn/sources-with-title?mediaType=tv&tmdbId=1396&seasonId=1&episodeId=1", 200),
    ],
}
partial_eval = evaluate_provider("partial", cineby_model, [cineby_movie, tv_control_only], 0.75)
assert partial_eval["providerMediaBlockedTypes"] == ["movie"], partial_eval
assert partial_eval["providerMediaBlockedComplete"] is False, partial_eval
assert terminal_state(partial_eval, cineby_model, {}, 3)[0] is None

source = (ROOT / "scripts" / "validate_provider_v3_routes_sequential.py").read_text(encoding="utf-8")
assert "ThreadPoolExecutor" not in source
assert "as_completed" not in source
assert "for index, provider in enumerate(queue, start=1):" in source
assert "declaredTypesAreGateDenominator" in source
assert "internalRequestsAreGateDenominator" in source
assert "missing live route proof for declared types" in source
assert "_route_matches_model_url" in source
assert "Unknown literal IDs" in source
assert "write(knowledge_path, knowledge)" in source
assert "PROVIDER_V3_TERMINAL_MEDIA_BLOCK_V1" in source
assert "providerMediaBlockedComplete" in source

reconstruct = (ROOT / "scripts" / "reconstruct_provider_v3_sequential_live.py").read_text(encoding="utf-8")
assert 'completion_state = "declared-types-qualified"' in reconstruct
assert "validated_types=" in reconstruct
assert "missing_types=" in reconstruct
assert "requiredDeclaredTypeCoverageRatio" in reconstruct
assert "PROVIDER_V3_TERMINAL_MEDIA_BLOCK_V1" in reconstruct
assert 'evaluation.get("providerMediaBlockedComplete")' in reconstruct

probe = (ROOT / "scripts" / "nuvio_tv_probe_route_validation.cjs").read_text(encoding="utf-8")
assert "function requestPhase()" in probe
assert "inspectStream|inspectHlsChild" in probe
assert "network_phase: phase" in probe
assert "if (phase === 'playback') playbackRequestCount += 1;" in probe
assert "else routeTrace.push(evidence);" in probe
assert "playback_request_count: playbackRequestCount" in probe
assert "schema_version: 2" in probe

print(
    "Provider v3 sequential live gate tests passed: declared semantic types remain the only positive gate denominator, "
    "exact-identity resolved media blocks are terminal transport evidence only, 404/search-only/partial-lane cases stay red, "
    "and providers still advance strictly one at a time."
)
