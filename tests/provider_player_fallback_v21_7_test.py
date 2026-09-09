#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "upgrade_provider_player_fallback_v21_7.py"

spec = importlib.util.spec_from_file_location("v217", SCRIPT)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

module.patch_worker(); module.patch_proof(); module.patch_recovery(); module.patch_materializer(); module.patch_base()
module.validate_worker(); module.validate_proof(); module.validate_recovery(); module.validate_materializer(); module.validate_base()

base = module.BASE.read_text(encoding="utf-8")
assert base.count(module.MARKER) == 1
start = base.index("function _spv216FallbackStreams(rows)")
end = base.index("async function _resolveProviderValuePlan", start)
helper = base[start:end]
assert "stream.__nuvioCorrelatedPlayerFallbackV1 = { url };" in helper
assert "_spv216PlayerFallbackEligible(url)" in helper
assert "_directMedia(url)" in base

section = base.split(f"/* {module.MARKER} */", 1)[1].split("async function _resolveProviderValuePlan", 1)[0].casefold()
for token in ("animesama", "animevostfr", "jujutsu", "sibnet", "sendvid"):
    assert token not in section

print("provider player fallback V21.7 tests passed")
