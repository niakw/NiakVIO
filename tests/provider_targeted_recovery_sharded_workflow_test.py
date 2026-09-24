#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
mono=(ROOT/".github/workflows/temp-targeted-regression-recovery.yml").read_text(encoding="utf-8")
sharded=(ROOT/".github/workflows/provider-targeted-recovery-sharded.yml").read_text(encoding="utf-8")

for needle in [
    "should_run={'true' if count<=120 and not bulk_push else 'false'}",
    'message.startswith("provider: bulk stage ")',
    'message.startswith("provider: bulk activate ")',
    "needs.size.outputs.should_run == 'true'",
    "scripts/run_provider_targeted_recovery.py",
    "--shard-count 1",
    "--max-workers 20",
]:
    assert needle in mono, needle

for needle in [
    "Provider Targeted Recovery - Sharded",
    "provider_count>120",
    "matrix:",
    "shard: [0, 1, 2, 3, 4, 5, 6, 7]",
    "--shard-count 8",
    '--shard-index "${{ matrix.shard }}"',
    "scripts/merge_provider_targeted_recovery_shards.py",
    "scripts/refine_provider_repair_batches.py",
    "provider-targeted-recovery-shard-*",
    "ci(repair-sharded): persist targeted recovery",
    "provider-brain-autopilot.yml",
    "FIELD_PROVIDER_SHARDED_AUTOPILOT",
    "actions: write",
]:
    assert needle in sharded, needle

assert "ThreadPoolExecutor" not in mono
print("Provider targeted recovery workflow size routing passed")
