#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
PATCHES = SCRIPTS / "provider_patches"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(PATCHES))
SCRIPT = SCRIPTS / "register_dle_anime_runtime_v1.py"
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

# Facades must remain constructible against the exact shared parser revision.
# This catches stale textual anchors before the expensive rematerialization step.
import french_manga_dle_runtime_v1 as french_manga
import voiranime_homes_dle_runtime_v1 as voiranime_homes
fm_wrapper = french_manga._french_manga_wrapper()
vh_wrapper = voiranime_homes._voiranime_homes_wrapper()
assert french_manga.SEARCH_ITEM_MARKER in fm_wrapper
assert voiranime_homes.SEARCH_ITEM_MARKER in vh_wrapper
assert "function seasonSignal(row,season)" in fm_wrapper
assert "function seasonSignal(row,season)" in vh_wrapper

print("provider-owned DLE facade registration/apply test passed: french-manga + voiranime-homes")
