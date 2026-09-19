#!/usr/bin/env python3
from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import rotating_corpus as corpus  # noqa: E402

DATA = json.loads((ROOT / ".github/triggers/rotating-popular-corpus.json").read_text(encoding="utf-8"))
MAX_YEAR = dt.datetime.now(dt.timezone.utc).year - 1

assert int(DATA.get("schema_version") or 0) == 2
assert set(DATA.get("lists") or {}) == {"movie", "tv", "anime"}
selection = DATA.get("selection") or {}
assert selection.get("global_lists") == ["movie", "tv", "anime"]
assert selection.get("initial_per_lane") == 1
assert selection.get("clean_miss_action") == "same_lane_next_random_candidate"
assert selection.get("technical_error_action") == "stop_and_report"
assert selection.get("identity_contradiction_action") == "stop_and_report"
assert selection.get("fixed_batch_size") is None

for lane in corpus.LANES:
    rows = corpus.fixtures_by_lane(lane)
    assert len(rows) >= 20, (lane, len(rows))
    assert len({row["slug"] for row in rows}) == len(rows)
    assert len({str(row["tmdbId"]) for row in rows}) == len(rows)
    for row in rows:
        assert row["lane"] == lane
        assert 2010 <= int(row["year"]) <= MAX_YEAR, row
        if lane == "movie":
            assert row["mediaType"] == "movie"
            assert row.get("season") is None and row.get("episode") is None
        else:
            assert int(row.get("season") or 0) >= 1
            assert int(row.get("episode") or 0) >= 1

# One title per lane is the default. The corpus is a reserve, not a fixed batch.
selected = []
for lane in corpus.LANES:
    rows = corpus.select_fixtures(lane, seed="policy", count=1)
    assert len(rows) == 1
    selected.extend(rows)
assert len(selected) == 3

# Deterministic seeded randomness remains reproducible but can differ per provider.
a = [row["slug"] for row in corpus.rotated_candidates("movie", seed="stable", provider="alpha")]
b = [row["slug"] for row in corpus.rotated_candidates("movie", seed="stable", provider="alpha")]
c = [row["slug"] for row in corpus.rotated_candidates("movie", seed="stable", provider="beta")]
assert a == b
assert a != c

assert corpus.classify_outcome(runtime_ok=True, stream_count=0) == "catalog_miss"
assert corpus.classify_outcome(runtime_ok=True, stream_count=1) == "positive"
assert corpus.classify_outcome(runtime_ok=False, stream_count=0) == "technical_error"
assert corpus.classify_outcome(runtime_ok=True, stream_count=0, runtime_error=True) == "technical_error"
assert corpus.classify_outcome(runtime_ok=True, stream_count=0, contradiction=True) == "identity_contradiction"

# Historical regression fixtures can still be addressed explicitly without
# contaminating the recent global pools.
assert corpus.fixture_by_slug("breaking-bad-s01e01")["year"] == 2008
assert all(row["slug"] != "breaking-bad-s01e01" for row in corpus.fixtures_by_lane("tv"))

print(
    "RECENT_GLOBAL_LAB_CORPUS_POLICY_OK "
    + " ".join(f"{lane}={len(corpus.fixtures_by_lane(lane))}" for lane in corpus.LANES)
    + f" years=2010-{MAX_YEAR} initial_per_lane=1 clean_miss_rotation=true"
)
