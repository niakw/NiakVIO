#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

spec = importlib.util.spec_from_file_location(
    "clean_proposal_provenance",
    SCRIPTS / "materialize_clean_provider_reconstruction.py",
)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

rows = {
    "published": {
        "id": "published",
        "source": "existing",
        "base_source": "legacy",
    }
}
existing = mod.ensure_proposal_provenance_row(
    rows,
    "published",
    {"upstream_id": "published"},
    "pending-niakvio-clean-reconstruction-v2",
    "2026-09-20T00:00:00+00:00",
)
assert existing is rows["published"]

fresh = mod.ensure_proposal_provenance_row(
    rows,
    "fluneo",
    {
        "canonical_id": "fluneo",
        "upstream_id": "fluneo",
        "upstream_filename": "fluneo.js",
    },
    "new-niakvio-clean-seed",
    "2026-09-20T00:00:00+00:00",
)
assert fresh["id"] == "fluneo"
assert fresh["proposal_only"] is True
assert fresh["publication_allowed"] is False
assert fresh["production_writes_allowed"] is False
assert fresh["activation_eligible"] is False
assert fresh["strict_activation_eligible"] is False
assert fresh["runtime_evidence_eligible"] is False
assert fresh["activation_blockers"] == ["canonical_pipeline_proof_required"]
assert fresh["source"] == "niakvio-learning-clean-proposal"
assert fresh["upstream_code_role"] == "knowledge-only"
assert fresh["upstream_code_executed"] is False
assert fresh["legacy_provider_js_executed_for_reconstruction"] is False
assert fresh["published_filename"] is None
assert fresh["sha256"] is None
assert fresh["patched_sha256"] is None

try:
    mod.ensure_proposal_provenance_row(
        rows,
        "broken-existing",
        {"upstream_id": "broken-existing"},
        "pending-niakvio-clean-reconstruction-v2",
        "2026-09-20T00:00:00+00:00",
    )
except ValueError as exc:
    assert "missing provenance row" in str(exc)
else:
    raise AssertionError("missing provenance on an existing/pending provider must fail closed")

print("Learning new-provider proposal provenance contract passed")
