#!/usr/bin/env python3
"""Bridge the historical zero-episodic-year cleanup onto the shared-TMDB owner Core.

The identity ownership cleanup predates the runtime TMDB-owner consolidation. This
pre-migrator keeps both contracts: STREAM_IDENTITY remains a client of the shared
Core TMDB capability, while episodic year becomes completely inert, including the
contentLike heuristic. It only adapts migration/test revision anchors; product
semantics are still applied by apply_core_identity_ownership_cleanup.py.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLEANUP = ROOT / "scripts/apply_core_identity_ownership_cleanup.py"
OLD_SOURCE = "cross-client-shared-catalogue-policy-movie-year-only-v9"
SHARED_SOURCE = "cross-client-shared-tmdb-owner-movie-year-only-v10"
OLD_TARGET = "cross-client-shared-catalogue-policy-zero-episodic-year-v10"
COMBINED_TARGET = "cross-client-shared-tmdb-owner-zero-episodic-year-v11"

text = CLEANUP.read_text(encoding="utf-8")
if COMBINED_TARGET not in text:
    # The cleanup's product-source anchor must match the already-proven shared
    # TMDB owner. The historical test-rewrite source may differ, so tests are
    # normalized explicitly below instead of relying on that old one-shot label.
    product_anchor = (
        '\"implementationRevision\": \"' + OLD_SOURCE + '\",'
    )
    shared_anchor = (
        '\"implementationRevision\": \"' + SHARED_SOURCE + '\",'
    )
    if product_anchor not in text:
        raise AssertionError("historical cleanup product revision anchor missing")
    text = text.replace(product_anchor, shared_anchor, 1)
    text = text.replace(OLD_TARGET, COMBINED_TARGET)
    CLEANUP.write_text(text, encoding="utf-8")

value = CLEANUP.read_text(encoding="utf-8")
for needle in (SHARED_SOURCE, COMBINED_TARGET):
    if needle not in value:
        raise AssertionError(needle)

# Tests were added across three identity revisions. Revision names are metadata,
# while their behavioral assertions are the authority. Normalize every known
# identity-policy regression test to the combined revision without weakening any
# movie/TV/type/title assertion.
for rel in (
    "tests/global_stream_identity_test.py",
    "tests/global_identity_policy_ownership_test.py",
    "tests/priority_tv_year_domain_refresh_test.py",
    "tests/episodic_year_identity_regression_test.py",
):
    path = ROOT / rel
    if not path.exists():
        continue
    test = path.read_text(encoding="utf-8")
    for predecessor in (OLD_SOURCE, SHARED_SOURCE, OLD_TARGET):
        test = test.replace(predecessor, COMBINED_TARGET)
    path.write_text(test, encoding="utf-8")

print("IDENTITY_CLEANUP_SHARED_OWNER_PREPATCH_OK revision=" + COMBINED_TARGET)
