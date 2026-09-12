#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "upgrade_anime_only_capability_v35.py"
spec = importlib.util.spec_from_file_location("v35", SCRIPT)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)

sample = {
    "published_types": ["movie", "anime"],
    "notes": [],
    "repair_disposition": {
        "requiredLanes": ["anime", "movie"],
        "provenLanes": ["anime"],
        "missingLanes": ["movie"],
        "completeCapabilityProof": False,
        "laneStatuses": {"anime": ["playable_verified"], "movie": ["wrong_content"]},
    },
    "route_proof": {
        "runtimePlanSemanticLanes": ["anime"],
        "canonicalExecutionAuthority": {
            "supportedLanes": ["anime", "movie"],
            "coveredLanes": ["anime", "movie"],
            "missingLanes": [],
        },
        "canonicalExecutionPreference": [{"owner": "apiRecipe", "index": 0, "lanes": ["anime", "movie"]}],
    },
    "live_route_gate": {
        "required_types": ["anime", "movie"],
        "validated_types": ["anime", "movie"],
        "missing_types": [],
        "completion_state": "declared-types-qualified",
        "declared_type_coverage_ratio": 1.0,
        "effective_coverage_ratio": 1.0,
        "required_coverage_ratio": 1.0,
    },
}

p = copy.deepcopy(sample)
mod.close_patch(p)
assert p["published_types"] == ["anime"]
assert p["repair_disposition"]["requiredLanes"] == ["anime"]
assert p["repair_disposition"]["missingLanes"] == []
assert p["repair_disposition"]["completeCapabilityProof"] is True
assert p["repair_disposition"]["laneStatuses"]["movie"] == ["wrong_content"], "historical evidence must remain"
a = p["route_proof"]["canonicalExecutionAuthority"]
assert a["supportedLanes"] == ["anime"] and a["coveredLanes"] == ["anime"]
assert p["route_proof"]["canonicalExecutionPreference"][0]["lanes"] == ["anime"]
g = p["live_route_gate"]
assert g["required_types"] == ["anime"] and g["validated_types"] == ["anime"]
assert g["completion_state"] == "declared-types-qualified" and g["effective_coverage_ratio"] == 1.0

before = copy.deepcopy(p)
mod.close_patch(p)
assert p == before, "V35 capability closure must be idempotent"
print("anime-only capability closure V35 tests passed")
