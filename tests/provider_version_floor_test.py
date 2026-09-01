#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

PATCH = SCRIPTS / "reapply_published_overrides.py"
FLOORS = ROOT / "provider-version-floors.json"

spec = importlib.util.spec_from_file_location("reapply_published_overrides_version_floor_test", PATCH)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

floors_payload = json.loads(FLOORS.read_text(encoding="utf-8"))
floors = floors_payload.get("providers") or {}
assert len(floors) == 96, f"expected 96 exposed provider version floors, got {len(floors)}"

assert module.bump_provider_version("1.0.69", "1.0.70") == "1.0.71"
assert module.bump_provider_version("1.0.71", "1.0.70") == "1.0.72"
assert module.bump_provider_version("1.0.31", "1.0.35") == "1.0.36"
assert module.bump_provider_version("3.8.64", "3.8.66") == "3.8.67"
assert module.bump_provider_version("0.0.63", "0.0.64") == "0.0.65"

loaded = module.load_provider_version_floors()
for provider_id in ("kehflix", "goated", "nakios", "desiflix", "purstream", "flemmix", "4khdhubnew"):
    assert provider_id in loaded, provider_id

assert module.version_is_strictly_above_floor("1.0.71", "1.0.70")
assert not module.version_is_strictly_above_floor("1.0.70", "1.0.70")
assert not module.version_is_strictly_above_floor("1.0.69", "1.0.70")

print("provider version floor tests passed")
