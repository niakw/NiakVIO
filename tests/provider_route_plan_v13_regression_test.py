#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import recover_provider_routes_from_upstreams as recovery  # noqa: E402


def row(route: str, *, reusable: bool, headers: dict | None = None, external: bool = False, role: str = "detail") -> dict:
    return {
        "route": route,
        "origin": "https://provider.example",
        "role": role,
        "method": "GET",
        "semanticType": "tv",
        "fixture": "fixture",
        "requestSpecReusable": reusable,
        "requestSpec": {"method": "GET", "headers": headers or {}},
        "externalIdentityCorrelation": external,
        "taskStreamCount": 4,
        "taskRawStreamCount": 4,
    }


# Flat routes require both reusable request semantics and a proof-derived dynamic identity.
assert recovery.generic_execution_route(row("/browser?keyword={query}", reusable=True, role="search")) is True
assert recovery.generic_execution_route(row("/watch/title/ep-1", reusable=True)) is False
assert recovery.generic_execution_route(row("/file/rwaq016kx4ig", reusable=False)) is False
assert recovery.generic_execution_route(row("/series/{imdbId}", reusable=True, headers={"Referer": "https://provider.example/"}, external=True)) is False

# Fresh non-flat observations block the same stale flat baseline from being preserved.
blocked = recovery._flat_route_blocklist([
    row("/file/rwaq016kx4ig", reusable=False),
    row("/browser?keyword={query}", reusable=True, role="search"),
])
routes, preserved = recovery.select_runtime_routes(
    ["/file/rwaq016kx4ig", "/old/search?q={query}"],
    ["/file/rwaq016kx4ig"],
    ["/browser?keyword={query}"],
    blocked,
)
assert routes == ["/browser?keyword={query}"], (routes, preserved)
assert preserved is False

# External-ID structured plan preserves origin + request headers but excludes terminal HLS output.
plan = recovery._positive_external_identity_plan(
    [
        row(
            "/series/{imdbId}",
            reusable=True,
            headers={"Referer": "https://provider.example/", "Origin": "https://provider.example"},
            external=True,
        ),
        row(
            "/hls/s2/serial/{imdbId}/1/1/playlist.m3u8",
            reusable=True,
            headers={"Referer": "https://provider.example/"},
            external=True,
        ),
        {
            **row("/meta/series/{imdbId}.json", reusable=True, external=True),
            "origin": "https://v3-cinemeta.strem.io",
        },
    ],
    {},
)
assert len(plan) == 1, plan
assert plan[0]["base"] == "https://provider.example", plan
assert plan[0]["route"] == "/series/{imdbId}", plan
assert plan[0]["requestSpec"]["headers"]["Origin"] == "https://provider.example", plan

base = (ROOT / "scripts" / "provider_base_store.py").read_text(encoding="utf-8")
migration = (ROOT / "scripts" / "upgrade_provider_route_plan_v13.py").read_text(encoding="utf-8").casefold()
for marker in (
    "NIAKVIO_PROVIDER_BASE_STRUCTURED_EXTERNAL_ID_V13",
    "async function _resolveExternalIdentityPlan",
    "function _externalEpisodeMarker",
    "externalIdentityPlan",
    "imdbId: values.imdbId",
):
    assert marker in base, marker

# Generic migration must not encode the motivating providers/hosts.
for forbidden in ("papadustream", "movies4u", "animekai", "m4uplay", "anikai.cc"):
    assert forbidden not in migration, forbidden

print("provider route plan v13 regression passed")
