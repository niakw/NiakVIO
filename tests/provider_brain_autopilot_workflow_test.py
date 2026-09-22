#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
autopilot=(ROOT/".github/workflows/provider-brain-autopilot.yml").read_text(encoding="utf-8")
retest=(ROOT/".github/workflows/provider-retest.yml").read_text(encoding="utf-8")
fast=(ROOT/".github/workflows/provider-fast-repair.yml").read_text(encoding="utf-8")
remat=(ROOT/".github/workflows/provider-remat-test.yml").read_text(encoding="utf-8")

for required in (
    "scripts/build_provider_execution_plan.py",
    "provider-remat-test.yml",
    "provider-fast-repair.yml",
    "domain-refresh.yml",
    "brain-learning-lab.yml",
    "CORE_CLIENT_LEARNING",
    "provider-waf-browser-session.yml",
    "target_providers=\"$HARNESS\"",
    "mutation=false",
):
    assert required in autopilot,required

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

# Autopilot itself never mutates production provider bytes.
for forbidden in (
    "materialize_provider_v3_one.py",
    "run_provider_brain_repair.py",
    "git push",
    "provider-overrides.json provider",
):
    assert forbidden not in autopilot,forbidden

print("provider Brain Autopilot workflow contract passed")
