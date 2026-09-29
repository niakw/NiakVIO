#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
workflow = (ROOT / ".github/workflows/brain-learning-lab.yml").read_text(encoding="utf-8")

required = [
    "REQUESTED_TARGET_PROVIDER",
    "REQUESTED_ARCHITECTURE_FORCE",
    "target_provider:",
    "architecture_force:",
    "automation/provider-census-status.json",
    "automation/provider-repair-learn-handoff-v1.json",
    "target provider is not in current census repairQueue",
    "environmentQueue",
    "targeted Learning cohort escaped current repair/environment queues",
    "autopilot-targeted-core-learning",
    "target provider is not LEARN/pending in current handoff",
    'provider_filter="$target_provider"',
    '"policy": "target-scoped-handoff"',
    'json.dump(data,open(sys.argv[4],"w",encoding="utf-8"),ensure_ascii=False,indent=2)',
    'echo "target_provider=$target_provider"',
    'echo "architecture_force=$architecture_force"',
    "steps.learning-slot.outputs.target_provider",
    "steps.learning-slot.outputs.architecture_force",
    "required_set=set(required)",
    "cached['rows']=filtered_rows",
    "cached['providerCount']=len({",
    'if [ -n "$TARGET_PROVIDER" ]; then args+=(--provider "$TARGET_PROVIDER"); fi',
]
for needle in required:
    assert needle in workflow, needle

parse_index = workflow.index("trigger_target=")
census_index = workflow.index("target provider is not in current census repairQueue")
handoff_index = workflow.index("target provider is not LEARN/pending in current handoff")
filter_index = workflow.index('provider_filter="$target_provider"')
queue_step = workflow.index("- name: Run adaptive Learning provider queue")
queue_index = workflow.index("steps.learning-slot.outputs.target_provider", queue_step)
assert parse_index < census_index < handoff_index < filter_index < queue_index

# Explicit provider targeting is independent from the ephemeral fastHandoff
# marker. The selector may legitimately return fastHandoff=false after Repair
# has consumed its transient marker, while the provider remains current
# repairQueue + LEARN/pending debt.
target_block = workflow[census_index:filter_index]
assert "/tmp/fast-learning-handoff.json" not in target_block, target_block
assert "repairQueue" in target_block, target_block

handoff_selector = workflow.index("python scripts/select_fast_learning_handoff.py")
multi_start = workflow.index('if [ -n "$target_providers" ]; then', handoff_selector)
multi_end = workflow.index('elif [ -n "$target_provider" ]; then', multi_start)
multi_block = workflow[multi_start:multi_end]
assert 'environmentQueue' in multi_block, multi_block
assert 'eligible=repair|environment' in multi_block, multi_block
assert 'provider-fast-repair.json' not in multi_block, multi_block
assert 'current census repair/environment queues are the canonical scope' in multi_block, multi_block
assert 'autopilot-targeted-core-learning' in multi_block, multi_block
assert '"policy": "target-scoped-handoff"' in workflow, workflow
assert 'row.get("owner")' in target_block or "row.get('owner')" in target_block, target_block
assert 'row.get("status")' in target_block or "row.get('status')" in target_block, target_block

lines = workflow.splitlines()
marker = "automation/provider-census-status.json automation/provider-repair-learn-handoff-v1.json /tmp/fast-learning-handoff.json <<'PY'"
start = next(i for i,line in enumerate(lines) if marker in line)
end = next(i for i in range(start + 1, len(lines)) if lines[i].strip() == "PY")
assert all(lines[i].startswith("          ") for i in range(start + 1, end + 1)), lines[start:end + 1]

print("Brain push-targeted Learning workflow contract passed")

trigger_block = workflow[workflow.index("trigger_target="):workflow.index('target_provider="$(printf', workflow.index("trigger_target="))]
assert "trigger_force=" in trigger_block
assert "trigger_targets=" in trigger_block
assert 'target_providers="$trigger_targets"' in trigger_block
assert "architecture_force=true" in trigger_block
assert "needs.experiment.outputs.architecture_force == 'true'" in workflow
assert "needs.experiment.outputs.architecture_force != 'true'" in workflow
assert 'if [ "${FAST_HANDOFF:-false}" = "true" ] && [ -n "${FAST_MISSING_PROVIDERS:-}" ]; then' in workflow
assert 'effective_filter="${FAST_MISSING_PROVIDERS}"' in workflow
assert 'if [ "${FAST_HANDOFF:-false}" = "true" ]; then\n            effective_filter="${FAST_MISSING_PROVIDERS:-}"' not in workflow

cache_start = workflow.index("required_set=set(required)")
cache_end = workflow.index("missing=[p for p in required if p not in covered]", cache_start)
cache_block = workflow[cache_start:cache_end]
assert "filtered_rows" in cache_block
assert "providerId" in cache_block
assert "required_set" in cache_block
assert "cached_path.write_text" in cache_block
