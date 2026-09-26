#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
workflow = (ROOT / ".github/workflows/provider-recognition-repair-v6.yml").read_text(encoding="utf-8")
learning = (ROOT / ".github/workflows/brain-learning-lab.yml").read_text(encoding="utf-8")

# Canonical Repair/FORCE may consume prior Learning/LLM evidence, but it never
# starts a Learning child. Learning is owned by its scheduled/manual slot.
persist = workflow.index("- name: Persist Repair census state")
persist_block = workflow[persist:]
assert "FIELD_PROVIDER_BRAIN_LEARNING_DEBT" in persist_block
assert "learning_dispatch=false owner=scheduled-learning-slot" in persist_block
assert "gh workflow run brain-learning-lab.yml" not in persist_block

# Explicit FORCE remains provider-local, isolated and current-byte gated.
for required in (
    "- name: Evaluate isolated Brain LLM Force candidates",
    "scripts/evaluate_brain_llm_force_candidates.py",
    "scripts/apply_brain_llm_force_mutations.py",
    "brain-llm-force-candidate-evaluation.json",
    "accepted-brain-llm-force-mutations.json",
    "materialize_provider_v3_one.py",
    "run_provider_retest.py",
    "FIELD_BRAIN_LLM_FORCE_REQUIREMENT",
    "FIELD_BRAIN_LLM_FORCE_CURRENT_BYTES",
    "requireExternalForceMutations",
    "requireExternalBrainGuidance",
    "FIELD_FORCE_REPAIR_DIRECT_APPLY captured=true",
    "fix(force-repair): apply validated provider corrections + evidence",
):
    assert required in workflow, required

assert "FIELD_PROVIDER_BRAIN_FORCE_DEBT" in persist_block
assert "learning_dispatch=false owner=force" in persist_block
assert "resume_mode=force" in persist_block
assert '-f mode="$resume_mode"' in persist_block
assert "FIELD_PROVIDER_BRAIN_RESUME_MODE" in persist_block

# Current evidence may be rebased only across provider-neutral drift.
assert "FIELD_REPAIR_CONCURRENT_PROVIDER_DRIFT" in persist_block
assert "FIELD_REPAIR_CANONICAL_LEDGER_REBASED_NEUTRAL" in persist_block
assert "FIELD_REPAIR_FRESH_CENSUS_DISPATCH" in persist_block

# External guidance is pinned/sanitized before Force can use it.
for required in (
    "niakvio-guidance-state.json",
    "external Brain guidance paging is incomplete",
    "FIELD_EXTERNAL_BRAIN_LLM_GUIDANCE_PIN verified=true",
    "external Brain guidance source SHA does not match canonical Repair trigger",
    "external Brain guidance Brain SHA does not match canonical Repair trigger",
    "Force guidance paging incomplete",
):
    assert required in workflow, required

# Learning remains proposal/sandbox only and does not apply Force mutations.
assert "Open or refresh Brain architecture PR" in learning
assert "apply_brain_llm_force_mutations.py" not in learning

print("provider Repair/FORCE scheduled-Learning ownership contract passed")
