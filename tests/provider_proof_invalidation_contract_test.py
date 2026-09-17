#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
SCRIPT = SCRIPTS / "check_provider_non_regression_v1.py"
REGISTRY = ROOT / "automation/provider-proof-invalidations.json"


def load_module():
    spec = importlib.util.spec_from_file_location("provider_non_regression", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    module = load_module()
    rows = module.load_proof_invalidations(REGISTRY)
    assert "allwish" in rows, rows
    row = rows["allwish"]
    assert module.invalidated_lanes_for(rows, "ALLWISH") == {"movie", "tv"}
    assert row["invalidateProviderPositive"] is True
    assert row["contradictionAuthority"] == "cross-fixture-content-identity-contradiction"
    assert len(row["evidenceRefs"]) >= 2

    malformed = {
        "schemaVersion": 1,
        "authority": "provider-proof-invalidation-v1",
        "providers": {
            "bad": {
                "active": True,
                "invalidatedLanes": ["movie"],
                "invalidateProviderPositive": True,
                "contradictionAuthority": "",
                "reasonCodes": [],
                "evidenceRefs": []
            }
        }
    }
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "bad.json"
        path.write_text(json.dumps(malformed), encoding="utf-8")
        try:
            module.load_proof_invalidations(path)
        except ValueError:
            pass
        else:
            raise AssertionError("malformed proof invalidation registry must fail closed")

    # An evidence-backed contradiction must remove the exact same lanes from
    # both proof obligations and semantic floor. Unrelated semantic losses stay hard.
    module.changed_scope = lambda matrix, base_ref, force_all: (["allwish"], [], False)
    module.git_json = lambda ref, path: {}
    module.current_activation_debt = lambda: {}
    matrix = {"providers": [{
        "provider": "allwish",
        "snapshotStates": {"5.21.36": {"icon": module.GREEN}},
        "historicalVerifiedLanes": ["movie", "tv"],
        "contractDrift": {
            "currentSemanticTypes": ["anime"],
            "lostSemanticTypes": ["movie", "tv"],
            "hlsM3u8Lost": False,
        },
        "nonRegressionStatus": "CONTRACT_REGRESSION",
    }]}
    candidate = {"rows": [{"provider": "allwish", "semantic_type": "anime", "status": "no_streams"}]}
    module.load_proof_invalidations = lambda: {"allwish": row}
    result = module.candidate_gate(matrix, candidate, "HEAD^", True)
    obligation = result["obligations"]["allwish"]
    assert result["passed"] is True, result
    assert obligation["lostSemanticTypesRaw"] == ["movie", "tv"], obligation
    assert obligation["lostSemanticTypes"] == [], obligation

    module.load_proof_invalidations = lambda: {}
    result = module.candidate_gate(matrix, candidate, "HEAD^", True)
    assert result["passed"] is False, result
    assert result["obligations"]["allwish"]["lostSemanticTypes"] == ["movie", "tv"], result
    assert "semantic_capability_regression" in result["obligations"]["allwish"]["failures"], result

    print("PROVIDER_PROOF_INVALIDATION_CONTRACT_OK allwish_lanes=movie,tv semantic_floor=same-lanes-invalidated unrelated=fail_closed malformed=fail_closed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
