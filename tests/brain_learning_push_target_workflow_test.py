#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
workflow = (ROOT / ".github/workflows/brain-learning-lab.yml").read_text(encoding="utf-8")

required = [
    "REQUESTED_TARGET_PROVIDER",
    "target_provider:",
    "target provider is not in current Repair Learning handoff",
    'provider_filter="$target_provider"',
    'echo "target_provider=$target_provider"',
    "steps.learning-slot.outputs.target_provider",
    'if [ -n "$TARGET_PROVIDER" ]; then args+=(--provider "$TARGET_PROVIDER"); fi',
]
for needle in required:
    assert needle in workflow, needle

parse_index = workflow.index("trigger_target=")
scope_index = workflow.index("target provider is not in current Repair Learning handoff")
filter_index = workflow.index('provider_filter="$target_provider"')
queue_index = workflow.index("steps.learning-slot.outputs.target_provider")
assert parse_index < scope_index < filter_index < queue_index

lines = workflow.splitlines()
start = next(i for i,line in enumerate(lines) if "fast-learning-handoff.json <<'PY'" in line)
end = next(i for i in range(start + 1, len(lines)) if lines[i].strip() == "PY")
assert all(lines[i].startswith("          ") for i in range(start + 1, end + 1)), lines[start:end + 1]

print("Brain push-targeted Learning workflow contract passed")
