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


second = derive_with_hint("imdb_id", "tt0903747")
assert second["route"] == "/series/{imdbId}", second
assert second["derivation"].get("externalIdentityCorrelation") is True, second
assert second["derivation"].get("providerValueCorrelation") is False, second

generic = derive_with_hint("id", "tt12343534")
assert generic["route"] == "/series/{imdbId}", generic
assert generic["derivation"].get("externalIdentityCorrelation") is True, generic
assert generic["derivation"].get("providerValueCorrelation") is False, generic

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

assert materializer._identity_mode_from_plan(["/series/{imdbId}"], None) == "external_id"

worker = (ROOT / "scripts" / "provider_worker.cjs").read_text(encoding="utf-8")
base = (ROOT / "scripts" / "provider_base_store.py").read_text(encoding="utf-8")
recovery_source = (ROOT / "scripts" / "recover_provider_routes_from_upstreams.py").read_text(encoding="utf-8")
assert "NUVIO_PROVIDER_WORKER_EXTERNAL_IDENTITY_HINT_V11" in worker
assert "NIAKVIO_PROVIDER_BASE_EXTERNAL_IDENTITY_ROUTE_V11" in base
assert "NIAKVIO_PROVIDER_MODEL.proofDetailBases" in base
assert "const imdbId = _text(meta && meta.imdbId)" in base
assert "ROUTE_RECOVERY_HELPER_EVIDENCE_ONLY_V11_1" in recovery_source
assert "if _repair_recipe_origin_allowed(row) and generic_execution_route(row)" in recovery_source

print("provider external identity route v11 tests passed")
