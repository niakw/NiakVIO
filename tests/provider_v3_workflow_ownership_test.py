#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
policy=json.loads((ROOT/"automation/provider-v3-architecture.json").read_text(encoding="utf-8"))
sync=(ROOT/".github/workflows/sync.yml").read_text(encoding="utf-8")
learn=(ROOT/".github/workflows/brain-learning-lab.yml").read_text(encoding="utf-8")
manual=(ROOT/".github/workflows/provider-v3-reconstruct-all.yml").read_text(encoding="utf-8") if (ROOT/".github/workflows/provider-v3-reconstruct-all.yml").exists() else ""
core=(ROOT/".github/workflows/core-media-finalize-main.yml").read_text(encoding="utf-8")
domain=(ROOT/".github/workflows/domain-refresh.yml").read_text(encoding="utf-8")
for mode in ("quick","deep"):
    assert policy["routine"][mode]["repair_allowed"] is False
    assert policy["routine"][mode]["provider_fix_mutation_allowed"] is False
for forbidden in (
    "run_adaptive_deep_repair.py",
    "run_adaptive_quick_repair.py",
    "Repair unresolved provider structures",
    "promote_candidates.py",
    "promote_refresh_candidates.py",
    "quarantine_catalogue_audit_failures.py",
):
    assert forbidden not in sync, f"routine pipeline still mutates/repairs providers: {forbidden}"
for required in (
    "build_published_provider_stage.py",
    "build_observational_health_report.py",
    "resolve_provider_hubs.py",
    "verify_provider_v3_reverse_rebuild.py",
):
    assert required in sync, required
assert "--apply" not in sync.split("Verify current domains and hubs without mutation",1)[1].split("- name:",1)[0]
for required in ("run_brain_learning_queue.py","build_brain_repair_proposal.py","brain-repair/proposal"):
    assert required in learn, f"LEARN lost repair/proposal ownership: {required}"
if manual:
    for required in ("materialize_provider_v3_all.py","verify_provider_v3_reverse_rebuild.py","96"):
        assert required in manual
for forbidden in ("--apply","git push origin HEAD:main","reapply_published_overrides.py\n"):
    assert forbidden not in core, f"Core gate must be read-only: {forbidden}"
assert "contents: write" not in core
assert "--apply" not in domain
assert "contents: write" not in domain
assert "git push" not in domain
print("provider v3 workflow ownership contract passed")
