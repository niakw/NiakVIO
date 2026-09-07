#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
migration = (ROOT / "scripts" / "upgrade_provider_search_request_plan_v14_1.py").read_text(encoding="utf-8")
recovery = (ROOT / "scripts" / "recover_provider_routes_from_upstreams.py").read_text(encoding="utf-8")
base = (ROOT / "scripts" / "provider_base_store.py").read_text(encoding="utf-8")

# The migration must stay provider/domain/fixture agnostic.
for forbidden in (
    "movies4u",
    "animekai",
    "frenchstream",
    "m4uplay",
    "fs23",
    "interstellar",
):
    assert forbidden not in migration.casefold(), forbidden

# Search/detail success is evidence only; only terminal resolver roles may revoke
# stale domain substitutions.
assert 'role not in {"source", "player"}' in recovery
assert "ROUTE_RECOVERY_SEARCH_REQUEST_PLAN_V14_1" in recovery

# Anchor labels can strengthen an already-safe detail URL, but loose overlap and
# explicit movie-year conflicts remain fail-closed.
for marker in (
    "NIAKVIO_PROVIDER_SEARCH_REQUEST_PLAN_V14_1",
    "function _spv14LabelScoreForUrl",
    "if (score < 90) continue",
    'mediaType === "movie" && expectedYear && observedYear && observedYear !== expectedYear',
    "_spv14LabelScoreForUrl(html, base, url, meta, mediaType, season)",
):
    assert marker in base, marker

# Existing URL eligibility gates remain upstream of scoring.
assert base.index(".filter(_spv4SameProviderOrigin)") < base.index("_spv14LabelScoreForUrl(html, base, url, meta, mediaType, season)")
assert base.index(".filter(_spv7DetailUrlEligible)") < base.index("_spv14LabelScoreForUrl(html, base, url, meta, mediaType, season)")

print("provider search request plan v14.1 contract passed")
