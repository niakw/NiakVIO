#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import provider_route_proof as proof  # noqa: E402

task = {
    "fixture": {
        "tmdbId": "123",
        "mediaType": "movie",
        "title": "Sinners",
        "year": 2025,
    }
}
fetch = {
    "url": "https://4khdhub.one/sinners-movie-7978/",
    "final_url": "https://4khdhub.one/sinners-movie-7978/",
    "method": "GET",
    "status": 200,
    "content_type": "text/html",
}

route, meta = proof.derive_observed_route(fetch, task, [])
assert route is None, (route, meta)
assert meta["reusable"] is False, meta
assert meta["fixtureSpecificValues"] or meta["unresolvedOpaqueSegments"], meta

route2, meta2 = proof.derive_observed_route(
    fetch,
    task,
    [{"key": "id", "value": "7978"}],
)
assert route2 == "/{slug}-movie-{id}/", (route2, meta2)
assert meta2["reusable"] is True, meta2
assert meta2["providerValueCorrelation"] is True, meta2
assert meta2["unresolvedOpaqueSegments"] == [], meta2

# A numeric token hidden in a composite template remains unsafe if no prior
# response provided authority for that exact provider-local value.
fetch_series = {
    **fetch,
    "url": "https://4khdhub.one/breaking-bad-series-1385/",
    "final_url": "https://4khdhub.one/breaking-bad-series-1385/",
}
tv_task = {
    "fixture": {
        "tmdbId": "1396",
        "mediaType": "tv",
        "title": "Breaking Bad",
        "year": 2008,
        "season": 1,
        "episode": 1,
    }
}
route3, meta3 = proof.derive_observed_route(fetch_series, tv_task, [])
assert route3 is None, (route3, meta3)
assert meta3["reusable"] is False, meta3

route4, meta4 = proof.derive_observed_route(
    fetch_series,
    tv_task,
    [{"key": "post_id", "value": "1385"}],
)
assert route4 == "/{slug}-series-{id}/", (route4, meta4)
assert meta4["providerValueCorrelation"] is True, meta4

print("provider composite-id causal route proof test passed")
