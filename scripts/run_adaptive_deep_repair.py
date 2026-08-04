#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Run deep_repair_loop with the provider-agnostic adaptive runtime layer."""
from __future__ import annotations

import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADAPTIVE = ROOT / "scripts" / "adaptive_runtime"
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(ADAPTIVE))
sys.path.insert(1, str(SCRIPTS))

import runtime_repair  # noqa: E402

loaded = Path(runtime_repair.__file__).resolve()
expected = (ADAPTIVE / "runtime_repair.py").resolve()
if loaded != expected:
    raise SystemExit(f"adaptive runtime layer not loaded: {loaded} != {expected}")

sys.argv[0] = str(SCRIPTS / "deep_repair_loop.py")
runpy.run_path(sys.argv[0], run_name="__main__")
