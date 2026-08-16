#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "scripts" / "run_adaptive_quick_repair.py"
spec = importlib.util.spec_from_file_location("run_adaptive_quick_repair", path)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)

config = {
    "modes": {
        "quick": {
            "fixtures": [
                {"category": "movie", "tmdbId": "1"},
                {"category": "tv", "tmdbId": "2", "season": 1, "episode": 1},
            ],
            "max_streams_to_probe": 1,
            "probe_first_segment": False,
            "verify_fixture_duration_identity": False,
        },
        "deep": {
            "fixtures": [
                {"category": "movie", "tmdbId": "1"},
                {"category": "tv", "tmdbId": "2", "season": 1, "episode": 1},
                {"category": "anime", "tmdbId": "3", "season": 1, "episode": 1},
            ],
            "max_streams_to_probe": 10,
            "fallback_fixture_limit_per_category": 3,
            "minimum_fixture_duration_ratio": 0.55,
            "maximum_fixture_duration_ratio": 1.8,
        },
    }
}

module._strengthen_quick_probe(config)
quick = config["modes"]["quick"]
deep_runtime_slot = config["modes"]["deep"]
categories = [row["category"] for row in quick["fixtures"]]
assert categories.count("movie") == 1
assert categories.count("tv") == 1
assert categories.count("anime") == 1
assert quick["max_streams_to_probe"] == 2
assert quick["probe_best_variant"] is True
assert quick["probe_first_segment"] is True
assert quick["probe_streams_adaptively"] is True
assert quick["fixture_limit_per_category"] is True
assert quick["fallback_fixture_limit_per_category"] == 1
assert quick["verify_fixture_duration_identity"] is True
assert quick["minimum_fixture_duration_ratio"] == 0.55
assert quick["maximum_fixture_duration_ratio"] == 1.8

# The health harness currently activates per-category fixture selection/fallback
# only for requestedMode=deep. Routine repair therefore executes that selector
# through a temporary deep slot which must be exactly the bounded quick profile,
# not the ordinary expensive deep configuration. One alternate per category is
# intentional: enough to distinguish a catalogue miss from structural failure,
# while deep retains the broader three-fallback authority.
assert deep_runtime_slot == quick
assert deep_runtime_slot["max_streams_to_probe"] == 2
assert deep_runtime_slot["fallback_fixture_limit_per_category"] == 1

print("quick repair probe profile test passed")
