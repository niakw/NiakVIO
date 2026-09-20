#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "build_brain_architecture_proposal.py"

with tempfile.TemporaryDirectory(prefix="niakvio-arch-cohort-") as tmp:
    root = Path(tmp)
    state = root / "state.json"
    policy = root / "policy.json"
    self_config = root / "self.json"
    workflow = root / "workflow.yml"
    targeted = root / "targeted.json"
    queue_summary = root / "queue-summary.json"
    queue_state = root / "queue-state.json"
    batch_plan = root / "batch-plan.json"
    out_policy = root / "policy.proposed.json"
    summary = root / "summary.json"
    markdown = root / "summary.md"

    entries = []
    for provider in ("alpha", "beta"):
        for variant in range(4):
            entries.append({
                "providerId": provider,
                "failureClass": "chain_terminal_gap",
                "signature": "shared-terminal-signature",
                "profile": "adaptive_runtime_recovery",
                "experimentVariant": variant,
                "successes": 0,
                "failures": 1,
                "consecutiveFailures": 1,
            })
    state.write_text(json.dumps({
        "unresolvedFailureCounts": {},
        "proposals": [],
        "experimentMemory": {"entries": entries},
    }), encoding="utf-8")
    allowed = [
        ".github/workflows/brain-learning-lab.yml",
        "engine_v2/config/brain-policy.json",
        "engine_v2/scripts/learning-lab.mjs",
        "engine_v2/src/repair-brain.mjs",
        "scripts/build_brain_architecture_proposal.py",
        "scripts/run_brain_learning_sandbox.py",
        "scripts/brain_repair_runtime.py",
        "scripts/run_brain_learning_queue.py",
        "tests/brain_*",
    ]
    policy.write_text(json.dumps({
        "learningLab": {
            "selfArchitectureAllowedTargets": allowed,
            "coreEvidenceAuthority": "hypothesis_only",
            "targetProvidersPerRun": "time_budgeted_queue",
            "retryPolicy": "deadline-driven",
            "clientSelection": "tv_desktop_mobile",
            "streamSampling": "all_returned_streams",
            "allStreamsSafetyCap": 40,
        }
    }), encoding="utf-8")
    self_config.write_text(json.dumps({
        "autoPatchAllowlist": {},
        "thresholds": {
            "repeatedUnknownFailures": 2,
            "repeatedProfileFailures": 2,
            "routeDiscoveryEmptyEvidence": 1,
        }
    }), encoding="utf-8")
    workflow.write_text(
        "run_brain_learning_queue.py\n"
        "--learning-queue-state\n"
        "publish-architecture-proposal:\n"
        "--stream-safety-cap 40\n",
        encoding="utf-8",
    )
    targeted.write_text(json.dumps({"providers": []}), encoding="utf-8")
    queue_summary.write_text(json.dumps({
        "processedProviderCount": 2,
        "deferredRepairProviders": ["alpha", "beta"],
        "results": [],
    }), encoding="utf-8")
    queue_state.write_text(json.dumps({
        "remainingProviderCount": 2,
        "deferredRepairProviders": ["alpha", "beta"],
    }), encoding="utf-8")

    batch_plan.write_text(json.dumps({
        "sourceRunId": "synthetic",
        "groups": [
            {
                "groupId": "terminal-extraction|html_scraper",
                "repairScope": "terminal-extraction",
                "capabilityStrategy": "html_scraper",
                "runtimeFamilies": ["family-a"],
                "dominantIssues": ["network_zero_result"],
                "providers": ["alpha"],
            },
            {
                "groupId": "transport|mixed_embed_resolver",
                "repairScope": "transport",
                "capabilityStrategy": "mixed_embed_resolver",
                "runtimeFamilies": ["family-b"],
                "dominantIssues": ["network_http_error"],
                "providers": ["beta"],
            },
            {
                "groupId": "harness-compatibility|html_scraper",
                "repairScope": "harness-compatibility",
                "capabilityStrategy": "html_scraper",
                "providers": ["not-deferred"],
            },
        ],
    }), encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--learning-state", str(state),
            "--policy", str(policy),
            "--self-config", str(self_config),
            "--workflow", str(workflow),
            "--targeted-lab", str(targeted),
            "--queue-summary", str(queue_summary),
            "--queue-state", str(queue_state),
            "--batch-plan", str(batch_plan),
            "--output-policy", str(out_policy),
            "--summary", str(summary),
            "--markdown", str(markdown),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
        timeout=20,
    )
    result = json.loads(summary.read_text(encoding="utf-8"))
    cohort = [
        row for row in result.get("proposals") or []
        if row.get("evolutionKind") == "repair_strategy_exhaustion_cohort"
    ]
    assert len(cohort) == 1, result
    row = cohort[0]
    assert row["priority"] == "critical", row
    assert row["evidence"]["deferredProviderCount"] == 2, row
    assert row["evidence"]["providers"] == ["alpha", "beta"], row
    assert row["evidence"]["failureCohorts"]["chain_terminal_gap"] == ["alpha", "beta"], row
    assert row["evidence"]["failedProfileCohorts"]["adaptive_runtime_recovery"] == ["alpha", "beta"], row
    assert row["evidence"]["repeatedSignatureCount"] == 1, row
    assert "engine_v2/src/repair-brain.mjs" in row["targets"], row
    assert result["deferredRepairProviderCount"] == 2, result
    assert result["deferredRepairProviders"] == ["alpha", "beta"], result
    assert "do not recycle v0-v3" in row["recommendation"].casefold(), row
    assert "requiresHumanMerge" in row and row["requiresHumanMerge"] is True, row
    blueprints = result["strategyBlueprints"]
    assert result["strategyBlueprintCount"] == 2, result
    assert {item["strategyId"] for item in blueprints} == {
        "chain_terminal_extractor_v1",
        "native_transport_differential_v1",
    }, blueprints
    terminal = next(item for item in blueprints if item["strategyId"] == "chain_terminal_extractor_v1")
    assert terminal["providers"] == ["alpha"], terminal
    assert "playback-verified media" in terminal["acceptanceProof"], terminal
    transport = next(item for item in blueprints if item["strategyId"] == "native_transport_differential_v1")
    assert transport["providers"] == ["beta"], transport
    assert "representative native TV/mobile" in transport["method"], transport
    assert "provider mutation only after harness mismatch excluded" in transport["acceptanceProof"], transport
    assert all(item["productionWritesAllowed"] is False for item in blueprints)
    assert all(item["requiresHumanMerge"] is True for item in blueprints)
    assert row["evidence"]["strategyBlueprints"] == blueprints, row

print("Brain architecture deferred repair cohort contract passed")
