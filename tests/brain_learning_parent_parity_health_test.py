#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_adaptive_quick_repair.py"
spec = importlib.util.spec_from_file_location("brain_learning_parent_parity", SCRIPT)
assert spec and spec.loader
quick = importlib.util.module_from_spec(spec)
spec.loader.exec_module(quick)

calls: list[str] = []
original_base = quick._base_run_health
original_plan = quick._plan_quick_results
original_mode = os.environ.get("NUVIO_BRAIN_PLANNER_MODE")
original_parity = os.environ.get("NUVIO_BRAIN_LEARNING_PARENT_PARITY_MODE")

def fake_run_health(**kwargs):
    calls.append(str(kwargs["mode"]))
    return {"results": []}

try:
    quick._base_run_health = fake_run_health
    quick._plan_quick_results = lambda *_args, **_kwargs: None

    os.environ["NUVIO_BRAIN_PLANNER_MODE"] = "learning"
    os.environ["NUVIO_BRAIN_LEARNING_PARENT_PARITY_MODE"] = "deep"
    assert quick._learning_parent_parity_mode() == "deep"
    quick._quick_run_health(
        stage=ROOT,
        registry_path=ROOT / "provider_catalog.json",
        output_dir=ROOT,
        mode="quick",
    )
    assert calls[-1] == "deep", calls

    os.environ.pop("NUVIO_BRAIN_LEARNING_PARENT_PARITY_MODE", None)
    assert quick._learning_parent_parity_mode() == "quick"
    quick._quick_run_health(
        stage=ROOT,
        registry_path=ROOT / "provider_catalog.json",
        output_dir=ROOT,
        mode="quick",
    )
    assert calls[-1] == "quick", calls

    os.environ["NUVIO_BRAIN_PLANNER_MODE"] = "repair"
    os.environ["NUVIO_BRAIN_LEARNING_PARENT_PARITY_MODE"] = "deep"
    assert quick._learning_parent_parity_mode() == "quick"
    quick._quick_run_health(
        stage=ROOT,
        registry_path=ROOT / "provider_catalog.json",
        output_dir=ROOT,
        mode="quick",
    )
    assert calls[-1] == "quick", calls
finally:
    quick._base_run_health = original_base
    quick._plan_quick_results = original_plan
    if original_mode is None:
        os.environ.pop("NUVIO_BRAIN_PLANNER_MODE", None)
    else:
        os.environ["NUVIO_BRAIN_PLANNER_MODE"] = original_mode
    if original_parity is None:
        os.environ.pop("NUVIO_BRAIN_LEARNING_PARENT_PARITY_MODE", None)
    else:
        os.environ["NUVIO_BRAIN_LEARNING_PARENT_PARITY_MODE"] = original_parity

source = SCRIPT.read_text(encoding="utf-8")
assert "FIELD_BRAIN_LEARNING_PARENT_PARITY health_mode=deep" in source
assert 'os.environ.get("NUVIO_BRAIN_LEARNING_PARENT_PARITY_MODE")' in source

print("Brain Learning published-parent health parity contract passed")
