#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATCH_DIR = ROOT / "scripts/provider_patches"
PATCH = PATCH_DIR / "anime_sama_runtime_v1.py"
if str(PATCH_DIR) not in sys.path:
    sys.path.insert(0, str(PATCH_DIR))

spec = importlib.util.spec_from_file_location("anime_sama_runtime_v1", PATCH)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

source = '''"use strict";\nasync function getStreams(){return [];}\nmodule.exports={getStreams};\n'''
out = module.apply(source)
assert module.MANAGED_FIX_ID == "PROVIDER.ANIME-SAMA.RUNTIME.V1"
assert "NIAKVIO_ANIME_SAMA_RUNTIME_V1" in out
assert "episodes.js" in out
assert "/template-php/defaut/fetch.php" in out
assert "catalogue-episodes-js-v1" in out
assert "upstreamJsExecuted" in out and "false" in out
assert out.count("NIAKVIO_ANIME_SAMA_RUNTIME_V1") >= 1
print("anime-sama runtime v1 contract passed")
