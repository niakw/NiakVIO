#!/usr/bin/env python3
"""Backward-compatible entry point for the hardened NuvioTV target-media resolver.

Provider configs and release guards still reference the V4 path.  Keep that
stable API while delegating to the V5 implementation, which retains all V4
markers/compatibility helpers and adds site -> player -> media playback context.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent
IMPL = ROOT / "nuvio_tv_target_media_v5.py"

_spec = importlib.util.spec_from_file_location("nuvio_tv_target_media_v5_impl", IMPL)
if _spec is None or _spec.loader is None:
    raise RuntimeError(f"cannot import {IMPL}")
_impl = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_impl)

# Re-export the implementation surface because existing regression tests import
# V4 helpers/constants directly (ABS_V3/ABS_V4, TARGET, strip helpers, etc.).
for _name in dir(_impl):
    if not _name.startswith("__"):
        globals()[_name] = getattr(_impl, _name)
