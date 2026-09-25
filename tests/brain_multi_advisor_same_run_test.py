#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_provider_brain_repair.py"
spec = importlib.util.spec_from_file_location("provider_brain", SCRIPT)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)

with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    guidance = tmp / "guidance.json"
    memory = tmp / "memory.json"
    rows = [{
        "providerId": "mallumv",
        "failureClass": "chain_terminal_gap",
        "targetLayer": "provider",
        "strategy": "terminal_media_extractor_with_playback_validation",
        "profile": "chain_terminal_extractor_v1",
        "confidence": 0.96,
        "priorOnly": True,
        "experiment": {"maxDepth": index},
        "experimentFingerprint": fp,
    } for index, fp in enumerate(("a"*64, "b"*64, "c"*64), start=1)]
    guidance.write_text(json.dumps({"rows": rows}), encoding="utf-8")

    assert mod.advisor_wave_budget(["mallumv"], guidance) == 3
    assert mod.advisor_wave_budget(["missing"], guidance) == 1

    original_memory = mod.REPAIR_MEMORY
    mod.REPAIR_MEMORY = memory
    try:
        memory.write_text(json.dumps({"entries": [{
            "providerId": "mallumv",
            "profile": "chain_terminal_extractor_v1",
            "llmAdvisorExperimentFingerprint": "a"*64,
            "consecutiveFailures": 1,
        }]}), encoding="utf-8")
        remaining = mod.untried_advisor_fingerprints(["mallumv"], guidance)
        assert remaining["mallumv"] == {
            ("chain_terminal_extractor_v1", "b"*64),
            ("chain_terminal_extractor_v1", "c"*64),
        }, remaining

        memory.write_text(json.dumps({"entries": [
            {
                "providerId": "mallumv",
                "profile": "chain_terminal_extractor_v1",
                "llmAdvisorExperimentFingerprint": "a"*64,
                "consecutiveFailures": 1,
            },
            {
                "providerId": "mallumv",
                "profile": "chain_terminal_extractor_v1",
                "llmAdvisorExperimentFingerprint": "b"*64,
                "consecutiveFailures": 1,
            },
        ]}), encoding="utf-8")
        remaining = mod.untried_advisor_fingerprints(["mallumv"], guidance)
        assert remaining["mallumv"] == {
            ("chain_terminal_extractor_v1", "c"*64),
        }, remaining

        memory.write_text(json.dumps({"entries": [
            {
                "providerId": "mallumv",
                "profile": "chain_terminal_extractor_v1",
                "llmAdvisorExperimentFingerprint": fp,
                "consecutiveFailures": 1,
            } for fp in ("a"*64, "b"*64, "c"*64)
        ]}), encoding="utf-8")
        assert mod.untried_advisor_fingerprints(["mallumv"], guidance) == {}
    finally:
        mod.REPAIR_MEMORY = original_memory

source = SCRIPT.read_text(encoding="utf-8")
assert "FIELD_PROVIDER_BRAIN_ADVISOR_ROTATION" in source
assert "waves = max(requested_waves, advisor_hypotheses)" in source
assert "advisor_rotation_pending" in source
assert "deferred.difference_update(advisor_rotation_pending)" in source
assert 'decision = "rotate"' in source
assert '"advisorHypothesisWaveBudget": advisor_hypotheses' in source

print("Brain same-run multi-advisor rotation contract passed")
