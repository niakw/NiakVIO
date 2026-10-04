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

with tempfile.TemporaryDirectory() as tmp:
    tmp=Path(tmp)
    memory=tmp/"memory.json"
    original_memory=mod.REPAIR_MEMORY
    mod.REPAIR_MEMORY=memory
    try:
        memory.write_text(json.dumps({"entries":[{
            "providerId":"moviebox",
            "profile":"search_contract_inference_v1",
            "llmAdvisorExperimentFingerprint":"d"*64,
            "consecutiveFailures":1,
            "failures":1,
            "executionObserved":True,
            "lastOutcome":"exploration_progress_nonpublishable",
            "lastReason":"sandbox_diagnostic_progress:provider-requests",
        }]}),encoding="utf-8")
        summary={"plans":{"published:moviebox":{
            "providerId":"moviebox",
            "action":"probe-targeted-repair",
            "llmAdvisorApplied":True,
            "llmAdvisorGuidanceKind":"meta-gap-synthesis",
            "llmAdvisorProfile":"search_contract_inference_v1",
            "llmAdvisorExperimentFingerprint":"d"*64,
        }}}
        assert mod.executed_advisor_rotation_pending(summary)=={"moviebox"}
        for guidance_kind in ("persistent-learning","external-brain-llm"):
            summary["plans"]["published:moviebox"]["llmAdvisorGuidanceKind"]=guidance_kind
            assert mod.executed_advisor_rotation_pending(summary)=={"moviebox"},guidance_kind
        summary["plans"]["published:moviebox"]["llmAdvisorGuidanceKind"]="meta-gap-synthesis"
        memory.write_text(json.dumps({"entries":[{
            "providerId":"moviebox",
            "profile":"search_contract_inference_v1",
            "llmAdvisorExperimentFingerprint":"d"*64,
            "consecutiveFailures":1,
            "failures":1,
            "executionObserved":False,
            "lastOutcome":"profile_unavailable",
            "lastReason":"planned_profile_not_applicable_to_current_bytes",
        }]}),encoding="utf-8")
        assert mod.executed_advisor_rotation_pending(summary)==set()
    finally:
        mod.REPAIR_MEMORY=original_memory

# Scheduler must count the exact meta-gap fingerprints the Node planner will
# execute, not the persisted source fingerprint. This locks the Moviebox case
# that previously produced six empty waves: raw bfe304... remained "untried"
# after all three transport-bound derived experiments had already failed.
with tempfile.TemporaryDirectory() as tmp:
    tmp=Path(tmp)
    guidance=tmp/"meta-guidance.json"
    memory=tmp/"meta-memory.json"
    source_fp="bfe304a6bd72e51555e6f5a67619c4ddd20e857ae745edd6e294a6b46b9d2d76"
    experiment={
        "aliasSearch":True,
        "documentRequestMining":True,
        "maxDepth":5,
        "maxEmbeds":24,
        "maxPages":30,
        "maxRecipePasses":5,
        "recipePolicy":"current_only",
        "responseSalvage":True,
        "roleOrder":["search","detail","api","episode","player","source","other"],
        "routePolicy":"owned_plus_peer",
        "sessionBootstrap":False,
        "terminalOnly":False,
    }
    guidance.write_text(json.dumps({"rows":[{
        "providerId":"moviebox",
        "failureClass":"route_proven_gap",
        "targetLayer":"provider",
        "strategy":"meta_gap_search_contract_fallback",
        "profile":"search_contract_inference_v1",
        "confidence":0.86,
        "priorOnly":True,
        "experiment":experiment,
        "experimentFingerprint":source_fp,
        "guidanceKind":"meta-gap-synthesis",
    }]}),encoding="utf-8")
    original_memory=mod.REPAIR_MEMORY
    mod.REPAIR_MEMORY=memory
    try:
        memory.write_text(json.dumps({"entries":[]}),encoding="utf-8")
        executable=mod.untried_advisor_fingerprints(
            ["moviebox"],guidance,{"moviebox":"transport_blocked"}
        )
        expected={
            ("search_contract_inference_v1","8b609f0c3db58ed1ede14fd6786f5e5e320211270c303c9220f924be6ff826ae"),
            ("search_contract_inference_v1","322d30d3b0b57e86a239e40f1642319033c2a5efd728fd0ae0a3a60a83ba8f39"),
            ("search_contract_inference_v1","1b2df01e169620770748a39980923cde2cca1eaff6b0e6ac0238cea627560cae"),
        }
        assert executable["moviebox"]==expected,executable
        assert all(fp!=source_fp for _profile,fp in executable["moviebox"]),executable

        memory.write_text(json.dumps({"entries":[{
            "providerId":"moviebox",
            "profile":"search_contract_inference_v1",
            "llmAdvisorExperimentFingerprint":fp,
            "consecutiveFailures":1,
            "executionObserved":True,
        } for _profile,fp in sorted(expected)]}),encoding="utf-8")
        assert mod.untried_advisor_fingerprints(
            ["moviebox"],guidance,{"moviebox":"transport_blocked"}
        )=={}
    finally:
        mod.REPAIR_MEMORY=original_memory

source = SCRIPT.read_text(encoding="utf-8")
assert "FIELD_PROVIDER_BRAIN_ADVISOR_ROTATION" in source
assert "FIELD_PROVIDER_BRAIN_ADVISOR_DYNAMIC_EXTENSION" in source
assert "waves = max(requested_waves, advisor_hypotheses)" in source
assert "advisor_dynamic_wave_ceiling = max(requested_waves, 6)" in source
assert "for wave in range(1, advisor_dynamic_wave_ceiling + 1)" in source
assert "if wave > waves or not remaining:" in source
assert "advisor_rotation_this_wave" in source
assert "waves += 1" in source
assert "no_new_repair_experiment" in source
assert "advisor_rotation_pending" in source
assert "_meta_gap_scheduler_fingerprints" in source
assert "advisor_failure_classes" in source
assert "executed_advisor_rotation_pending" in source
assert "dynamic_advisor_rotation" in source
assert "or provider in dynamic_advisor_rotation" in source
assert "deferred.difference_update(advisor_rotation_pending)" in source
assert 'decision = "rotate"' in source
assert '"advisorHypothesisWaveBudget": advisor_hypotheses' in source
assert '"advisorDynamicWaveCeiling": advisor_dynamic_wave_ceiling' in source

print("Brain same-run multi-advisor rotation contract passed")
