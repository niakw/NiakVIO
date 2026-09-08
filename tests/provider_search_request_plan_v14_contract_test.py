#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
upgrade = (ROOT / "scripts" / "upgrade_provider_search_request_plan_v14.py").read_text(encoding="utf-8")

for needle in (
    "ROUTE_RECOVERY_SEARCH_REQUEST_PLAN_V14",
    "PROVIDER_SEARCH_REQUEST_PLAN_V14",
    "NIAKVIO_PROVIDER_BASE_SEARCH_REQUEST_PLAN_V14",
    "def _positive_search_request_plan",
    "def _positive_proof_hosts",
    'patch[\\"search_request_plan\\"]',
    'model[\\"searchRequestPlan\\"]',
    'patch[\\"proof_protected_hosts\\"]',
    "old not in protected",
    "async function _resolveSearchRequestPlan",
    "searchPlanRequest",
    "_spv4HtmlDetails(payload.value, payload.base, meta, mediaType, season)",
    "_crawlDirectMedia(_uniq(details).slice(0, 8)",
    "flat_route_boundary_preserved=1",
    "provider_specific_rules=0",
):
    assert needle.replace('\\"', '"') in upgrade, needle

# This is a portfolio-level migration. Provider ids, domains and test fixture titles
# must never be the mechanism by which it repairs one site.
for forbidden in (
    "movies4u",
    "m4uplay",
    "animekai",
    "papadustream",
    "frenchstream",
    "interstellar",
    "jujutsu",
    "breaking bad",
):
    assert forbidden not in upgrade.casefold(), forbidden

print("provider search request plan V14 generic contract passed")
