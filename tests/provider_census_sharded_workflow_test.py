#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
text=(ROOT/".github/workflows/provider-census-sharded.yml").read_text(encoding="utf-8")

required=[
    "workflow_run:",
    "PROVIDER - Bulk Onboarding",
    "source_sha: ${{ steps.pin.outputs.sha }}",
    "should_run: ${{ steps.pin.outputs.should_run }}",
    "ref: ${{ needs.prepare.outputs.source_sha }}",
    '"$count" -gt 120',
    "matrix:\n        shard: [0, 1, 2, 3, 4, 5, 6, 7]",
    "NIAKVIO_QUICK_YIELD_WORKERS: '20'",
    "--shard-count 8",
    '--shard-index "${{ matrix.shard }}"',
    "scripts/merge_provider_census_shards.py",
    "scripts/update_provider_census_proof_history.py",
    "scripts/build_provider_repair_batch_plan.py",
    "pattern: provider-census-shard-*",
    "merge-multiple: true",
    "automation/provider-repair-batch-plan-latest.json",
    "automation/provider-bulk-activation-latest.json",
    "provider:\\ bulk\\ activate\\ *",
    'args+=(--provider "$providers")',
    "ci(census-sharded): persist",
    "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1",
    "actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a",
    "actions/download-artifact@3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c",
]
for needle in required:
    assert needle in text, needle

assert "matrix.shard + 1" not in text
assert "permissions:\n  contents: read" in text
assert "permissions:\n      contents: write" in text
assert text.count("provider-census-shard-${{ matrix.shard }}") >= 2
print("Provider sharded census workflow contract passed")
