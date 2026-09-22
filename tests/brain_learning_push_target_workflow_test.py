#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
workflow = (ROOT / ".github/workflows/brain-learning-lab.yml").read_text(encoding="utf-8")

required = [
    "REQUESTED_TARGET_PROVIDER",
    "target_provider:",
    "automation/provider-census-status.json",
    "automation/provider-repair-learn-handoff-v1.json",
    "target provider is not in current census repairQueue",
    "target provider is not LEARN/pending in current handoff",
    'provider_filter="$target_provider"',
    'echo "target_provider=$target_provider"',
    "steps.learning-slot.outputs.target_provider",
    'if [ -n "$TARGET_PROVIDER" ]; then args+=(--provider "$TARGET_PROVIDER"); fi',
]
for needle in required:
    assert needle in workflow, needle

parse_index = workflow.index("trigger_target=")
census_index = workflow.index("target provider is not in current census repairQueue")
handoff_index = workflow.index("target provider is not LEARN/pending in current handoff")
filter_index = workflow.index('provider_filter="$target_provider"')
queue_index = workflow.index("steps.learning-slot.outputs.target_provider")
assert parse_index < census_index < handoff_index < filter_index < queue_index

# Explicit provider targeting is independent from the ephemeral fastHandoff
# marker. The selector may legitimately return fastHandoff=false after Repair
# has consumed its transient marker, while the provider remains current
# repairQueue + LEARN/pending debt.
target_block = workflow[census_index:filter_index]
assert "/tmp/fast-learning-handoff.json" not in target_block, target_block
assert "repairQueue" in target_block, target_block
assert 'row.get("owner")' in target_block or "row.get('owner')" in target_block, target_block
assert 'row.get("status")' in target_block or "row.get('status')" in target_block, target_block

lines = workflow.splitlines()
start = next(i for i,line in enumerate(lines) if "automation/provider-census-status.json automation/provider-repair-learn-handoff-v1.json <<'PY'" in line)
end = next(i for i in range(start + 1, len(lines)) if lines[i].strip() == "PY")
assert all(lines[i].startswith("          ") for i in range(start + 1, end + 1)), lines[start:end + 1]

print("Brain push-targeted Learning workflow contract passed")
