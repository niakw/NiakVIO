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
    "cancel-in-progress: false",
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
canonical=workflow.index("- name: Run canonical recognition and correction only for unresolved providers")
assert learning_import < canonical
learning_block=workflow[learning_import:canonical]
assert "brain-learning/proposals" in learning_block
assert "engine_v2/learning/latest.json" in learning_block
assert "sanitize_brain_learning_memory.py" in learning_block
assert "NIAKVIO_BRAIN_LEARNING_MEMORY=" in learning_block
assert "engine_v2/learning/llm-guidance.json" in learning_block
assert "NIAKVIO_BRAIN_LLM_GUIDANCE=" in learning_block
assert 'data["persistentLearningPrior"]=True' in learning_block
assert "import_external_brain_llm_guidance.py" in learning_block
assert "external-brain-llm-guidance-repair.json" in learning_block
assert "external_imported=true" in learning_block
assert learning_block.index("NiakVIO-Brain-LLM.git") < learning_block.index("source=niakvio-learning")

persist=workflow.index("- name: Persist Repair census state")
copy=workflow.index("provider-brain-repair-latest.json",persist)
push=workflow.index("git push origin HEAD:main",persist)
dispatch=workflow.index("gh workflow run brain-learning-lab.yml",persist)
resume_dispatch=workflow.index("gh workflow run provider-recognition-repair-v6.yml",persist)
assert persist < copy < push < dispatch < resume_dispatch
assert "exit 0\n          fi\n          git commit" not in workflow[persist:dispatch]
assert 'if [ "$resume" = "1" ] && [ "$remaining" -gt 0 ]' in workflow[persist:resume_dispatch]
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

print("provider Repair-to-Learning causal escalation workflow contract passed")
