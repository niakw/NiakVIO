#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "register_neko_sama_runtime_v2.py"
spec = importlib.util.spec_from_file_location("register_neko_sama_runtime_v2", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

data = json.loads((ROOT / "provider-overrides.json").read_text(encoding="utf-8"))
changed = module.apply_document(data)
module.validate_document(data)
row = data["provider_patches"]["neko-sama"]
assert module.LEGO in row["provider_lego_scripts"]
assert row["provider_lego_options"][module.LEGO]["base"] == "https://animes-sama.su"
assert isinstance(changed, bool)
print("neko-sama v2 runtime registration test passed")
