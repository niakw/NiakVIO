#!/usr/bin/env python3
from __future__ import annotations

import base64
import importlib.util
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
PATCH = SCRIPTS_DIR / "provider_patches/anime_sama_runtime_v1.py"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

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
assert f"STARTFIX:{module.MANAGED_FIX_ID}" in out
assert f"CLOSEFIX:{module.MANAGED_FIX_ID}" in out
match = re.search(rf"/\* FIXDATA:{re.escape(module.MANAGED_FIX_ID)}:([^ ]+) \*/", out)
assert match, "managed FIXDATA marker missing"
data = json.loads(base64.urlsafe_b64decode(match.group(1)).decode("utf-8"))
assert data["runtimeFamily"] == "catalogue-episodes-js-v1"
assert data["legacyExecutableSeed"] is False
assert data["upstreamJsExecuted"] is False
assert out.count("NIAKVIO_ANIME_SAMA_RUNTIME_V1") >= 1
print("anime-sama runtime v1 contract passed")
