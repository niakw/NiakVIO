#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

spec = importlib.util.spec_from_file_location(
    "adaptive_runtime_repair_observed",
    ROOT / "scripts" / "adaptive_runtime" / "runtime_repair.py",
)
assert spec and spec.loader
runtime = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runtime)

candidate = {
    "canonical_id": "demo",
    "metadata": {
        "name": "Demo",
        "baseUrl": "https://demo.example",
        "supportedTypes": ["movie"],
    },
}
result = {
    "status": "no_streams",
    "evidence": {"streams_returned": 0, "streams_playable": 0},
    "tests": [{
        "fixture": {
            "label": "Fixture Movie",
            "title": "Fixture Movie",
            "tmdbId": "101",
            "mediaType": "movie",
            "year": 2020,
        },
        "failure_class": "content_lookup_completed_no_streams",
        "network_observations": [
            {
                "stage": "search",
                "host": "api.themoviedb.org",
                "method": "GET",
                "path_pattern": "/3/movie/{id}",
                "proof_url": "https://api.themoviedb.org/3/movie/101",
                "status": 200,
                "ok": True,
                "infrastructure": True,
            },
            {
                "stage": "search",
                "host": "demo.example",
                "method": "POST",
                "path_pattern": "/engine/ajax/search.php",
                "proof_url": "https://demo.example/engine/ajax/search.php",
                "proof_body_kind": "form",
                "proof_body_fields": ["query", "page"],
                "proof_body_values": {"query": "Fixture Movie", "page": "1"},
                "proof_headers": {
                    "content-type": "application/x-www-form-urlencoded",
                    "accept": "text/html",
                    "cookie": "must-not-be-used",
                },
                "content_type": "text/html; charset=utf-8",
                "status": 200,
                "ok": True,
                "infrastructure": False,
            },
            {
                "stage": "search",
                "host": "demo.example",
                "method": "GET",
                "path_pattern": "/api/search?q={value}",
                "proof_url": "https://demo.example/api/search?q=Fixture%20Movie",
                "content_type": "application/json",
                "status": 200,
                "ok": True,
                "infrastructure": False,
            },
            {
                # 987 is a provider-local ID, not the fixture TMDB id. Until
                # response->request binding exists this route must not execute.
                "stage": "player",
                "host": "demo.example",
                "method": "GET",
                "path_pattern": "/player/{id}",
                "proof_url": "https://demo.example/player/987",
                "content_type": "text/html",
                "status": 200,
                "ok": True,
                "infrastructure": False,
            },
            {
                "stage": "player",
                "host": "demo.example",
                "method": "GET",
                "path_pattern": "/player?token={value}",
                "proof_url": "https://demo.example/player?token=%3Credacted%3E",
                "status": 200,
                "ok": True,
                "infrastructure": False,
            },
            {
                "stage": "search",
                "host": "demo.example",
                "method": "GET",
                "path_pattern": "/failed?q={value}",
                "proof_url": "https://demo.example/failed?q=Fixture%20Movie",
                "status": 500,
                "ok": False,
                "infrastructure": False,
            },
        ],
    }],
}

recipes = runtime.observed_request_recipes(candidate, result)
assert len(recipes) == 2, recipes
assert [row["route"] for row in recipes] == [
    "/engine/ajax/search.php",
    "/api/search?q={query}",
], recipes
post = recipes[0]
assert post["source"] == "current-observation", post
assert post["method"] == "POST", post
assert post["body"] == {"query": "{query}", "page": "1"}, post
assert post["headerNames"] == ["accept", "content-type"], post
assert post["origin"] == "https://demo.example", post
assert recipes[1]["response"] == "json", recipes[1]
assert all("987" not in row["route"] for row in recipes)
assert all("token" not in row["route"].casefold() for row in recipes)

candidate["brain_observed_request_recipes"] = recipes
candidate["brain_repair_plan"] = {
    "failureClass": "route_proven_gap",
    "experimentVariant": 4,
    "experimentGeneration": 2,
}
config = {
    "provider_patches": {
        "demo": {"official_site": "https://demo.example", "capability": "html_scraper"},
    },
    "provider_capabilities": {
        "demo": {"strategy": "html_scraper", "catalogue_types": ["movie"]},
    },
}
options = runtime._adaptive_runtime_options(candidate, config)
assert options is not None
assert options["request_recipes"][:2] == recipes, options["request_recipes"]
assert options["route_prior_counts"]["currentObservationRequestRecipes"] == 2

# Planner transport must keep causal shape but not raw URL/body/header values.
spec2 = importlib.util.spec_from_file_location(
    "brain_runtime_observed",
    ROOT / "scripts" / "brain_repair_runtime.py",
)
assert spec2 and spec2.loader
brain = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(brain)
transport = brain._planner_result(result)
obs = transport["tests"][0]["network_observations"]
provider_obs = [row for row in obs if not row["infrastructure"]]
assert provider_obs[0]["stage"] == "search", provider_obs[0]
assert provider_obs[0]["method"] == "POST", provider_obs[0]
assert provider_obs[0]["path_pattern"] == "/engine/ajax/search.php", provider_obs[0]
assert provider_obs[0]["proof_body_kind"] == "form", provider_obs[0]
serialized = repr(transport)
assert "Fixture Movie" not in serialized, serialized
assert "proof_url" not in serialized, serialized
assert "proof_body_values" not in serialized, serialized
assert "cookie" not in serialized, serialized

runner = (ROOT / "scripts" / "run_adaptive_deep_repair.py").read_text(encoding="utf-8")
assert 'candidate["brain_observed_request_recipes"] = runtime_repair.observed_request_recipes(candidate, result)' in runner

print("Brain current-observation request recipe contract passed")
