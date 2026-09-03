#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
policy=json.loads((ROOT/"automation/provider-v3-architecture.json").read_text(encoding="utf-8"))
sync=(ROOT/".github/workflows/sync.yml").read_text(encoding="utf-8")
learn=(ROOT/".github/workflows/brain-learning-lab.yml").read_text(encoding="utf-8")
manual=(ROOT/".github/workflows/provider-v3-reconstruct-all.yml").read_text(encoding="utf-8")
core=(ROOT/".github/workflows/core-media-finalize-main.yml").read_text(encoding="utf-8")
domain=(ROOT/".github/workflows/domain-refresh.yml").read_text(encoding="utf-8")
for mode in ("quick","deep"):
    assert policy["routine"][mode]["repair_allowed"] is False
    assert policy["routine"][mode]["provider_fix_mutation_allowed"] is False
    assert policy["routine"][mode]["provider_reconstruction_allowed"] is False
for name,text in (("Quick/Deep",sync),("Core",core)):
    for forbidden in ("run_adaptive_deep_repair.py","run_adaptive_quick_repair.py","promote_candidates.py","promote_refresh_candidates.py","materialize_provider_v3_all.py","verify_provider_v3_reverse_rebuild.py","--apply"):
        assert forbidden not in text, f"{name} may not mutate/reconstruct providers: {forbidden}"
    assert "audit_provider_v3_static.py" in text
for required in ("run_brain_learning_queue.py","build_brain_repair_proposal.py","brain-repair/proposal"):
    assert required in learn
assert "--include-disabled" in learn or "including disabled providers" in learn
for required in ("materialize_provider_v3_all.py","verify_provider_v3_reverse_rebuild.py","96"):
    assert required in manual
assert "Refuse direct main mutation" in manual
assert "--apply" in domain and "--domain-only" in domain
assert "update_provider_v3_domain_config.py" in domain and "audit_provider_v3_static.py" in domain
assert "materialize_provider_v3_all.py" not in domain and "verify_provider_v3_reverse_rebuild.py" not in domain
for forbidden in ("run_adaptive_deep_repair.py","run_adaptive_quick_repair.py","promote_candidates.py","promote_refresh_candidates.py"):
    assert forbidden not in domain
print("provider v3 workflow ownership contract passed")
