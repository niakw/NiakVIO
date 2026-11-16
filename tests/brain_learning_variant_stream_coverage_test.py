#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_brain_learning_queue.py"

spec = importlib.util.spec_from_file_location("brain_learning_variant_stream_coverage", SCRIPT)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

assert mod.learning_stream_probe_policy(40, False) == (2, False)
assert mod.learning_stream_probe_policy(1, False) == (1, False)
assert mod.learning_stream_probe_policy(40, True) == (40, True)
assert mod.learning_stream_probe_policy(100, True) == (40, True)

assert mod.requires_full_variant_probe({"failureClass": "variant_coverage_gap"}) is True
assert mod.requires_full_variant_probe({"groupId": "variant-coverage|mixed_embed_resolver"}) is True
assert mod.requires_full_variant_probe({"observedPipelineStage": "variant-coverage"}) is True
assert mod.requires_full_variant_probe({"failureClass": "provider_network_zero_result"}) is False
assert mod.requires_full_variant_probe(None) is False

source = SCRIPT.read_text(encoding="utf-8")
assert '"max_streams_per_runtime": stream_probe_cap' in source
assert '"probe_all_streams": probe_all_streams' in source
assert '"all_streams_safety_cap": stream_probe_cap if probe_all_streams else 40' in source
assert 'summary["variantCoverageProbe"] = bool(full_variant_probe)' in source
assert 'requires_full_variant_probe(provider_plan)' in source
assert 'default=40' in source

print("Brain Learning variant stream coverage contract passed")
