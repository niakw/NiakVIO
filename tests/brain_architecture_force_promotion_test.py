#!/usr/bin/env python3
from __future__ import annotations

import json
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEARN = (ROOT / ".github/workflows/brain-learning-lab.yml").read_text(encoding="utf-8")
REPAIR = (ROOT / ".github/workflows/provider-recognition-repair-v6.yml").read_text(encoding="utf-8")
SELF = json.loads((ROOT / "engine_v2/config/brain-self-evolution.json").read_text(encoding="utf-8"))
POLICY = json.loads((ROOT / "engine_v2/config/brain-policy.json").read_text(encoding="utf-8"))

assert "architecture_force:" in LEARN
assert "steps.learning-slot.outputs.architecture_force == 'true'" in LEARN
assert "needs.experiment.outputs.architecture_force == 'true'" in LEARN
assert "brain_architecture_force_materializer.py" in LEARN
assert "engine_v2/scripts/plan-repairs.mjs" in LEARN
assert "brain-architecture-force.patch" in LEARN
assert "force_promotable=" in LEARN
assert "no-force-promotable-blueprint" in LEARN
assert "proposal_only=true" in LEARN
assert "Promote FORCE architecture directly on main" in LEARN
assert 'git push --force-with-lease=refs/heads/main:"$promotion_base" origin HEAD:main' in LEARN
assert "scripts/brain_force_rebase_guard.py" in LEARN
assert "FIELD_BRAIN_ARCH_FORCE_MAIN_PROMOTION neutral_rebase=true" in LEARN
assert 'promotion_base="$remote_main"' in LEARN
assert "git apply --check brain-learning-output/brain-architecture-force.patch" in LEARN
assert "FIELD_BRAIN_ARCH_FORCE_MAIN_PROMOTION" in LEARN
assert "mode=direct-main-no-pr" in LEARN
assert "FIELD_BRAIN_ARCH_FORCE_REPRESENTATIVE_REPLAY" in LEARN
assert 'gh workflow run provider-recognition-repair-v6.yml' in LEARN
assert '-f mode=force' in LEARN
assert 'preferred_profile="$preferred_profile"' in LEARN
assert 'forcePreferredStrategy' in (ROOT / "scripts/brain_repair_runtime.py").read_text(encoding="utf-8")
assert 'NUVIO_BRAIN_FORCE_PREFERRED_PROFILE' in (ROOT / "scripts/run_provider_brain_repair.py").read_text(encoding="utf-8")
assert 'postExhaustionStrategyHint(' in (ROOT / "engine_v2/scripts/plan-repairs.mjs").read_text(encoding="utf-8")
assert "A generated Brain executor cannot be proven by a one-wave" in LEARN
assert 'brain_cmd.append("--architecture-force")' in (ROOT / "scripts/run_provider_repair_pipeline_v6.py").read_text(encoding="utf-8")
assert '-f target_provider="$representative"' in LEARN
assert "exactly one representative current repairQueue member" in LEARN
assert "needs.experiment.outputs.architecture_force != 'true' && (github.event_name == 'push' || github.event_name == 'workflow_dispatch')" in LEARN
assert 'gh pr merge "$PR_NUMBER"' not in LEARN
assert "mode=merge-after-green-pr-checks" not in LEARN
assert "architecture FORCE changed non-allowlisted paths" in LEARN
assert 'engine_v2/config/brain-self-evolution.json "${{ steps.materialize-architecture.outputs.force_promotable }}"' in LEARN
assert "if architecture_force and not has_executable:" in LEARN
assert "architecture_force=" in LEARN and "executable=" in LEARN
assert "architecture FORCE crossed provider/publication boundary" in LEARN

assert "-f architecture_force=true" in REPAIR
assert "-f publish_proposal=false" in REPAIR
assert '-f target_providers="$deferred_csv"' in REPAIR
assert "FIELD_PROVIDER_BRAIN_FORCE_ARCH_DISPATCH" in REPAIR

force = SELF.get("forceArchitecture") or {}
assert force.get("enabled") is True
assert force.get("structuralMaterializationRequired") is True
assert force.get("requireExecutableDiff") is True
assert force.get("requireTargetedTests") is True
assert force.get("requireWorkflowGate") is True
assert force.get("providerPublicationAuthority") is False
assert force.get("productionProviderWritesAllowed") is False
assert "scripts/brain_meta_learning.py" in (SELF.get("structuralProposalSurfaces") or [])
assert "scripts/brain_architecture_force_materializer.py" in (SELF.get("structuralProposalSurfaces") or [])
assert "engine_v2/scripts/plan-repairs.mjs" in (SELF.get("structuralProposalSurfaces") or [])
generated = set((SELF.get("forceArchitecture") or {}).get("generatedEditAllowlist") or [])
assert "scripts/brain_meta_learning.py" in generated
assert "engine_v2/scripts/plan-repairs.mjs" in generated
assert "scripts/brain_layers/*" in generated
assert ".github/workflows/brain-learning-lab.yml" not in generated
assert ".github/workflows/provider-recognition-repair-v6.yml" not in generated
assert "engine_v2/config/brain-policy.json" not in generated

lab = POLICY.get("learningLab") or {}
promotion = lab.get("forceArchitecturePromotion") or {}
assert promotion.get("enabled") is True
assert promotion.get("requireExecutableDiff") is True
assert promotion.get("allowNewFailureFamilies") is True
assert promotion.get("allowNewArchitectureLayers") is True
assert promotion.get("providerPublicationAuthority") is False
assert promotion.get("productionProviderWritesAllowed") is False

# Neutral evidence-only main movement may be rebased and revalidated; any
# provider/global code drift remains fail-closed and forces a fresh FORCE run.
GUARD=ROOT/"scripts"/"brain_force_rebase_guard.py"
spec=importlib.util.spec_from_file_location("brain_force_rebase_guard",GUARD)
assert spec and spec.loader
guard=importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)
neutral=guard.classify(
    ROOT,"a"*40,"b"*40,
    drift_fn=lambda *_args: (["automation/provider-census-status.json","PROVIDER_CENSUS_STATUS.md"],set()),
)
assert neutral["safe"] is True and neutral["reason"]=="neutral-only",neutral
provider=guard.classify(
    ROOT,"a"*40,"b"*40,
    drift_fn=lambda *_args: ([],{"moviebox"}),
)
assert provider["safe"] is False and provider["reason"]=="provider-drift",provider
global_blocked=guard.classify(
    ROOT,"a"*40,"b"*40,
    drift_fn=lambda *_args: (_ for _ in ()).throw(ValueError("global/provider-wide drift since guidance source: scripts/brain_repair_runtime.py")),
)
assert global_blocked["safe"] is False and global_blocked["reason"]=="non-neutral-drift",global_blocked

# The workflow must package the actual generated runtime executor: a
# registry/planner-only patch is dead code and cannot be promoted.
force_diff = LEARN.split("git diff --binary --", 1)[1].split(
    "> brain-learning-output/brain-architecture-force.patch", 1,
)[0]
assert "scripts/adaptive_runtime/runtime_repair.py" in force_diff
assert "tests/brain_llm_advisor_execution_test.py" in LEARN, (
    "FORCE replay must exercise planner exhaustion after a new strategy is installed"
)
assert LEARN.count("python tests/brain_llm_advisor_execution_test.py") >= 5, (
    "materialization, promotion and stale-rebase must run dynamic strategy convergence"
)

assert LEARN.count("python scripts/brain_force_applied_profile_guard.py --proposal") == 3
assert "scripts/adaptive_runtime/runtime_repair.py" in SELF["forceArchitecture"]["generatedEditAllowlist"]

# Validate the guard on a structurally installed v3 and on real omission
# scenarios before any workflow consumes a FORCE artifact.
import sys
import tempfile
sys.path.insert(0, str(ROOT / "scripts"))
GUARD_APPLIED = ROOT / "scripts/brain_force_applied_profile_guard.py"
applied_spec = importlib.util.spec_from_file_location("brain_force_applied", GUARD_APPLIED)
assert applied_spec and applied_spec.loader
applied_guard = importlib.util.module_from_spec(applied_spec)
applied_spec.loader.exec_module(applied_guard)
with tempfile.TemporaryDirectory(prefix="brain-force-applied-") as temp:
    root = Path(temp)
    fixture = {
        "scripts/brain_repair_runtime.py": (
            'POST_EXHAUSTION_STRATEGY_PROFILES = {\n'
            '    "route_transition_graph_v2",\n'
            '    "route_transition_graph_v3",\n'
            '}\n'
        ),
        "engine_v2/scripts/plan-repairs.mjs": (
            'const POST_EXHAUSTION_STRATEGIES = {\n'
            '  route_proven_gap: [\n'
            '    { profile: "route_transition_graph_v2", method: "baseline" },\n'
            '    { profile: "route_transition_graph_v3", method: "new" },\n'
            '  ],\n'
            '};\n'
        ),
        "scripts/adaptive_runtime/runtime_repair.py": (
            'POST_EXHAUSTION_STRATEGY_PROFILES = {\n'
            '    "route_transition_graph_v2",\n'
            '    "route_transition_graph_v3",\n'
            '}\n'
            'if new_strategy_id == "route_transition_graph_v2":\n'
            '    choice = "old"\n'
            'elif new_strategy_id == "route_transition_graph_v3":\n'
            '    choice = "new"\n'
        ),
    }
    for relative, content in fixture.items():
        file = root / relative
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(content, encoding="utf-8")
    plan = {"strategyBlueprints": [{
        "strategyId": "route_transition_graph_v3",
        "evolvesFromStrategyId": "route_transition_graph_v2",
        "requiresNewExecutableRepairProfile": True,
        "forcePromotionEligible": True,
    }]}
    report = {"strategyId": "route_transition_graph_v3",
              "editCount": 3, "changedFiles": list(fixture)}
    assert applied_guard.verify(plan, report, root=root) == "route_transition_graph_v3"
    try:
        applied_guard.verify(plan, {**report, "changedFiles": list(fixture)[:2]}, root=root)
    except ValueError as exc:
        assert "artifact lost generated runtime" in str(exc), exc
    else:
        raise AssertionError("incomplete FORCE artifact unexpectedly accepted")
    runtime = root / "scripts/adaptive_runtime/runtime_repair.py"
    runtime.write_text(
        fixture["scripts/adaptive_runtime/runtime_repair.py"].replace(
            '    "route_transition_graph_v3",\n', ""
        ),
        encoding="utf-8",
    )
    try:
        applied_guard.verify(plan, report, root=root)
    except ValueError as exc:
        assert "not selectable by adaptive runtime" in str(exc), exc
    else:
        raise AssertionError("unselectable FORCE strategy unexpectedly accepted")

print("Brain architecture FORCE promotion workflow contract passed")

# FORCE proposal-only is a valid non-promotable outcome; executable diff
# requirements apply only when the materializer reports a real structural patch.
assert 'if [ "${{ steps.materialize-architecture.outputs.force_promotable }}" = "true" ]; then' in LEARN
assert 'FIELD_BRAIN_ARCH_FORCE_PROMOTION skipped=true reason=no-force-promotable-blueprint proposal_only=true' in LEARN
