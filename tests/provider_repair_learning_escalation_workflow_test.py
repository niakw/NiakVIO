#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
workflow=(ROOT/".github/workflows/provider-recognition-repair-v6.yml").read_text(encoding="utf-8")

required=[
    "actions: write",
    "automation/provider-brain-repair-latest.json",
    "automation/brain-positive-program-memory.json",
    "deferredLearningProviders",
    "FIELD_PROVIDER_BRAIN_ESCALATE",
    "gh workflow run brain-learning-lab.yml",
    "-f publish_proposal=true",
    "FIELD_PROVIDER_BRAIN_RESUME",
    "resumeRecommended",
    "gh workflow run provider-recognition-repair-v6.yml",
    "cancel-in-progress: ${{ github.event_name == 'push' }}",
    "FIELD_REPAIR_CENSUS_NOT_PERSISTED authority_schema_v3_required",
    "automation/provider-authority-status.json",
    "Import sanitized Brain Learning priors for canonical Repair",
    "scripts/sanitize_brain_learning_memory.py",
    "NIAKVIO_BRAIN_LEARNING_MEMORY=",
    "FIELD_CANONICAL_REPAIR_LEARNING_MEMORY imported=true",
    "engine_v2/learning/llm-guidance.json",
    "NIAKVIO_BRAIN_LLM_GUIDANCE=",
    "FIELD_CANONICAL_REPAIR_LLM_GUIDANCE imported=true",
    "scripts/import_external_brain_llm_guidance.py",
    "NiakVIO-Brain-LLM.git",
    "niakvio-guidance",
    "FIELD_CANONICAL_REPAIR_EXTERNAL_LLM_GUIDANCE imported=true",
    '"authorityRepairEligible" in row and "authorityAction" in row',
]
for needle in required:
    assert needle in workflow, f"missing causal Learning escalation contract: {needle}"

learning_import=workflow.index("- name: Import sanitized Brain Learning priors for canonical Repair")
force_mutation=workflow.index("- name: Apply bounded Brain LLM Force mutations to sandbox")
canonical=workflow.index("- name: Run canonical recognition and correction only for unresolved providers")
assert learning_import < force_mutation < canonical
force_mutation_block=workflow[force_mutation:canonical]
assert "scripts/apply_brain_llm_force_mutations.py" in force_mutation_block
assert "niakvio-force-mutations.json" in force_mutation_block
assert "directApplyValidated" in force_mutation_block
assert "not-explicit-force" in force_mutation_block
assert "--current-sha \"$GITHUB_SHA\"" in force_mutation_block
assert "automation/brain-llm-force-mutation-application.json" in force_mutation_block
learning_block=workflow[learning_import:canonical]
assert "brain-learning/proposals" in learning_block
assert "engine_v2/learning/latest.json" in learning_block
assert "sanitize_brain_learning_memory.py" in learning_block
assert "NIAKVIO_BRAIN_LEARNING_MEMORY=" in learning_block
assert "engine_v2/learning/llm-guidance.json" in learning_block
assert "NIAKVIO_BRAIN_LLM_GUIDANCE=" in learning_block
assert 'data["persistentLearningPrior"]=True' in learning_block
assert 'allowed_v2=allowed_v1|{"experiment","experimentFingerprint"}' in learning_block
assert "validate_public" in learning_block
assert 'schema not in {1,2}' in learning_block
assert "import_external_brain_llm_guidance.py" in learning_block
assert "external-brain-llm-guidance-repair.json" in learning_block
assert "external_imported=true" in learning_block
assert "--negative-memory automation/brain-repair-memory.json" in learning_block
assert '--negative-memory "$RUNNER_TEMP/brain-learning-latest.json"' in learning_block
assert "empty-after-negative-memory-filter" in learning_block
assert "from import_external_brain_llm_guidance import canon,failed_llm_experiments" in learning_block
assert "negative_paths=[Path(value) for value in sys.argv[4:]]" in learning_block
assert 'negative_paths=[Path(value) for value in sys.argv[4:]]' in learning_block
assert 'automation/brain-repair-memory.json "$RUNNER_TEMP/brain-learning-latest.json"' in learning_block
assert 'data["droppedFailedExperimentRows"]=dropped_failed' in learning_block
assert learning_block.index("NiakVIO-Brain-LLM.git") < learning_block.index("source=niakvio-learning")

persist=workflow.index("- name: Persist Repair census state")
copy=workflow.index("provider-brain-repair-latest.json",persist)
push=workflow.index("git push origin HEAD:main",persist)
dispatch=workflow.index("gh workflow run brain-learning-lab.yml",persist)
resume_dispatch=workflow.index("gh workflow run provider-recognition-repair-v6.yml",persist)
assert persist < copy < push < dispatch < resume_dispatch
assert "-f slot_remaining_minutes=20" in workflow[dispatch:resume_dispatch]
assert "-f slot_phase=1" in workflow[dispatch:resume_dispatch]
assert "exit 0\n          fi\n          git commit" not in workflow[persist:dispatch]
assert 'if [ "$resume" = "1" ] && [ "$remaining" -gt 0 ] && [ "$unvisited" -gt 0 ]' in workflow[persist:resume_dispatch]
assert "FIELD_PROVIDER_BRAIN_RESUME_SKIPPED reason=no-unvisited-provider" in workflow[persist:]
persist_block=workflow[persist:dispatch]
assert 'cp automation/brain-positive-program-memory.json "$tmp/brain-positive-program-memory.json"' in persist_block
assert 'cp "$tmp/brain-positive-program-memory.json" automation/brain-positive-program-memory.json' in persist_block
assert 'git add automation/brain-positive-program-memory.json' in persist_block
assert 'cp automation/provider-authority-status.json "$tmp/provider-authority-status.json"' in persist_block
assert 'cp "$tmp/provider-authority-status.json" automation/provider-authority-status.json' in persist_block
assert 'git add automation/provider-authority-status.json' in persist_block
assert 'canonical_repair_outcome="${{ steps.canonical-repair.outcome }}"' in persist_block
assert 'if [ "$canonical_repair_outcome" != "skipped" ]' in persist_block
assert 'git diff --quiet "$GITHUB_SHA" -- automation/brain-repair-memory.json' in persist_block
assert 'git diff --quiet "$GITHUB_SHA" -- automation/brain-positive-program-memory.json' in persist_block
assert 'source != current' in persist_block
assert 'FIELD_REPAIR_CURRENT_RUN_BRAIN_REPORT captured=false reason=canonical-repair-skipped' in persist_block
assert 'FIELD_REPAIR_CURRENT_RUN_BRAIN_REPORT captured=false reason=source-sha-mismatch' in persist_block
assert 'FIELD_REPAIR_STALE_BRAIN_NOT_PERSISTED' in persist_block
assert 'FIELD_REPAIR_STALE_ESCALATION_SKIPPED' in persist_block

print("provider Repair-to-Learning causal escalation workflow contract passed")


# A failed canonical Repair may persist causal Brain memory/report only; it may
# never replace the durable census/authority/WAF ledger with its rejected
# candidate state.
persist_block=workflow[workflow.index("- name: Persist Repair census state"):]
assert 'canonical_ledger_publishable=0' in persist_block
assert 'if [ "$canonical_repair_outcome" = "success" ]; then' in persist_block
assert "FIELD_REPAIR_CANONICAL_LEDGER_FAIL_CLOSED" in persist_block
assert persist_block.count('if [ "$canonical_ledger_current" = "1" ] && [ "$canonical_ledger_publishable" = "1" ]; then') >= 2
assert 'FIELD_REPAIR_CANONICAL_LEDGER_SKIPPED reason=canonical-repair-$canonical_repair_outcome' in persist_block


# Explicit Force may apply a validated provider-local candidate directly, but
# Learning itself remains proposal-only. Direct application is guarded by the
# canonical Repair success *and* the four-version/non-regression candidate gate.
force_block=workflow[workflow.index("- name: Enforce four-version floor on repair candidate"):workflow.index("if [ \"$canonical_ledger_current\" != \"1\" ] && [ \"$provider_input_drift\" = \"1\" ]")]
assert "id: candidate-gate" in force_block
assert "DISPATCH_MODE: ${{ inputs.mode || '' }}" in force_block
assert "CANDIDATE_GATE_OUTCOME: ${{ steps.candidate-gate.outcome }}" in force_block
assert '[ "${{ github.event_name }}" = "workflow_dispatch" ]' in force_block
assert '[ "${DISPATCH_MODE:-}" = "force" ]' in force_block
assert '[ "${CANDIDATE_GATE_OUTCOME:-}" = "success" ]' in force_block
assert "FIELD_FORCE_REPAIR_DIRECT_APPLY captured=true" in force_block
assert "git cherry-pick --no-commit" in force_block
assert "fix(force-repair): apply validated provider corrections + evidence" in force_block
assert "scripts/provider_patches/" in force_block
assert 'mode not in {"repair","force"}' in workflow
assert 'data.get("directApplyValidated") is True' in force_block
assert 'str(data.get("mode") or "").strip().casefold()=="force"' in force_block
assert 'force_requested=1' in force_block
assert "require_external_force_mutations" in workflow
assert "requireExternalForceMutations" in workflow
assert "FIELD_BRAIN_LLM_FORCE_REQUIREMENT" in force_mutation_block
assert "appliedProviderCount" in force_mutation_block
assert "Explicit Force required external Brain mutations but none were applied" in force_mutation_block
assert force_mutation < canonical

learning_workflow=(ROOT/".github/workflows/brain-learning-lab.yml").read_text(encoding="utf-8")
assert "productionWritesAllowed!==false" in learning_workflow
assert "publicationAllowed!==false" in learning_workflow
assert "pullRequestOnly!==true" in learning_workflow
assert "requiresHumanMerge!==true" in learning_workflow
assert "Open or refresh Brain architecture PR" in learning_workflow
assert "apply_brain_llm_force_mutations.py" not in learning_workflow

assert '-f target_providers="$deferred_csv"' in workflow
