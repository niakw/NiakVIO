#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
activation=(ROOT/".github/workflows/provider-bulk-activation.yml").read_text(encoding="utf-8")
sharded=(ROOT/".github/workflows/provider-census-sharded.yml").read_text(encoding="utf-8")
mono=(ROOT/".github/workflows/temp-current-bytes-full-provider-census.yml").read_text(encoding="utf-8")
targeted=(ROOT/".github/workflows/temp-targeted-regression-recovery.yml").read_text(encoding="utf-8")
domains=(ROOT/".github/workflows/domain-refresh.yml").read_text(encoding="utf-8")
script=(ROOT/"scripts/activate_bulk_proven_providers.py").read_text(encoding="utf-8")
onboard=(ROOT/"scripts/add_provider.py").read_text(encoding="utf-8")

for token in (
    "automation/provider-census-status.json",
    "scripts/activate_bulk_proven_providers.py",
    "automation/provider-bulk-activation-latest.json",
    "provider: bulk activate $ACTIVATION_COUNT full-ok",
    "scripts/reapply_published_overrides.py",
    "scripts/validate_published_provider_config.py",
):
    assert token in activation, token

for token in (
    '"activation_mode": "bulk_onboarding_pending" if bulk else "onboarding_pending"',
    '"validation": "bulk_onboarding_pending" if bulk else "onboarding_pending"',
    '"bulk_census_full_ok_required"',
):
    assert token in onboard, token

for token in (
    '"status") or "")!="FULL OK"',
    "declared.issubset(verified)",
    'proof.get("brainCheckRequired") is True',
    'prov["activation_mode"]="bulk_census_full_ok"',
):
    assert token in script, token

assert "automation/provider-bulk-activation-latest.json" in sharded
assert "'provider_catalog.json'" in sharded
assert "provider: bulk activate " in sharded
assert 'args+=(--provider "$providers")' in sharded
assert '"$count" -gt 120' in sharded
assert 'head_message="$(git log -1 --pretty=%s)"' in sharded
assert '[[ "$head_message" == provider:\\ bulk\\ activate\\ * ]]' in sharded
assert '"$count" -gt 120' in mono
for workflow in (targeted,domains):
    assert "provider: bulk activate " in workflow
print("Bulk proof-driven activation -> targeted sharded reproof contract passed")
