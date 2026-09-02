#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
policy=json.loads((ROOT/"automation/provider-v3-architecture.json").read_text(encoding="utf-8"))
sync=(ROOT/".github/workflows/sync.yml").read_text(encoding="utf-8")
learn=(ROOT/".github/workflows/brain-learning-lab.yml").read_text(encoding="utf-8")
manual=(ROOT/".github/workflows/provider-v3-reconstruct-all.yml").read_text(encoding="utf-8") if (ROOT/".github/workflows/provider-v3-reconstruct-all.yml").exists() else ""

assert policy["routine"]["deep"]["repair_allowed"] is False
assert policy["routine"]["learning"]["repair_allowed"] is True
assert policy["routine"]["learning"]["proposal_pr_only"] is True
for forbidden in (
    "run_adaptive_deep_repair.py",
    "run_adaptive_quick_repair.py",
    "runtime_repair.py --",
    "Repair unresolved provider structures",
):
    assert forbidden not in sync, f"DEEP/routine pipeline still repairs providers: {forbidden}"
for required in ("run_brain_learning_queue.py","build_brain_repair_proposal.py","brain-repair/proposal"):
    assert required in learn, f"LEARN lost repair/proposal ownership: {required}"
if manual:
    for required in ("materialize_provider_v3_all.py","verify_provider_v3_reverse_rebuild.py","96"):
        assert required in manual
print("provider v3 workflow ownership contract passed")
