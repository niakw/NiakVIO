#!/usr/bin/env python3
"""Identity preflight must be inferred from executable DATA, not site presence."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from materialize_provider_v3_all import identity_input, provider_model  # noqa: E402


def assert_mode(value, expected, requires):
    assert value["mode"] == expected, value
    assert value["requiresTmdbBeforeRun"] is requires, value


# A trusted site or API origin is routing context, not evidence that title
# metadata is needed before provider execution.
assert_mode(identity_input({"official_site": "https://example.test"}, ["/api/movie/{id}"], None), "tmdb_direct", False)

# Real catalogue/title/slug plans need Core TMDB metadata first.
assert_mode(identity_input({}, ["/search?q={query}", "/film/{slug}"], None), "catalog_search", True)
assert_mode(identity_input({}, ["/api/search/{query}"], None), "catalog_search", True)

# A direct recipe must stay deferred; a search recipe must preflight.
assert_mode(identity_input({}, [], {"directRoute": "/{media}?id={tmdbId}&mode=json"}), "tmdb_direct", False)
assert_mode(identity_input({}, [], {"searchRoute": "/search-bar/search/{query}", "movieRoute": "/stream/{id}"}), "catalog_search", True)

# External-id plans need Core metadata, which already carries external_ids.
assert_mode(identity_input({}, ["/resolve?imdb={imdbId}"], None), "external_id", True)

# Static-library pollution must never turn a direct provider into catalogue mode.
assert_mode(identity_input({}, ["/search?q=ponyfill", "/license", "/api/movie/{id}"], None), "tmdb_direct", False)

# Explicit contracts remain authoritative.
explicit = {
    "identity_input": {
        "mode": "catalog_search",
        "requires_tmdb_before_run": True,
        "required_fields": ["title", "mediaType"],
    }
}
value = identity_input(explicit, ["/api/movie/{id}"], {"directRoute": "/movie/{tmdbId}"})
assert value["mode"] == "catalog_search" and value["requiredFields"] == ["title", "mediaType"], value

# Most importantly, static refreshed DATA participates in inference.
model = provider_model(
    "fixture",
    {"official_site": "https://example.test"},
    {"strategy": "html_scraper"},
    {"model": {"routes": ["/?s={query}", "/film/{slug}"], "strategy": "html_scraper"}},
)
assert_mode(model["identityInput"], "catalog_search", True)

direct_model = provider_model(
    "fixture-direct",
    {"official_site": "https://api.example.test"},
    {"strategy": "api_stream_resolver"},
    {"model": {"routes": ["/api/sources/movie/{id}"], "strategy": "api_stream_resolver"}},
)
assert_mode(direct_model["identityInput"], "tmdb_direct", False)

print("provider v3 identity preflight contract passed")
