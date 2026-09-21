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
]
for needle in required:
    assert needle in workflow, f"missing causal Learning escalation contract: {needle}"

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

print("provider Repair-to-Learning causal escalation workflow contract passed")
