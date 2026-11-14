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
    "automation/provider-onboarding-pending-status-latest.json",
    "scripts/activate_bulk_proven_providers.py",
    "automation/provider-bulk-activation-latest.json",
    "provider: bulk activate $ACTIVATION_COUNT full-ok",
    "tests/provider_v3_minimizer_published_test.py",
    "scripts/validate_published_provider_config.py",
    "tests/production_active_provider_freshness_test.py",
    "provider_catalog.json",
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
    'proof.get("testedThisRun") is not True',
    "declared.issubset(verified)",
    'proof.get("brainCheckRequired") is True',
    'prov["activation_mode"]="bulk_census_full_ok"',
    'scope="france"',
    'write(CATALOG,catalog)',
    "restore_pending_artifacts(",
    "provider-disabled",
):
    assert token in script, token

assert "provider-disabled" in activation
assert "provider-disabled" in onboard
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

assert "providerSha256" in script
assert "pending_artifact_hash_mismatch" in script
assert "onboarding-pending-status" in script
assert "automation/provider-onboarding-pending-status-latest.json" in sharded
print("Bulk activation is byte-bound to isolated pending census proof")

assert "workflow_run:" in activation
assert "Provider Census - Sharded" in activation
assert "CORE - Finalize Accepted Release" in activation
assert "github.event.workflow_run.conclusion == 'success'" in activation
assert "scripts/reapply_published_overrides.py" not in activation
assert "Never rebuild/reapply provider code here" in activation
print("Bulk activation preserves exact replayed pending bytes and converges from workflow_run")

assert "PROVIDER - Bulk Activation" in sharded
assert 'census_scope="all"' in sharded
assert "proof_source_artifact_digest" in script
assert "pending_proof_source_byte_drift" in script
assert "pending ProviderBase hash mismatch" in script
print("Bulk activation exact-source proof -> full-cohort revalidation contract passed")
