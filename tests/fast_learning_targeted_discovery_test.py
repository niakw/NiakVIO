#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
discover=(ROOT/"scripts"/"discover_candidates.py").read_text(encoding="utf-8")
workflow=(ROOT/".github/workflows/brain-learning-lab.yml").read_text(encoding="utf-8")

for required in (
    'parser.add_argument(\n        "--provider"',
    "requested_provider_ids",
    "if requested_provider_ids and provider_id not in requested_provider_ids:",
    "FIELD_DISCOVERY_TARGET_SCOPE_COMPLETE",
    "requested_provider_ids.issubset(set(seen_canonical_ids))",
):
    assert required in discover, required

for required in (
    "FAST_HANDOFF_PROVIDER_FILTER",
    "build_published_provider_stage.py --stage staging",
    "args+=(--provider",
    "FIELD_FAST_LEARNING_STAGE source=published-exact",
    "FIELD_CLEAN_RECONSTRUCTION_STAGE",
    "fast_handoff='+fast",
):
    assert required in workflow, required

assert "validate-stage-against-catalog.mjs" in workflow
assert 'if [ "$FAST_HANDOFF" != "true" ]; then' in workflow

stage_start = workflow.index("- name: Build isolated current provider stage")
stage_end = workflow.index("- name: Observe the complete catalogue once for Learning", stage_start)
stage_block = workflow[stage_start:stage_end]
target_if = stage_block.index('if [ "$FAST_HANDOFF" = "true" ]')
target_else = stage_block.index("else", target_if)
target_block = stage_block[target_if:target_else]
assert "rm -rf staging" not in target_block, target_block
assert "timeout --signal=TERM --kill-after=5s 30s" in target_block, target_block
assert "FIELD_FAST_LEARNING_STAGE_ASSERT" in target_block, target_block
assert "targeted published stage cardinality mismatch" in target_block, target_block
assert "rm -rf staging" in stage_block[target_else:], stage_block[target_else:]

print("Fast-Handoff targeted discovery/reconstruction contract passed")
