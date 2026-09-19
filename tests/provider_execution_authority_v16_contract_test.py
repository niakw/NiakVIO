#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
migration = (ROOT / "scripts" / "upgrade_provider_execution_authority_v16.py").read_text(encoding="utf-8")
base = (ROOT / "scripts" / "provider_base_store.py").read_text(encoding="utf-8")

# V16 is a global execution-order primitive. Motivating providers/hosts/fixtures
# must never become runtime special cases.
for forbidden in (
    "animekai",
    "movies4u",
    "frenchstream",
    "mugiwarastream",
    "mugiwara",
    "m4uplay",
    "anikai",
    "interstellar",
    "jujutsu",
):
    assert forbidden not in migration.casefold(), forbidden

for marker in (
    "NIAKVIO_PROVIDER_EXECUTION_AUTHORITY_V16",
    "hasProofRecipe",
    "hasProofSearch",
    "_resolveApiRecipe(proofMeta, type, season, episode)",
    "_resolveSearchRequestPlan(proofMeta, type, season, episode)",
    "explicitCrawled",
):
    assert marker in migration, marker

# Pre-existing bounded/fail-closed owners remain in ProviderBase source before
# migrations are applied by the runner; V16 patches rather than replaces them.
for marker in (
    "function _crawlDirectMedia",
    "function _strictHtmlIdentityOk",
    "async function _spv4GetStreams",
):
    assert marker in base, marker

print("provider execution authority V16 contract passed")
