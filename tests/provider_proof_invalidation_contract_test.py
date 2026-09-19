#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/check_provider_non_regression_v1.py"
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

    print("PROVIDER_PROOF_INVALIDATION_CONTRACT_OK allwish_lanes=movie,tv provider_positive=invalidated malformed=fail_closed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
