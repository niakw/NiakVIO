#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
upgrade_path = ROOT / "scripts" / "upgrade_provider_search_request_plan_v14.py"
upgrade = upgrade_path.read_text(encoding="utf-8")

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

# The current ProviderBase has evolved beyond the literal V14 early return:
# eight correlated details are resolved individually, then the same bounded
# set is crawled and accumulated under the global 40-stream cap. The V14
# migration validator must accept this stronger form, but fail closed if the
# bounded crawl disappears.
spec = importlib.util.spec_from_file_location("provider_search_plan_v14", upgrade_path)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
current_base = (ROOT / "scripts" / "provider_base_store.py").read_text(encoding="utf-8")
module.validate_base(current_base)

broken = current_base.replace(
    "_crawlDirectMedia(boundedDetails, payload.base || url, 3)",
    "_crawlDirectMedia([], payload.base || url, 3)",
    1,
)
assert broken != current_base
try:
    module.validate_base(broken)
except AssertionError as exc:
    assert "bounded detail crawl missing" in str(exc), exc
else:
    raise AssertionError("V14 validator accepted a ProviderBase without bounded detail crawl")

print("provider search request plan V14 generic contract passed")
