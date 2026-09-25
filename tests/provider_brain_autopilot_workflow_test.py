#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
autopilot=(ROOT/".github/workflows/provider-brain-autopilot.yml").read_text(encoding="utf-8")
retest=(ROOT/".github/workflows/provider-retest.yml").read_text(encoding="utf-8")
fast=(ROOT/".github/workflows/provider-fast-repair.yml").read_text(encoding="utf-8")
remat=(ROOT/".github/workflows/provider-remat-test.yml").read_text(encoding="utf-8")
learning=(ROOT/".github/workflows/brain-learning-lab.yml").read_text(encoding="utf-8")

for required in (
    "scripts/build_provider_execution_plan.py",
    "scripts/provider_learning_dispatch_gate.py",
    "provider-remat-test.yml",
    "provider-fast-repair.yml",
    "domain-refresh.yml",
    "brain-learning-lab.yml",
    "CORE_CLIENT_LEARNING",
    "provider-waf-browser-session.yml",
    "select-plan",
    "--lane BRAIN_LEARNING",
    "--lane CORE_CLIENT_LEARNING",
    "automation/provider-learning-dispatch-ledger.json",
    'target_providers="$learning_csv"',
    'target_providers="$harness_learning_csv"',
    "no-new-causal-fingerprint",
    "fingerprint=new",
    "architecture_learning=true",
    "mutation=proposal-only",
    "targeted=true",
):
    assert required in autopilot,required

# A current causal plan is mandatory. Autopilot never dispatches from a stale SHA.
for required in (
    'git fetch --quiet origin main',
    'remote_main="$(git rev-parse origin/main)"',
    'if [ "$remote_main" != "$GITHUB_SHA" ]; then',
    'FIELD_PROVIDER_AUTOPILOT_STALE',
    'gh workflow run provider-brain-autopilot.yml',
):
    assert required in autopilot, required

# A domain/transport owner invalidates downstream assumptions and must run alone.
assert 'if [ -n "$DOMAIN" ]; then' in autopilot
assert "exit 0" in autopilot.split('if [ -n "$DOMAIN" ]; then',1)[1].split("fi",1)[0]

# Retest hands control to the causal router, never directly to Fast Repair.
chain=retest.split("Launch causal Brain Autopilot when requested",1)[1]
assert "provider-brain-autopilot.yml" in chain
assert "gh workflow run provider-fast-repair.yml" not in chain

# Cohort dispatch is first-class for catalogue-scale execution.
for source in (fast,remat):
    assert "target_providers:" in source
    assert "DISPATCH_PROVIDERS" in source
    assert "IFS=',' read -r -a raw_providers" in source

for required in (
    "target_providers:",
    "REQUESTED_TARGET_PROVIDERS",
    "autopilot-targeted-learning",
    "target_providers=$target_providers",
):
    assert required in learning,required
assert "cancel-in-progress: ${{ github.event_name == 'push' }}" in learning
assert 'if [ -n "$LEARNING" ] && [ -z "$FAST" ]' not in autopilot

# Harness transport refresh is independent from architecture Learning. The latter
# is gated and targets only the newly eligible cohort.
harness_start=autopilot.index('if [ -n "$HARNESS" ]; then')
harness_block=autopilot[harness_start:autopilot.index("      - uses: actions/upload-artifact@",harness_start)]
assert "provider-waf-browser-session.yml" in harness_block
assert "provider_learning_dispatch_gate.py select-plan" in harness_block
assert "brain-learning-lab.yml" in harness_block
assert '-f publish_proposal=true' in harness_block
assert '-f target_providers="$harness_learning_csv"' in harness_block
assert "architecture_learning=true" in harness_block

learning_start=autopilot.index('if [ -n "$LEARNING" ]; then')
learning_block=autopilot[learning_start:harness_start]
assert "provider_learning_dispatch_gate.py select-plan" in learning_block
assert '-f target_providers="$learning_csv"' in learning_block
assert '-f target_providers="$LEARNING"' not in learning_block

# The only contents-write use is the sanitized dispatch ledger transaction.
assert "contents: write" in autopilot
assert 'git add automation/provider-learning-dispatch-ledger.json' in autopilot
assert autopilot.count("git add ") == 1, autopilot
assert autopilot.count("git push origin HEAD:main") == 1, autopilot
for forbidden_write in (
    "git add provider-overrides.json",
    "git add providers",
    "git add provider-bases",
    "git add engine_v2",
    "git add scripts",
):
    assert forbidden_write not in autopilot,forbidden_write

# Fast Repair is intentionally one bounded causal wave. Learning owns later
# rotations; autopilot must not silently re-expand it to the old 3-wave/20m path.
assert '-f waves=1 -f time_budget_seconds=600 -f max_rounds_per_batch=1' in autopilot
assert '-f waves=3' not in autopilot
assert 'default: "1"' in fast.split("waves:",1)[1].split("time_budget_seconds:",1)[0]
assert 'default: "600"' in fast.split("time_budget_seconds:",1)[1].split("max_rounds_per_batch:",1)[0]

# Autopilot itself never mutates production provider bytes.
for forbidden in (
    "materialize_provider_v3_one.py",
    "run_provider_brain_repair.py",
    "provider-overrides.json provider",
):
    assert forbidden not in autopilot,forbidden

print("provider Brain Autopilot workflow contract passed")
