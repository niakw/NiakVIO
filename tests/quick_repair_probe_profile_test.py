#!/usr/bin/env python3
from __future__ import annotations

import copy
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
            "fixture_limit": 1,
            "max_streams_to_probe": 1,
            "probe_best_variant": False,
            "probe_first_segment": False,
            "probe_streams_adaptively": False,
            "verify_fixture_duration_identity": False,
        },
        "deep": {
            "fixture_limit": 1,
            "max_streams_to_probe": 10,
            "probe_best_variant": True,
            "probe_first_segment": True,
            "probe_streams_adaptively": True,
            "fallback_fixture_limit_per_category": 3,
            "minimum_fixture_duration_ratio": 0.55,
            "maximum_fixture_duration_ratio": 1.8,
        },
    }
}
original_deep = copy.deepcopy(config["modes"]["deep"])
module._strengthen_quick_probe(config)
quick = config["modes"]["quick"]

assert quick["fixture_limit"] == 3
assert quick["max_streams_to_probe"] == 2
assert quick["probe_best_variant"] is True
assert quick["probe_first_segment"] is True
assert quick["probe_streams_adaptively"] is True
assert quick["verify_fixture_duration_identity"] is True
assert quick["minimum_fixture_duration_ratio"] == 0.55
assert quick["maximum_fixture_duration_ratio"] == 1.8

assert config["modes"]["deep"] == original_deep
assert config["modes"]["deep"]["max_streams_to_probe"] == 10
assert config["modes"]["deep"]["fallback_fixture_limit_per_category"] == 3

source = path.read_text(encoding="utf-8")
assert 'mode="quick"' in source
assert 'modes["deep"] = copy.deepcopy(quick)' not in source

print("quick repair probe profile test passed")
