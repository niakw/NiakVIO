#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
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
                {"providerId": "novel", "profile": "quantum_protocol_v9", "failureClass": "impossible_new_signal", "signature": "opaque_future_case", "successes": 0, "consecutiveFailures": 2},
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
        ],
        "deferredRepairProviders": ["novel"],
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
    assert "novel_failure_class" in kinds
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
    assert "novel_architecture_layer_synthesis_v1" in strategies, strategies
    assert strategies["novel_architecture_layer_synthesis_v1"]["providers"] == ["novel"]
    assert strategies["novel_architecture_layer_synthesis_v1"]["forcePromotionEligible"] is True
    assert data["failureTaxonomy"]["unknownFamily"] == "unknown_new_failure"
    assert data["failureTaxonomy"]["unknownPolicy"] == "synthesize-new-strategy-never-retry-blindly"
    layer_ids = {row["id"] for row in data["architectureLayers"]}
    assert "meta_learning_gap_synthesis" in layer_ids, layer_ids
    assert "force_architecture_promotion" in layer_ids, layer_ids
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
assert "actions: write" in architecture_job
assert "gh workflow run brain-learning-lab.yml" in architecture_job
assert 'git status --porcelain --untracked-files=all' in architecture_job
assert architecture_job.count("cp brain-learning-output/brain-architecture-proposal.md engine_v2/learning/architecture-proposal.md") >= 2
assert "brain-architecture-force.patch" in architecture_job
assert "brain_architecture_force_materializer.py" in WORKFLOW.read_text(encoding="utf-8")
assert "architecture_force" in WORKFLOW.read_text(encoding="utf-8")
assert "architecture FORCE crossed provider/publication boundary" in architecture_job
assert "Promote FORCE architecture directly on main" in architecture_job
assert 'git push --force-with-lease=refs/heads/main:"$promotion_base" origin HEAD:main' in architecture_job
assert 'promotion_base="$GITHUB_SHA"' in architecture_job
assert 'promotion_base="$remote_main"' in architecture_job
assert "gh pr merge" not in architecture_job
assert "FIELD_BRAIN_ARCH_FORCE_MAIN_PROMOTION" in architecture_job
assert "architecture FORCE changed non-allowlisted paths" in architecture_job


# Current-byte executable profiles must be replayed before invoking costly
# architecture FORCE. Incomplete wiring must not be mistaken for installation.
spec = importlib.util.spec_from_file_location("brain_arch_proposal_guard", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)
with tempfile.TemporaryDirectory(prefix="brain-existing-profile-") as tmp:
    root = Path(tmp)
    surfaces = {
        "scripts/brain_repair_runtime.py": (
            'POST_EXHAUSTION_STRATEGY_PROFILES = {\n'
            '    "route_transition_graph_v1",\n'
            '    "route_transition_graph_v2",\n'
            '}\n'
        ),
        "engine_v2/scripts/plan-repairs.mjs": (
            'const strategies = [{ profile: "route_transition_graph_v1" }, '
            '{ profile: "route_transition_graph_v2" }];\n'
        ),
        "scripts/adaptive_runtime/runtime_repair.py": (
            'if new_strategy_id == "route_transition_graph_v1":\n'
            '    pass\n'
        ),
    }
    for path, content in surfaces.items():
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    assert module.fully_installed_repair_profiles(root) == {"route_transition_graph_v1"}
    runtime = root / "scripts/adaptive_runtime/runtime_repair.py"
    runtime.write_text(
        surfaces["scripts/adaptive_runtime/runtime_repair.py"]
        + 'elif new_strategy_id == "route_transition_graph_v2":\n'
        + '    pass\n',
        encoding="utf-8",
    )
    installed = module.fully_installed_repair_profiles(root)
    assert installed == {"route_transition_graph_v1", "route_transition_graph_v2"}
    groups = {"groups": [{
        "repairScope": "route-to-terminal",
        "groupId": "route-to-terminal|demo",
        "providers": ["demo"],
    }]}
    existing = module.build_strategy_blueprints(
        groups, {"demo"}, {"demo": {"route_transition_graph_v1"}},
        existing_executable_profiles=installed,
    )[0]
    assert existing["strategyId"] == "route_transition_graph_v2", existing
    assert existing["existingExecutableRepairProfile"] is True, existing
    assert existing["requiresNewExecutableRepairProfile"] is False, existing
    assert existing["forcePromotionEligible"] is False, existing
    assert existing["forcePromotionReason"] == "already-installed-profile-replay-first", existing
    new = module.build_strategy_blueprints(
        groups, {"demo"}, {"demo": {"route_transition_graph_v1", "route_transition_graph_v2"}},
        existing_executable_profiles=installed,
    )[0]
    assert new["strategyId"] == "route_transition_graph_v3", new
    assert new["evolvesFromStrategyId"] == "route_transition_graph_v2", new
    assert new["requiresNewExecutableRepairProfile"] is True, new
    assert new["forcePromotionEligible"] is True, new
assert "route_transition_graph_v2" in module.fully_installed_repair_profiles()

negative = {"entries": [
    {"providerId": "demo", "profile": "route_transition_graph_v2", "executionObserved": True, "failures": 1},
    {"providerId": "demo", "profile": "route_transition_graph_v99", "executionObserved": False, "failures": 10},
    {"providerId": "other", "profile": "route_transition_graph_v5", "executionObserved": True, "failures": 3},
]}
merged = module.merge_executed_repair_negatives({"demo": {"route_transition_graph_v1"}}, negative, {"demo"})
assert merged == {"demo": {"route_transition_graph_v1", "route_transition_graph_v2"}}, merged
assert module.build_strategy_blueprints(groups, {"demo"}, merged, existing_executable_profiles=installed)[0]["strategyId"] == "route_transition_graph_v3"
fast_handoff = (ROOT / ".github/workflows/provider-fast-repair.yml").read_text(encoding="utf-8").split("      - name: Persist validated provider-local repair or evidence", 1)[1]
assert 'summary.get("brainNoProgressReason")' in fast_handoff
assert "stalled and unresolved" in fast_handoff
print("Brain self-architecture tests passed")
