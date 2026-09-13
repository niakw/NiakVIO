#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts" / "rotating_corpus.py"
spec = importlib.util.spec_from_file_location("rotating_corpus", MODULE)
assert spec and spec.loader
rotation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rotation)

rows = rotation.all_fixtures()
assert len(rows) >= 30, len(rows)
for lane in rotation.LANES:
    lane_rows = rotation.fixtures_by_lane(lane)
    assert len(lane_rows) >= 10, (lane, len(lane_rows))
    selected_a = rotation.select_fixtures(lane, count=4, seed="run-100", provider="provider-a")
    selected_b = rotation.select_fixtures(lane, count=4, seed="run-100", provider="provider-a")
    selected_next = rotation.select_fixtures(lane, count=4, seed="run-101", provider="provider-a")
    assert [row["slug"] for row in selected_a] == [row["slug"] for row in selected_b]
    assert [row["slug"] for row in selected_a] != [row["slug"] for row in selected_next]
    assert len({row["slug"] for row in selected_a}) == len(selected_a)

assert rotation.classify_outcome(runtime_ok=True, stream_count=0) == "catalog_miss"
assert rotation.classify_outcome(runtime_ok=True, stream_count=1) == "positive"
assert rotation.classify_outcome(runtime_ok=False, stream_count=0) == "technical_error"
assert rotation.classify_outcome(runtime_ok=True, stream_count=0, runtime_error=True) == "technical_error"
assert rotation.classify_outcome(runtime_ok=True, stream_count=1, contradiction=True) == "identity_contradiction"

print("rotating corpus tests passed")
