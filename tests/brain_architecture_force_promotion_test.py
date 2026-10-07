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
assert '-f mode=repair' in LEARN
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

print("Brain architecture FORCE promotion workflow contract passed")

# FORCE proposal-only is a valid non-promotable outcome; executable diff
# requirements apply only when the materializer reports a real structural patch.
assert 'if [ "${{ steps.materialize-architecture.outputs.force_promotable }}" = "true" ]; then' in LEARN
assert 'FIELD_BRAIN_ARCH_FORCE_PROMOTION skipped=true reason=no-force-promotable-blueprint proposal_only=true' in LEARN
