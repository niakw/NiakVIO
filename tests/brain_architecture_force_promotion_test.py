#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEARN = (ROOT / ".github/workflows/brain-learning-lab.yml").read_text(encoding="utf-8")
REPAIR = (ROOT / ".github/workflows/provider-recognition-repair-v6.yml").read_text(encoding="utf-8")
SELF = json.loads((ROOT / "engine_v2/config/brain-self-evolution.json").read_text(encoding="utf-8"))
POLICY = json.loads((ROOT / "engine_v2/config/brain-policy.json").read_text(encoding="utf-8"))

assert "architecture_force:" in LEARN
assert "brain_architecture_force_materializer.py" in LEARN
assert "brain-architecture-force.patch" in LEARN
assert "Architecture FORCE may not auto-promote proposal-only metadata" in LEARN
assert 'gh pr merge "$PR_NUMBER"' in LEARN
assert "gh pr checks" in LEARN and "--watch" in LEARN and "--fail-fast" in LEARN
assert "mode=merge-after-green-pr-checks" in LEARN
assert "architecture FORCE changed non-allowlisted paths" in LEARN
assert "architecture FORCE crossed provider/publication boundary" in LEARN

assert "-f architecture_force=true" in REPAIR
assert "-f publish_proposal=true" in REPAIR
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
generated = set((SELF.get("forceArchitecture") or {}).get("generatedEditAllowlist") or [])
assert "scripts/brain_meta_learning.py" in generated
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

print("Brain architecture FORCE promotion workflow contract passed")
