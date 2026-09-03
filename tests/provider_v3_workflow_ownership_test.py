#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
policy=json.loads((ROOT/"automation/provider-v3-architecture.json").read_text(encoding="utf-8"))
routine=(ROOT/".github/workflows/sync.yml").read_text(encoding="utf-8")
learn=(ROOT/".github/workflows/brain-learning-lab.yml").read_text(encoding="utf-8")
manual=(ROOT/".github/workflows/provider-v3-reconstruct-all.yml").read_text(encoding="utf-8")
domain=(ROOT/".github/workflows/domain-refresh.yml").read_text(encoding="utf-8")
legacy_core=ROOT/".github/workflows/core-media-finalize-main.yml"

assert not legacy_core.exists(), "legacy duplicate Core finalizer workflow must stay deleted"
assert routine.startswith("name: CORE - Verify & Publish")
assert routine.count("schedule:")==1
assert "47 4 * * 2,5" in routine
assert "MODE=deep" in routine
assert "Deep gate - full structural contracts" in routine
assert "Deep - reproject manifests and integrity inventories" in routine

for mode in ("quick","deep"):
    assert policy["routine"][mode]["repair_allowed"] is False
    assert policy["routine"][mode]["provider_fix_mutation_allowed"] is False
    assert policy["routine"][mode]["provider_reconstruction_allowed"] is False

for forbidden in (
    "run_adaptive_deep_repair.py",
    "run_adaptive_quick_repair.py",
    "promote_candidates.py",
    "promote_refresh_candidates.py",
    "materialize_provider_v3_all.py",
    "verify_provider_v3_reverse_rebuild.py",
    "--apply",
):
    assert forbidden not in routine, f"routine workflow must not mutate/reconstruct providers: {forbidden}"

assert "audit_provider_v3_static.py" in routine
assert "build_published_provider_stage.py" in routine
assert "build_observational_health_report.py" in routine

for required in ("run_brain_learning_queue.py","build_brain_repair_proposal.py","brain-repair/proposal"):
    assert required in learn, f"LEARN lost repair/proposal ownership: {required}"
assert "--include-disabled" in learn or "including disabled providers" in learn

for required in ("materialize_provider_v3_all.py","verify_provider_v3_reverse_rebuild.py","96"):
    assert required in manual
assert "Refuse direct main mutation" in manual
assert "NUVIO_PROVIDER_V3_CONTEXT: workspace" in manual

assert "--apply" in domain and "--domain-only" in domain
assert "update_provider_v3_domain_config.py" in domain
assert "audit_provider_v3_static.py" in domain
assert "materialize_provider_v3_all.py" not in domain
assert "verify_provider_v3_reverse_rebuild.py" not in domain

print("provider v3 workflow ownership contract passed: one routine CORE workflow")
