#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import provider_route_proof as proof  # noqa: E402
import upgrade_provider_response_value_correlation_v20_2 as v20  # noqa: E402


# The migration must be idempotent and all owners must retain the V20 contract.
v20.main()
v20.main()

# Reload the proof module after the migration rewrites provider_route_proof.py.
import importlib.util  # noqa: E402
spec = importlib.util.spec_from_file_location("provider_route_proof_v20_test", ROOT / "scripts" / "provider_route_proof.py")
assert spec and spec.loader
proof = importlib.util.module_from_spec(spec)
spec.loader.exec_module(proof)

fixture = {
    "tmdbId": "95479",
    "mediaType": "anime",
    "title": "Jujutsu Kaisen",
    "year": 2020,
    "season": 1,
    "episode": 1,
}
task = {"fixture": fixture}

route, meta = proof.derive_observed_route(
    {
        "url": "https://example.invalid/engine/ajax/manga_episodes_api.php?id=1497198",
        "final_url": "https://example.invalid/engine/ajax/manga_episodes_api.php?id=1497198",
        "method": "GET",
        "body_kind": "none",
        "body_values": {},
        "proof_headers": {},
    },
    task,
    [{"key": "id", "value": "1497198"}],
)
assert route == "/engine/ajax/manga_episodes_api.php?id={id}", (route, meta)
assert meta["providerValueCorrelation"] is True, meta

route, meta = proof.derive_observed_route(
    {
        "url": "https://example.invalid/anime/93-jujutsu-kaisen-1/saison-1/episode-1.html",
        "final_url": "https://example.invalid/anime/93-jujutsu-kaisen-1/saison-1/episode-1.html",
        "method": "GET",
        "body_kind": "none",
        "body_values": {},
        "proof_headers": {},
    },
    task,
    [
        {"key": "id", "value": "93"},
        {"key": "slug", "value": "93-jujutsu-kaisen-1"},
    ],
)
assert route == "/anime/{slug}/saison-1/episode-1.html" or route == "/anime/{slug}/saison-{season}/episode-{episode}.html", (route, meta)
assert meta["providerValueCorrelation"] is True, meta
assert "{slug}" in route, route

route, meta = proof.derive_observed_route(
    {
        "url": "https://example.invalid/?trembed=0&trid=48062&trtype=2",
        "final_url": "https://example.invalid/?trembed=0&trid=48062&trtype=2",
        "method": "GET",
        "body_kind": "none",
        "body_values": {},
        "proof_headers": {},
    },
    task,
    [{"key": "trid", "value": "48062"}],
)
assert route == "/?trembed=0&trid={id}&trtype=2", (route, meta)
assert meta["providerValueCorrelation"] is True, meta

assert proof.response_value_hints({
    "response_value_hints": [
        {"key": "token", "value": "abcdef123456"},
        {"key": "expiry", "value": "1999999999"},
        {"key": "slug", "value": "safe-catalogue-value"},
    ]
}) == [{"key": "slug", "value": "safe-catalogue-value"}]

imdb_fixture = dict(fixture)
imdb_fixture["imdbId"] = "tt12345678"
imdb_route, imdb_meta = proof.derive_observed_route(
    {
        "url": "https://example.invalid/series/tt12345678",
        "final_url": "https://example.invalid/series/tt12345678",
        "method": "GET",
        "body_kind": "none",
        "body_values": {},
        "proof_headers": {},
    },
    {"fixture": imdb_fixture},
    [{"key": "id", "value": "tt12345678"}],
)
assert imdb_route == "/series/{imdbId}", (imdb_route, imdb_meta)
assert imdb_meta.get("externalIdentityCorrelation") is True, imdb_meta

base_text = (ROOT / "scripts" / "provider_base_store.py").read_text(encoding="utf-8")
worker_text = (ROOT / "scripts" / "provider_worker.cjs").read_text(encoding="utf-8")
recovery_text = (ROOT / "scripts" / "recover_provider_routes_from_upstreams.py").read_text(encoding="utf-8")
materializer_text = (ROOT / "scripts" / "materialize_provider_v3_all.py").read_text(encoding="utf-8")

assert "function _spv20ProviderValuesFromHtml" in base_text
assert "NIAKVIO_PROVIDER_RESPONSE_VALUE_CORRELATION_V20_2" in base_text
assert "providerSlug: providerValues.slug || providerValues.id || providerId" in base_text
assert "/\\{(?:id|slug)\\}/i.test(stepRoute)" in base_text
assert "/episode/[^?#/]*-(?:saison-)?0*" in base_text
assert "NUVIO_PROVIDER_RESPONSE_VALUE_CORRELATION_V20" in worker_text
assert "ROUTE_RECOVERY_RESPONSE_VALUE_CORRELATION_V20" in recovery_text
assert "PROVIDER_RESPONSE_VALUE_CORRELATION_V20" in materializer_text

# V18.4 JSON-text decoding and its sanitized trace must survive V20.2.
assert "NIAKVIO_PROVIDER_CORRELATED_VALUE_JSON_TEXT_V18_4" in base_text
assert "function _spv184Trace" in base_text
assert "_spv20ProviderValuesFromJson(JSON.parse(rawSearchValue), meta)" in base_text

migration_text = (ROOT / "scripts" / "upgrade_provider_response_value_correlation_v20_2.py").read_text(encoding="utf-8").casefold()
for forbidden in ("animesama", "animevostfr", "french-manga", "movieblast", "animezey", "cineby"):
    assert forbidden not in migration_text, forbidden

print("provider response-value correlation V20.2 tests passed")
