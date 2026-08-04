#!/usr/bin/env python3
"""Run the existing global repair harness with the adaptive runtime engine.

This wrapper does not select providers by name. The underlying harness keeps
its manifest-derived scope; only the deep-repair entry point is replaced so
that the adaptive runtime_repair module is loaded explicitly.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
HARNESS = ROOT / "scripts" / "local" / "test_global_provider_repair.py"
ADAPTIVE_RUNNER = ROOT / "scripts" / "run_adaptive_deep_repair.py"

spec = importlib.util.spec_from_file_location("nuvio_global_repair_harness", HARNESS)
if spec is None or spec.loader is None:
    raise RuntimeError(f"cannot load global repair harness: {HARNESS}")
harness = importlib.util.module_from_spec(spec)
spec.loader.exec_module(harness)

base_run = harness.run


def adaptive_run(*args: Any, env: dict[str, str] | None = None) -> None:
    rewritten = list(args)
    if len(rewritten) >= 2 and Path(str(rewritten[1])).name == "deep_repair_loop.py":
        rewritten[1] = ADAPTIVE_RUNNER
    base_run(*rewritten, env=env)


harness.run = adaptive_run

if __name__ == "__main__":
    raise SystemExit(harness.main())
