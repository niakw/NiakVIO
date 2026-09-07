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

# The migration must preserve the strict identity ordering: provider catalogue
# identity is proven before external player traversal, and direct media remains
# the terminal proof inside the bounded crawler.
for marker in (
    "NIAKVIO_PROVIDER_SOURCE_PLAN_V15",
    "function _spv15ExplicitPlayerAttrs",
    "function _spv15ArticleDetails",
    "rows.push(..._spv15ArticleDetails",
    "...explicitPlayers",
    "if (!providerOrigin && /^\\/e\\/",
):
    assert marker in migration, marker

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
