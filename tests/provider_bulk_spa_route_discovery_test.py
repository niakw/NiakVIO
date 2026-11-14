#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "scripts" / "probe_bulk_provider_routes.py"
spec = importlib.util.spec_from_file_location("probe_bulk_provider_routes", PATH)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

movie = {"title": "Interstellar", "tmdbId": "157336", "mediaType": "movie"}
tv = {"title": "Breaking Bad", "tmdbId": "1396", "mediaType": "tv", "season": 1, "episode": 1}
dollar = "$"

assert module._template_js_route(
    "/api/source?tmdb_id=" + dollar + "{id}&type=movie", movie
) == "/api/source?tmdb_id={tmdbId}&type={media}"

assert module._template_js_route(
    "/embed/tv/" + dollar + "{id}/" + dollar + "{season}/" + dollar + "{episode}", tv
) == "/embed/tv/{tmdbId}/{season}/{episode}"

bundle = (
    'const a = "/api/source?tmdb_id=' + dollar + '{id}&type=movie";\n'
    'const b = "https://api.themoviedb.org/3/movie/157336";\n'
    'const c = "/embed/tv/' + dollar + '{id}/' + dollar + '{season}/' + dollar + '{episode}";\n'
)
movie_routes = module._js_route_templates(bundle, movie, origin_host="example.test")
tv_routes = module._js_route_templates(bundle, tv, origin_host="example.test")

assert "/api/source?tmdb_id={tmdbId}&type={media}" in movie_routes, movie_routes
assert "/embed/tv/{tmdbId}/{season}/{episode}" in tv_routes, tv_routes
assert not any("themoviedb.org" in route for route in movie_routes + tv_routes)

assert module._safe_spa_route_candidate("/api/source?tmdb_id={tmdbId}&type={media}")
assert not module._safe_spa_route_candidate('/<iframe src="https://vidsrc.sh/embed/movie/{tmdbId}">')
assert not module._safe_spa_route_candidate("/,{query:e,include_adult:!1,page:1})).results")

assert module._identity_bound_api_response(
    b'{"src":"https://player.example/embed/movie/157336"}',
    "/api/source?tmdb_id={tmdbId}&type=movie",
    movie,
)
assert module._identity_bound_api_response(
    b'{"url":"https://cdn.example/master.m3u8"}',
    "/api/source?tmdb_id={tmdbId}&season={season}&episode={episode}",
    tv,
)
assert not module._identity_bound_api_response(
    b'{"url":"https://cdn.example/master.m3u8"}',
    "/api/source?tmdb_id={tmdbId}",
    tv,
)

print("PROVIDER_BULK_SPA_ROUTE_DISCOVERY_OK")
