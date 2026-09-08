#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import provider_route_proof as proof  # noqa: E402
import upgrade_provider_response_value_correlation_v20 as v20  # noqa: E402


# The migration must be idempotent and all owners must retain the V20 contract.
v20.main()
v20.main()


fixture = {
    "tmdbId": "95479",
    "mediaType": "anime",
    "title": "Jujutsu Kaisen",
    "year": 2020,
    "season": 1,
    "episode": 1,
}
task = {"fixture": fixture}

# Numeric provider id observed in a prior response may feed an arbitrary safe
# provider query parameter. The request, not the parameter name, proves dataflow.
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

# A composite catalogue slug obtained from an HTML href remains distinct from
# the numeric provider id and can carry season/episode identity downstream.
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

# Query values embedded in a prior HTML iframe may be correlated even when the
# site's field is not literally named id; fixed control values remain literal.
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

# Authentication/expiry/session values are never promoted from response hints.
assert proof.response_value_hints({
    "response_value_hints": [
        {"key": "token", "value": "abcdef123456"},
        {"key": "expiry", "value": "1999999999"},
        {"key": "slug", "value": "safe-catalogue-value"},
    ]
}) == [{"key": "slug", "value": "safe-catalogue-value"}]

base_text = (ROOT / "scripts" / "provider_base_store.py").read_text(encoding="utf-8")
worker_text = (ROOT / "scripts" / "provider_worker.cjs").read_text(encoding="utf-8")
recovery_text = (ROOT / "scripts" / "recover_provider_routes_from_upstreams.py").read_text(encoding="utf-8")
materializer_text = (ROOT / "scripts" / "materialize_provider_v3_all.py").read_text(encoding="utf-8")

assert "function _spv20ProviderValuesFromHtml" in base_text
assert "providerSlug: providerValues.slug || providerValues.id" in base_text
assert "/episode/[^?#/]*-(?:saison-)?0*" in base_text
assert "NUVIO_PROVIDER_RESPONSE_VALUE_CORRELATION_V20" in worker_text
assert "ROUTE_RECOVERY_RESPONSE_VALUE_CORRELATION_V20" in recovery_text
assert "PROVIDER_RESPONSE_VALUE_CORRELATION_V20" in materializer_text

# The common migration must remain provider-agnostic.
migration_text = (ROOT / "scripts" / "upgrade_provider_response_value_correlation_v20.py").read_text(encoding="utf-8").casefold()
for forbidden in ("animesama", "animevostfr", "french-manga", "movieblast", "animezey", "cineby"):
    assert forbidden not in migration_text, forbidden

print("provider response-value correlation V20 tests passed")
