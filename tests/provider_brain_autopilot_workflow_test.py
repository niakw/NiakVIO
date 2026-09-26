#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
autopilot = (ROOT / ".github/workflows/provider-brain-autopilot.yml").read_text(encoding="utf-8")
retest = (ROOT / ".github/workflows/provider-retest.yml").read_text(encoding="utf-8")
fast = (ROOT / ".github/workflows/provider-fast-repair.yml").read_text(encoding="utf-8")
remat = (ROOT / ".github/workflows/provider-remat-test.yml").read_text(encoding="utf-8")

for required in (
    "scripts/build_provider_execution_plan.py",
    "provider-remat-test.yml",
    "provider-fast-repair.yml",
    "domain-refresh.yml",
    "CORE_CLIENT_LEARNING",
    "provider-waf-browser-session.yml",
    "scheduled-learning-slot-only",
):
    assert required in autopilot, required

# Autopilot never launches Learning outside the dedicated slot.
assert "gh workflow run brain-learning-lab.yml" not in autopilot
assert "contents: read" in autopilot
assert "contents: write" not in autopilot
assert "git add " not in autopilot
assert "git push origin HEAD:main" not in autopilot

# It may still refresh WAF/native transport evidence for harness debt.
harness_start = autopilot.index('if [ -n "$HARNESS" ]; then')
harness_block = autopilot[harness_start:autopilot.index("      - uses: actions/upload-artifact@", harness_start)]
assert "provider-waf-browser-session.yml" in harness_block
assert "architecture_learning=false" in harness_block
assert "scheduled-learning-slot-only" in harness_block

learning_start = autopilot.index('if [ -n "$LEARNING" ]; then')
learning_block = autopilot[learning_start:harness_start]
assert "scheduled-learning-slot-only" in learning_block
assert "brain-learning-lab.yml" not in learning_block

# A current causal plan is mandatory.
for required in (
    'git fetch --quiet origin main',
    'remote_main="$(git rev-parse origin/main)"',
    'if [ "$remote_main" != "$GITHUB_SHA" ]; then',
    "FIELD_PROVIDER_AUTOPILOT_STALE",
):
    assert required in autopilot, required

# Retest routes through Autopilot, not directly to Fast Repair.
chain = retest.split("Launch causal Brain Autopilot when requested", 1)[1]
assert "provider-brain-autopilot.yml" in chain
assert "gh workflow run provider-fast-repair.yml" not in chain

for source in (fast, remat):
    assert "target_providers:" in source
    assert "DISPATCH_PROVIDERS" in source

assert '-f waves=1 -f time_budget_seconds=600 -f max_rounds_per_batch=1' in autopilot
print("provider Brain Autopilot scheduled-Learning ownership contract passed")
