#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SCRIPT = ROOT / "scripts" / "upgrade_provider_player_fallback_v21_6.py"
BASE = ROOT / "scripts" / "provider_base_store.py"

spec = importlib.util.spec_from_file_location("upgrade_provider_player_fallback_v21_6", SCRIPT)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

current = BASE.read_text(encoding="utf-8")
mod.validate_base(current)

modern = "if (fallbackStreams.length) planStreams.push(...fallbackStreams);"
legacy = "if (fallbackStreams.length) return fallbackStreams;"
assert modern in current and legacy not in current
mod.validate_base(current.replace(modern, legacy, 1))

for missing in (
    modern,
    "const resolvedPlanStreams = _dedupeStreamRows(planStreams);",
    "if (resolvedPlanStreams.length) return resolvedPlanStreams.slice(0, 40);",
):
    broken = current.replace(missing, "", 1)
    try:
        mod.validate_base(broken)
    except AssertionError as exc:
        assert "evolved ProviderBase fallback contract missing" in str(exc), exc
    else:
        raise AssertionError(f"V21.6 accepted incomplete evolved fallback contract without {missing}")

print("Provider player fallback V21.6 current contract passed: legacy and complete accumulated V28-era behavior accepted, partial evolution rejected")
