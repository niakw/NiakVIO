#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = (ROOT / ".github/workflows/provider-recognition-repair-v6.yml").read_text(encoding="utf-8")

push_branch = WORKFLOW.split('elif [ "${{ github.event_name }}" = "push" ]; then', 2)[2]
scope_block = push_branch.split('external_force_only=', 1)[0]

assert 'mapfile -t PUSH_TARGETS' in scope_block
assert 'if [ "${#PUSH_TARGETS[@]}" -gt 0 ]; then' in scope_block
assert scope_block.index('if [ "${#PUSH_TARGETS[@]}" -gt 0 ]; then') < scope_block.index('EXPLICIT_SCOPE=1')
assert 'EXPLICIT_SCOPE=1\n            mapfile -t PUSH_TARGETS' not in scope_block
assert 'for provider in "${PUSH_TARGETS[@]}"; do' in scope_block
assert 'args=(python scripts/run_provider_repair_pipeline_v6.py --mode "$MODE")' in WORKFLOW

print("Provider Repair empty push scope contract passed: empty trigger uses census repairQueue, non-empty trigger remains explicit")
