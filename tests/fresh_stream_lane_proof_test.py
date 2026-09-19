#!/usr/bin/env python3
from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from finalize_provider_repair_disposition_v1_impl import apply_current_stream_proof

statuses = defaultdict(lambda: defaultdict(set))
statuses["vidlove"]["movie"].add("playable_verified")
statuses["vidlove"]["tv"].add("playable_verified")
fresh = {
    "schemaVersion": 2,
    "laneProofs": {
        "movie": {"streamPositive": False},
        "tv": {"streamPositive": True},
    },
}
current = apply_current_stream_proof(
    "vidlove",
    {"movie", "tv"},
    {"movie", "tv"},
    statuses,
    fresh,
)
assert current == {"tv"}, current
assert "playable_verified" not in statuses["vidlove"]["movie"]
assert "fresh_identity_safe_positive_required" in statuses["vidlove"]["movie"]
assert "playable_verified" in statuses["vidlove"]["tv"]
assert "fresh_stream_positive" in statuses["vidlove"]["tv"]

legacy_statuses = defaultdict(lambda: defaultdict(set))
legacy_statuses["allwish"]["movie"].add("playable_verified")
legacy_statuses["allwish"]["tv"].add("playable_verified")
legacy = {
    "schemaVersion": 1,
    "streamPositive": False,
    "requiresFreshIdentitySafePositive": True,
}
current = apply_current_stream_proof(
    "allwish",
    {"movie", "tv"},
    {"movie", "tv"},
    legacy_statuses,
    legacy,
)
assert current == set(), current
assert "playable_verified" not in legacy_statuses["allwish"]["movie"]
assert "playable_verified" not in legacy_statuses["allwish"]["tv"]

unchanged_statuses = defaultdict(lambda: defaultdict(set))
current = apply_current_stream_proof(
    "example",
    {"movie", "tv"},
    {"movie"},
    unchanged_statuses,
    {},
)
assert current == {"movie"}

print("fresh stream lane proof passed: fresh positives/negatives are lane-scoped and legacy global invalidation remains compatible")
