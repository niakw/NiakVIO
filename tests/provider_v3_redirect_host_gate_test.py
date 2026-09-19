#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_provider_v3_routes_sequential import (  # noqa: E402
    _generic_control_route,
    _provider_contract_hosts,
    evaluate_provider,
    should_pass,
)

common = {
    "method": "GET",
    "status": 200,
    "content_type": "text/html",
    "header_names": ["accept"],
    "body_kind": "none",
    "body_fields": [],
}

# Regression 1: request identity must survive an HTTP redirect to a current
# provider terminal. Before the fix, only final_url was checked and this 200
# response was rejected because current.example was not yet canonical DATA.
redirect_model = {
    "canonicalSupportedTypes": ["anime"],
    "knownSite": "https://old.example",
    "routeData": [{"route": "/anime/{slug}", "type": "anime"}],
}
redirect_task = {
    "semantic_type": "anime",
    "fixture_slug": "jujutsu-kaisen-s01e01",
    "fixture": {
        "tmdbId": "95479",
        "mediaType": "anime",
        "title": "Jujutsu Kaisen",
        "season": 1,
        "episode": 1,
    },
    "status": "no_streams",
    "fetches": [{
        **common,
        "url": "https://old.example/anime/jujutsu-kaisen",
        "final_url": "https://current.example/anime/jujutsu-kaisen",
    }],
}
redirect_eval = evaluate_provider("redirect-regression", redirect_model, [redirect_task], 0.75)
assert redirect_eval["validatedTypes"] == ["anime"], redirect_eval
assert redirect_eval["missingTypes"] == [], redirect_eval
assert should_pass(redirect_eval) is True, redirect_eval

# Regression 2: officialHub is first-class provider authority. If another stale
# knownSite is also present, calls initiated on the hub must not be rejected.
hub_model = {
    "canonicalSupportedTypes": ["anime"],
    "knownSite": "https://stale.example",
    "officialHub": "https://hub.example",
    "routeData": [{"route": "/anime/{slug}", "type": "anime"}],
}
hosts = _provider_contract_hosts(hub_model)
assert "hub.example" in hosts, hosts
assert "stale.example" in hosts, hosts
hub_task = {
    **redirect_task,
    "fetches": [{
        **common,
        "url": "https://hub.example/anime/jujutsu-kaisen",
        "final_url": "https://current.example/anime/jujutsu-kaisen",
    }],
}
hub_eval = evaluate_provider("hub-regression", hub_model, [hub_task], 0.75)
assert hub_eval["validatedTypes"] == ["anime"], hub_eval
assert should_pass(hub_eval) is True, hub_eval

# Regression 3: query-only typed APIs are real provider routes, not arbitrary
# homepages. This is the Animesalt family shape: movie/tv/anime share `/` and
# differ by the semantic query literal while tmdbId carries reusable identity.
for media_type in ("movie", "tv", "anime"):
    route = f"/?tmdbId={{tmdbId}}&type={media_type}"
    assert _generic_control_route(route) is False, route

# Keep the false-positive guard strict. A root homepage does not become route
# proof merely because it accepts arbitrary params, a literal id, or type alone.
for route in (
    "/",
    "/?foo=bar",
    "/?tmdbId=123&type=movie",
    "/?tmdbId={tmdbId}",
    "/?type=movie",
):
    assert _generic_control_route(route) is True, route

query_model = {
    "canonicalSupportedTypes": ["movie", "tv", "anime"],
    "knownSite": "https://query.example",
    "routeData": [
        {"route": "/?tmdbId={tmdbId}&type=movie", "type": "movie"},
        {"route": "/?tmdbId={tmdbId}&type=tv", "type": "tv"},
        {"route": "/?tmdbId={tmdbId}&type=anime", "type": "anime"},
    ],
}
query_tasks = []
for media_type, tmdb_id in (("movie", "157336"), ("tv", "94605"), ("anime", "95479")):
    query_tasks.append({
        "semantic_type": media_type,
        "fixture_slug": f"typed-query-{media_type}",
        "fixture": {
            "tmdbId": tmdb_id,
            "mediaType": media_type,
            "title": f"Fixture {media_type}",
        },
        "status": "no_streams",
        "fetches": [{
            **common,
            "url": f"https://query.example/?tmdbId={tmdb_id}&type={media_type}",
            "final_url": f"https://query.example/?tmdbId={tmdb_id}&type={media_type}",
        }],
    })
query_eval = evaluate_provider("typed-query-regression", query_model, query_tasks, 0.75)
assert set(query_eval["validatedTypes"]) == {"movie", "tv", "anime"}, query_eval
assert query_eval["missingTypes"] == [], query_eval
assert should_pass(query_eval) is True, query_eval

print(
    "PROVIDER_V3_REDIRECT_HOST_GATE_TEST_OK "
    "request_identity=true official_hub=true typed_query_root=true"
)
