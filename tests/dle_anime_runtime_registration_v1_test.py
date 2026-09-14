#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "register_dle_anime_runtime_v1.py"
spec = importlib.util.spec_from_file_location("register_dle_anime_runtime_v1", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

data = json.loads((ROOT / "provider-overrides.json").read_text(encoding="utf-8"))
changed = module.apply_document(data)
module.validate_document(data)
for pid, target in module.TARGETS.items():
    row = data["provider_patches"][pid]
    lego = target["lego"]
    assert module.GENERIC_LEGO not in row["provider_lego_scripts"]
    assert lego in row["provider_lego_scripts"]
    assert row["provider_lego_options"][lego]["base"] == target["base"]
    assert row["provider_lego_options"][lego]["provider"] == pid
    assert row["proof_search_bases"] == [target["base"]]
assert isinstance(changed, bool)
print("provider-owned DLE facade registration test passed: french-manga + voiranime-homes")
