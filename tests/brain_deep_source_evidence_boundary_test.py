#!/usr/bin/env python3
"""Deep's actual stage bytes must reach the canonical Brain planner.

Use provider-owned code as an oracle, not a synthetic provider patch. The test
does not claim player/media success and cannot publish provider bytes.
"""
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import run_adaptive_deep_repair as deep
import brain_repair_runtime as brain

spec = importlib.util.spec_from_file_location(
    "source_oracle", ROOT / "scripts/provider_patches/4khdhub_runtime_v1.py")
assert spec and spec.loader
source_oracle = importlib.util.module_from_spec(spec)
spec.loader.exec_module(source_oracle)

source = source_oracle.WRAPPER.replace("CONFIG_PLACEHOLDER", json.dumps({
    "base": "https://provider.example", "maxStreams": 8, "ua": "test"}))
with tempfile.TemporaryDirectory(prefix="brain-deep-source-boundary-") as directory:
    stage = Path(directory) / "stage"
    output = Path(directory) / "output"
    provider = stage / "providers" / "source-oracle.js"
    provider.parent.mkdir(parents=True)
    provider.write_text(source, encoding="utf-8")
    key = "published:source-oracle"
    registry = stage / "candidates.json"
    registry.write_text(json.dumps({"candidates": [{
        "key": key, "canonical_id": "source-oracle",
        "local_path": "providers/source-oracle.js",
        "metadata": {"supportedTypes": ["movie", "tv"]},
    }]}))
    result = {
        "key": key, "status": "no_streams",
        "tests": [{"status": "no_streams",
                   "fixture": {"category": "movie", "mediaType": "movie"},
                   "network_observations": [{"status": 200, "ok": True,
                                              "stage": "search"}]}],
    }
    report = {"results": [result]}
    observed = []
    def bridge(registry_path, current_report, mode, *, stage=None):
        assert registry_path == registry and current_report == report
        assert mode == "deep"
        signal = brain._current_source_structural_repair_evidence(
            stage, {"local_path": "providers/source-oracle.js"}, result)
        observed.append(signal)
        return {}

    with patch.object(deep, "_base_run_health", return_value=report), \
         patch.object(deep.brain, "update_plans", side_effect=bridge), \
         patch.object(deep, "_HARNESS_DIFFERENTIAL_AUDITED", True):
        checked = deep._brain_run_health(
            stage=stage, registry_path=registry, output_dir=output, mode="deep")
    assert checked == report
    assert len(observed) == 1, observed
    assert observed[0]["source"] == "current_candidate_bytes", observed
    assert observed[0]["profile"] == "html_class_token_exact_v1", observed
    assert observed[0]["diagnosticOnly"] is True
    assert observed[0]["proofAuthority"] is False

    # The real adaptive transport is what production Deep imports, not the
    # canonical helper in isolation. Its batch must receive the exact source
    # signal before the Node planner is invoked. A mocked update_plans above
    # would miss the adapter-signature regression seen in run 42801267351.
    adaptive_batches = []
    def adaptive_batch(base_payload, items):
        assert base_payload["mode"] == "deep"
        adaptive_batches.extend(items)
        return {key: {"action": "collect-more-evidence", "allowedProfiles": []}}

    with patch.object(deep, "_base_run_health", return_value=report), \
         patch.object(deep.brain, "_run_planner_batch", side_effect=adaptive_batch), \
         patch.object(deep, "_HARNESS_DIFFERENTIAL_AUDITED", True):
        checked = deep._brain_run_health(
            stage=stage, registry_path=registry, output_dir=output, mode="deep")
    assert checked == report
    assert len(adaptive_batches) == 1
    forwarded = adaptive_batches[0]["candidate"]["structuralRepairEvidence"]
    assert forwarded["profile"] == "html_class_token_exact_v1", forwarded
    assert forwarded["sourceSha256"] == observed[0]["sourceSha256"], forwarded
    assert forwarded["diagnosticOnly"] and forwarded["proofAuthority"] is False

    # Negative control: blocked transport must NOT authorize a source-repair
    # inference just because the JS source contains a known structural marker.
    blocked = {"results": [{**result, "status": "blocked"}]}
    adaptive_batches.clear()
    with patch.object(deep.brain, "_run_planner_batch", side_effect=adaptive_batch):
        deep.brain.update_plans(registry, blocked, "deep", stage=stage)
    assert adaptive_batches and "structuralRepairEvidence" not in adaptive_batches[0]["candidate"]

print("BRAIN_DEEP_SOURCE_BOUNDARY_OK stage_current_bytes_reached_planner=true "
      "independent_validation_still_required=true publication_authority=false")
