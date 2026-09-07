#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import provider_route_proof as proof  # noqa: E402
import recover_provider_routes_from_upstreams as recovery  # noqa: E402
import materialize_provider_v3_all as materializer  # noqa: E402

fixture = {
    "slug": "breaking-bad-s01e01",
    "tmdbId": "1396",
    "mediaType": "tv",
    "title": "Breaking Bad",
    "year": 2008,
    "season": 1,
    "episode": 1,
}


def derive_with_hint(key: str, value: str) -> dict:
    task = {
        "fixture": fixture,
        "fetches": [
            {
                "url": "https://arm.haglund.dev/api/v2/themoviedb?id=1396",
                "final_url": "https://arm.haglund.dev/api/v2/themoviedb?id=1396",
                "method": "GET",
                "status": 200,
                "body_kind": "none",
                "response_value_hints": [{"key": key, "value": value}],
            },
            {
                "url": f"https://papadustream.club/series/{value}",
                "final_url": f"https://papadustream.club/series/{value}",
                "method": "GET",
                "status": 200,
                "body_kind": "none",
                "response_value_hints": [],
            },
        ],
    }
    rows = proof.derive_task_routes(task)
    assert len(rows) == 2, rows
    return rows[1]


# Explicit imdb_id evidence becomes semantic {imdbId}.
second = derive_with_hint("imdb_id", "tt0903747")
assert second["route"] == "/series/{imdbId}", second
assert second["derivation"].get("externalIdentityCorrelation") is True, second
assert second["derivation"].get("providerValueCorrelation") is False, second

# Cinemeta commonly exposes the same external identity under generic key `id`.
# IMDb shape must still win over provider-internal generic ID classification.
generic = derive_with_hint("id", "tt12343534")
assert generic["route"] == "/series/{imdbId}", generic
assert generic["derivation"].get("externalIdentityCorrelation") is True, generic
assert generic["derivation"].get("providerValueCorrelation") is False, generic

# The same literal without prior response proof is rejected fail-closed.
route, meta = proof.derive_observed_route(
    {
        "url": "https://papadustream.club/series/tt0903747",
        "final_url": "https://papadustream.club/series/tt0903747",
        "method": "GET",
        "status": 200,
        "body_kind": "none",
    },
    {"fixture": fixture},
    [],
)
assert route is None, (route, meta)
assert "tt0903747" in (meta.get("unresolvedOpaqueSegments") or []), meta

# Positive external-ID detail origin is execution authority, but helper metadata
# origins remain excluded by the same provider-origin boundary used by V10.
detail_bases = recovery._positive_external_detail_bases(
    [
        {
            "origin": "https://papadustream.club",
            "route": "/series/{imdbId}",
            "role": "detail",
            "requestSpecReusable": True,
            "externalIdentityCorrelation": True,
            "taskStreamCount": 4,
            "taskRawStreamCount": 4,
        },
        {
            "origin": "https://arm.haglund.dev",
            "route": "/meta/{imdbId}",
            "role": "detail",
            "requestSpecReusable": True,
            "externalIdentityCorrelation": True,
            "taskStreamCount": 4,
            "taskRawStreamCount": 4,
        },
    ],
    {},
)
assert detail_bases == ["https://papadustream.club"], detail_bases

# Existing materializer identity classification knows that an IMDb route requires
# Core metadata before provider execution.
assert materializer._identity_mode_from_plan(["/series/{imdbId}"], None) == "external_id"

worker = (ROOT / "scripts" / "provider_worker.cjs").read_text(encoding="utf-8")
base = (ROOT / "scripts" / "provider_base_store.py").read_text(encoding="utf-8")
assert "NUVIO_PROVIDER_WORKER_EXTERNAL_IDENTITY_HINT_V11" in worker
assert "NIAKVIO_PROVIDER_BASE_EXTERNAL_IDENTITY_ROUTE_V11" in base
assert "NIAKVIO_PROVIDER_MODEL.proofDetailBases" in base
assert "const imdbId = _text(meta && meta.imdbId)" in base

print("provider external identity route v11 tests passed")
