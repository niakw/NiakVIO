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


# V3 owns the terminal-verifying worker wrapper locally. Patch that boundary,
# not the older parity module's raw worker, so this unit test cannot accidentally
# hit the filesystem/network when the harness implementation evolves.
parity._run_verified = fake_worker
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
# Clean 0/0 costs two calls; the asymmetric positive is reverse-confirmed and
# therefore costs four calls before it can be called a certain regression.
assert len(calls) == 6, calls
assert row["samples"][-1]["confirmationClassification"] == "upstream_ok_niakvio_ko", row

# First-request-wins services must never manufacture a regression. The reverse
# order proves that both implementations can produce terminal media, so the
# lane is positive-but-flaky instead of upstream_ok_niakvio_ko.
parity.select_fixtures = lambda *args, **kwargs: [fixtures[1]]
flaky_calls = 0
def first_request_wins(path, fixture, timeout):
    global flaky_calls
    flaky_calls += 1
    return result(1 if flaky_calls % 2 else 0)
parity._run_verified = first_request_wins
flaky = parity.run_lane(
    "demo",
    "movie",
    Path("local.js"),
    Path("upstream.js"),
    timeout=10,
    sample_count=1,
    seed="seed",
)
assert flaky["status"] == "POSITIVE", flaky
assert flaky["samples"][0]["classification"] == "both_ok_flaky", flaky
assert flaky["samples"][0]["confirmation"] is not None, flaky
assert flaky_calls == 4, flaky_calls

# If every sampled work is a clean 0/0, the lane is RESAMPLE, never ZERO.
parity.select_fixtures = lambda *args, **kwargs: fixtures
parity._run_verified = lambda *args, **kwargs: result(0)
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
