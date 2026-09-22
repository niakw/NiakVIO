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

print("Fast-Handoff targeted discovery/reconstruction contract passed")
