#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
migration = (ROOT / "scripts" / "upgrade_provider_source_plan_v15.py").read_text(encoding="utf-8")
base = (ROOT / "scripts" / "provider_base_store.py").read_text(encoding="utf-8")

# V15 must stay generic. These are current motivating providers/hosts/fixtures,
# never runtime rules.
for forbidden in (
    "animekai",
    "movies4u",
    "frenchstream",
    "mugiwarastream",
    "mugiwara",
    "otakuhg",
    "otakuvid",
    "m4uplay",
    "interstellar",
    "jujutsu",
):
    assert forbidden not in migration.casefold(), forbidden

# V15 closes two systemic gaps: arbitrary UI data-* values cannot become URLs,
# and links from the currently proven search response may use that response's
# origin without promoting it into permanent provider authority.
for marker in (
    "NIAKVIO_PROVIDER_SOURCE_PLAN_V15",
    "function _spv15ExplicitPlayerAttrs",
    "function _spv15ArticleDetails",
    "function _spv4SameProviderOrigin(url, currentBase)",
    "candidate === current",
    "data-(?:src|url|video|embed|player|file|stream|link|href)",
    "_spv4SameProviderOrigin(url, base)",
    "rows.push(..._spv15ArticleDetails",
    "...explicitPlayers",
    "providerOrigin",
):
    assert marker in migration, marker

# The old catch-all data-* extractor was the source of bogus relative URLs such
# as language/tooltip/boolean values. V15 must explicitly remove that behavior.
assert "data-[a-z0-9_:-]+" not in base

# Existing fail-closed gates must remain present in the owned ProviderBase source;
# V15 patches them after earlier migrations rather than replacing their contract.
for marker in (
    "function _spv7DetailUrlEligible",
    "function _directMedia",
    "async function _crawlDirectMedia",
    "function _strictHtmlIdentityOk",
):
    assert marker in base, marker

print("provider source plan v15 contract passed")
