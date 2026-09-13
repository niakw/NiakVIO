#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

spec = importlib.util.spec_from_file_location(
    "provider_upstream_parity_v3",
    ROOT / "scripts/run_provider_upstream_parity_v3.py",
)
assert spec and spec.loader
parity = importlib.util.module_from_spec(spec)
spec.loader.exec_module(parity)

scope = parity.scope_ids(ROOT / "automation/evidence/hub-lab-matrix-46.json")
assert len(scope) == 46, len(scope)


def result(streams: int = 0, *, timeout: bool = False, error: str | None = None, statuses=None):
    return {
        "stream_count": streams,
        "timeout": timeout,
        "error_class": error,
        "http_statuses": list(statuses or []),
    }


assert parity.classify_pair(result(1), result(1)) == "both_ok"
assert parity.classify_pair(result(1), result(0)) == "upstream_ok_niakvio_ko"
assert parity.classify_pair(result(0), result(1)) == "niakvio_ok_upstream_ko"
assert parity.classify_pair(result(0), result(0)) == "catalog_miss_both"
assert parity.classify_pair(result(0), result(0, timeout=True)) == "niakvio_technical_upstream_no_stream"
assert parity.classify_pair(result(0, statuses=[403]), result(0)) == "upstream_technical_niakvio_no_stream"
assert parity.classify_pair(result(0, statuses=[403]), result(0, statuses=[500])) == "both_technical"

# Clean catalogue misses must advance to another fixture; a useful positive result
# stops the lane immediately.
fixtures = [
    {"slug": "a", "tmdbId": "1", "mediaType": "movie", "title": "A"},
    {"slug": "b", "tmdbId": "2", "mediaType": "movie", "title": "B"},
    {"slug": "c", "tmdbId": "3", "mediaType": "movie", "title": "C"},
]
parity.select_fixtures = lambda *args, **kwargs: fixtures
calls: list[str] = []


def fake_worker(path, fixture, timeout):
    calls.append(f"{path.name}:{fixture['tmdbId']}")
    # First work is clean 0/0. Second work proves upstream positive/local zero.
    if fixture["tmdbId"] == "1":
        return result(0)
    if path.name == "upstream.js":
        return result(1)
    return result(0)


parity.parity.run_worker = fake_worker
row = parity.run_lane(
    "demo",
    "movie",
    Path("local.js"),
    Path("upstream.js"),
    timeout=10,
    sample_count=3,
    seed="seed",
)
assert row["status"] == "REGRESSION", row
assert [sample["fixture"] for sample in row["samples"]] == ["a", "b"], row
assert len(calls) == 4, calls

# If every sampled work is a clean 0/0, the lane is RESAMPLE, never ZERO.
parity.parity.run_worker = lambda *args, **kwargs: result(0)
row = parity.run_lane(
    "demo",
    "movie",
    Path("local.js"),
    Path("upstream.js"),
    timeout=10,
    sample_count=3,
    seed="seed",
)
assert row["status"] == "RESAMPLE", row
assert len(row["samples"]) == 3, row

print("provider upstream parity v3 tests passed: scope=46 clean-miss=RESAMPLE")
