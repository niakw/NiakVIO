#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import provider_route_proof as proof  # noqa: E402
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

# A metadata response may prove an external IMDb identity without becoming an
# executable provider route itself. The following provider path must consume that
# evidence as {imdbId}, not as generic {id} and never as a frozen literal.
task = {
    "fixture": fixture,
    "fetches": [
        {
            "url": "https://arm.haglund.dev/api/v2/themoviedb?id=1396",
            "final_url": "https://arm.haglund.dev/api/v2/themoviedb?id=1396",
            "method": "GET",
            "status": 200,
            "body_kind": "none",
            "response_value_hints": [{"key": "imdb_id", "value": "tt0903747"}],
        },
        {
            "url": "https://papadustream.club/series/tt0903747",
            "final_url": "https://papadustream.club/series/tt0903747",
            "method": "GET",
            "status": 200,
            "body_kind": "none",
            "response_value_hints": [],
        },
    ],
}
rows = proof.derive_task_routes(task)
assert len(rows) == 2, rows
second = rows[1]
assert second["route"] == "/series/{imdbId}", second
assert second["derivation"].get("externalIdentityCorrelation") is True, second
assert second["derivation"].get("providerValueCorrelation") is False, second

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

# Existing materializer identity classification already knows that an IMDb route
# requires Core metadata before provider execution.
assert materializer._identity_mode_from_plan(["/series/{imdbId}"], None) == "external_id"

worker = (ROOT / "scripts" / "provider_worker.cjs").read_text(encoding="utf-8")
base = (ROOT / "scripts" / "provider_base_store.py").read_text(encoding="utf-8")
assert "NUVIO_PROVIDER_WORKER_EXTERNAL_IDENTITY_HINT_V11" in worker
assert "NIAKVIO_PROVIDER_BASE_EXTERNAL_IDENTITY_ROUTE_V11" in base
assert "const imdbId = _text(meta && meta.imdbId)" in base

print("provider external identity route v11 tests passed")
