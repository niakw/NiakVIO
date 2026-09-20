#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
bulk=(ROOT/".github/workflows/provider-bulk-onboarding.yml").read_text(encoding="utf-8")
sharded=(ROOT/".github/workflows/provider-census-sharded.yml").read_text(encoding="utf-8")
census=(ROOT/".github/workflows/temp-current-bytes-full-provider-census.yml").read_text(encoding="utf-8")
targeted=(ROOT/".github/workflows/temp-targeted-regression-recovery.yml").read_text(encoding="utf-8")
domains=(ROOT/".github/workflows/domain-refresh.yml").read_text(encoding="utf-8")
stage=(ROOT/"scripts/stage_provider_batch.py").read_text(encoding="utf-8")
single=(ROOT/"scripts/add_provider.py").read_text(encoding="utf-8")

for token in (
    "PROVIDER - Bulk Onboarding",
    ".github/provider-onboarding/batch.json",
    "scripts/stage_provider_batch.py",
    "automation/provider-bulk-onboarding-stage.json",
    "provider-bulk-onboarding-transaction-${{ github.run_id }}",
    "git diff --cached --binary --full-index",
    "git apply --3way --index",
    "provider: bulk stage $PROVIDER_COUNT pending",
):
    assert token in bulk, token

push_block=bulk.split("  push:",1)[1].split("\n\npermissions:",1)[0]
assert ".github/provider-onboarding/batch.json" in push_block
assert ".github/workflows/provider-bulk-onboarding.yml" not in push_block
assert "scripts/stage_provider_batch.py" not in push_block

# High-volume stage is deliberately local/offline and proof-neutral.
for forbidden in (
    "resolve_provider_hubs.py",
    "resolve_provider_hub_search_fallback.py",
    "probe_provider_site_structure.py",
    "provider_branding_assets.py",
    "nuvio_client_lab.cjs",
):
    assert forbidden not in bulk, forbidden
assert "networkDiscoveryExecuted" in stage and "False" in stage
assert "nativeLabExecuted" in stage
assert "activationAttempted" in stage
assert "add_provider.stage(request,bulk=True)" in stage.replace(" ", "")
assert "if not bulk:" in single
assert '"enabled": False' in single
assert '"validation": "onboarding_pending"' in single

# Bulk publication hands off to sharded evidence before any repair loop.
assert "workflow_run:" in sharded
assert "PROVIDER - Bulk Onboarding" in sharded
for workflow in (census,targeted,domains):
    assert "provider: bulk stage " in workflow
assert "ci(census-sharded):" in census
print("Bulk onboarding -> sharded census architecture passed")
