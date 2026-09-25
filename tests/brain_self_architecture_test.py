#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "build_brain_architecture_proposal.py"
POLICY = ROOT / "engine_v2" / "config" / "brain-policy.json"
SELF = ROOT / "engine_v2" / "config" / "brain-self-evolution.json"
WORKFLOW = ROOT / ".github" / "workflows" / "brain-learning-lab.yml"

with tempfile.TemporaryDirectory(prefix="brain-self-arch-") as tmp:
    tmp = Path(tmp)
    learning = {
        "unresolvedFailureCounts": {"unknown_failure": 3},
        "experimentMemory": {
            "entries": [
                {"providerId": "demo", "profile": "p1", "successes": 0, "consecutiveFailures": 2},
                {"providerId": "demo", "profile": "p2", "successes": 0, "consecutiveFailures": 2},
                {"providerId": "demo", "profile": "p3", "successes": 0, "consecutiveFailures": 2},
            ]
        },
        "proposals": [],
    }
    lab = {
        "status": "multi_provider",
        "providerId": "demo",
        "providers": [
            {
                "status": "unresolved",
                "providerId": "demo",
                "clients": {
                    "desktop": {
                        "runtimeStreams": 60,
                        "probedStreams": 40,
                        "playableProbes": 30,
                        "unplayableProbes": 10,
                        "inconclusiveProbes": 0,
                        "identityContradictions": 0,
                        "probeCoverageComplete": False,
                        "hiddenFailure": True,
                    }
                },
            }
        ],
    }
    selection = {
        "results": [
            {
                "provider": "demo",
                "coreHypothesis": {"status": "healthy", "needs_route_search": True},
                "routeSearch": {"routeEvidenceCount": 0, "fallbackApplied": 0},
                "finalLab": {"status": "unresolved"},
            }
        ]
    }

    paths = {}
    for name, value in {
        "learning.json": learning,
        "lab.json": lab,
        "selection.json": selection,
        "route.json": {},
        "fallback.json": {},
        "batch.json": {
            "groups": [
                {
                    "groupId": "harness-compatibility|api|browser-profile-only",
                    "repairScope": "harness-compatibility",
                    "capabilityStrategy": "api_stream_resolver",
                    "transportSignature": "browser-profile-only",
                    "providers": ["browser-only"],
                    "runtimeFamilies": ["api"],
                    "dominantIssues": ["waf_challenge"],
                    "harnessTransportClasses": ["browser-profile-only"],
                },
                {
                    "groupId": "harness-compatibility|api|browser-profile-only-both-networks",
                    "repairScope": "harness-compatibility",
                    "capabilityStrategy": "api_stream_resolver",
                    "transportSignature": "browser-profile-only-both-networks",
                    "providers": ["tls-gap"],
                    "runtimeFamilies": ["api"],
                    "dominantIssues": ["network_exception"],
                    "harnessTransportClasses": ["browser-profile-only-both-networks"],
                },
                {
                    "groupId": "harness-compatibility|html|residential-exit-all-challenged",
                    "repairScope": "harness-compatibility",
                    "capabilityStrategy": "html_scraper",
                    "transportSignature": "residential-exit-all-challenged",
                    "providers": ["challenged"],
                    "runtimeFamilies": ["html"],
                    "dominantIssues": ["waf_challenge"],
                    "harnessTransportClasses": ["residential-exit-all-challenged"],
                },
            ]
        },
    }.items():
        path = tmp / name
        path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
        paths[name] = path

    llm_batch = tmp / "llm.jsonl"
    llm_batch.write_text(
        json.dumps({
            "provider": "tls-gap",
            "failure_class": "transport_environment_gap",
            "ok": True,
            "routing": {
                "mode": "llm_diagnose",
                "target_layer": "harness",
                "strategy": "native_tls_browser_differential_v1",
                "prior_confidence": 0.99,
            },
            "proposal": {
                "provider_id": "tls-gap",
                "target_layer": "harness",
                "strategy": "native_tls_browser_differential_v1",
                "confidence": 0.97,
                "mutations": [],
                "abstain": True,
                "diagnosis": "PRIVATE OR RAW MODEL TEXT MUST NOT BE PERSISTED",
            },
        }) + "\n",
        encoding="utf-8",
    )

    proposed = tmp / "policy.json"
    summary = tmp / "summary.json"
    markdown = tmp / "summary.md"

    subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--learning-state", str(paths["learning.json"]),
            "--policy", str(POLICY),
            "--self-config", str(SELF),
            "--workflow", str(WORKFLOW),
            "--targeted-lab", str(paths["lab.json"]),
            "--target-selection", str(paths["selection.json"]),
            "--route-report", str(paths["route.json"]),
            "--route-fallback", str(paths["fallback.json"]),
            "--batch-plan", str(paths["batch.json"]),
            "--llm-batch", str(llm_batch),
            "--output-policy", str(proposed),
            "--summary", str(summary),
            "--markdown", str(markdown),
        ],
        cwd=ROOT,
        check=True,
    )

    data = json.loads(summary.read_text(encoding="utf-8"))
    next_policy = json.loads(proposed.read_text(encoding="utf-8"))

    kinds = {row.get("evolutionKind") for row in data.get("proposals") or []}
    assert "missing_repair_capability" in kinds
    assert "lab_self_limit" in kinds
    assert "core_sampling_blind_spot" in kinds
    assert "route_discovery_blind_spot" in kinds
    assert "method_exhaustion" in kinds
    assert "llm_non_provider_diagnosis" in kinds
    assert data["llmArchitectureGuidanceCount"] == 1
    llm_guidance = data["llmArchitectureGuidance"][0]
    assert llm_guidance["providerId"] == "tls-gap", llm_guidance
    assert llm_guidance["targetLayer"] == "harness", llm_guidance
    assert llm_guidance["strategy"] == "native_tls_browser_differential_v1", llm_guidance
    assert llm_guidance["mutationAuthority"] is False, llm_guidance
    assert "PRIVATE OR RAW MODEL TEXT" not in json.dumps(data), data

    strategies={
        row.get("strategyId"): row
        for row in data.get("strategyBlueprints") or []
        if isinstance(row,dict)
    }
    assert "browser_session_transport_bridge_v1" in strategies, strategies
    assert "native_tls_browser_differential_v1" in strategies, strategies
    assert "persistent_challenge_session_boundary_v1" in strategies, strategies
    assert strategies["browser_session_transport_bridge_v1"]["providers"] == ["browser-only"]
    assert strategies["native_tls_browser_differential_v1"]["providers"] == ["tls-gap"]
    assert strategies["persistent_challenge_session_boundary_v1"]["providers"] == ["challenged"]

    assert data["policy"]["publicationAllowed"] is False
    assert data["policy"]["productionWritesAllowed"] is False
    assert data["policy"]["pullRequestOnly"] is True
    assert data["policy"]["requiresHumanMerge"] is True

    current = json.loads(POLICY.read_text(encoding="utf-8"))
    assert next_policy["learningLab"]["allStreamsSafetyCap"] > current["learningLab"]["allStreamsSafetyCap"]
    allow = json.loads(SELF.read_text(encoding="utf-8")).get("autoPatchAllowlist") or {}
    assert "learningLab.allStreamsSafetyCap" in allow
    assert next_policy["learningLab"].get("targetProvidersPerRun") == "time_budgeted_queue"
    assert "maxRepairRounds" not in next_policy["learningLab"]
    assert markdown.is_file()
    assert "NiakVIO Brain architecture evolution" in markdown.read_text(encoding="utf-8")

workflow_source = WORKFLOW.read_text(encoding="utf-8")
architecture_job = workflow_source.split("  publish-architecture-proposal:", 1)[1].split("  continue-learning-slot:", 1)[0]
assert "git status --porcelain --untracked-files=all -- engine_v2/learning/architecture-proposal.json" in architecture_job
assert architecture_job.count("cp brain-learning-output/brain-architecture-proposal.md engine_v2/learning/architecture-proposal.md") >= 2
assert "git diff --quiet -- engine_v2/learning/architecture-proposal.json" not in architecture_job

print("Brain self-architecture tests passed")
