#!/usr/bin/env python3
"""Versioned Nuvio features must live inside the exact audited client range."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

spec = importlib.util.spec_from_file_location(
    "nuvio_runtime_compatibility",
    ROOT / "scripts" / "nuvio_runtime_compatibility.py",
)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

errors = module.validate_matrix()
assert not errors, errors

matrix = json.loads(
    (ROOT / "automation" / "nuvio-client-compatibility-matrix.json").read_text(encoding="utf-8")
)
for client_id, row in matrix["clients"].items():
    minimum = int(row["supported_version_code"]["min"])
    maximum = int(row["supported_version_code"]["max"])
    seen = set()
    for feature in row.get("versioned_features") or []:
        feature_id = str(feature.get("id") or "").strip()
        assert feature_id and feature_id not in seen, (client_id, feature_id)
        seen.add(feature_id)
        feature_min = int(feature["min_version_code"])
        assert minimum <= feature_min <= maximum, (client_id, feature_id, feature_min, minimum, maximum)
        assert isinstance(feature.get("brain_provider_mutation_required"), bool), (client_id, feature_id)

desktop = matrix["clients"]["nuvio-desktop"]
readiness = next(
    feature for feature in desktop["versioned_features"]
    if feature["id"] == "plugin-selection-readiness-v1"
)
assert readiness["min_version_code"] == 25
assert readiness["status"] == "upstream-reported-fixed-native-proof-required"
assert readiness["issue_state"] == "closed-not-planned"
assert "Native Lab" in readiness["evidence"]

source = (ROOT / "scripts" / "nuvio_runtime_compatibility.py").read_text(encoding="utf-8")
assert "outside audited range" in source
assert "versioned_features must be an array" in source

print("NUVIO_VERSIONED_FEATURE_CONTRACT_OK")
