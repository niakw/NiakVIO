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
    # The cleanup's source anchor must match the already-proven shared-TMDB Core.
    if OLD_SOURCE not in text:
        raise AssertionError("historical cleanup source revision anchor missing")
    text = text.replace(OLD_SOURCE, SHARED_SOURCE)
    # Preserve the zero-episodic-year semantic upgrade under a revision that also
    # records the shared TMDB/network owner contract.
    text = text.replace(OLD_TARGET, COMBINED_TARGET)
    CLEANUP.write_text(text, encoding="utf-8")

value = CLEANUP.read_text(encoding="utf-8")
for needle in (SHARED_SOURCE, COMBINED_TARGET):
    if needle not in value:
        raise AssertionError(needle)

# Tests introduced at different points in the migration history may already name
# either predecessor revision. Align only revision labels; their semantic
# assertions remain untouched and still prove the actual movie/TV behavior.
for rel in (
    "tests/global_stream_identity_test.py",
    "tests/episodic_year_identity_regression_test.py",
):
    path = ROOT / rel
    if not path.exists():
        continue
    test = path.read_text(encoding="utf-8")
    test = test.replace(SHARED_SOURCE, COMBINED_TARGET).replace(OLD_TARGET, COMBINED_TARGET)
    path.write_text(test, encoding="utf-8")

print("IDENTITY_CLEANUP_SHARED_OWNER_PREPATCH_OK revision=" + COMBINED_TARGET)
