#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts"/"audit_provider_quick_yield.py"
spec=importlib.util.spec_from_file_location("audit_provider_quick_yield_budget",SCRIPT)
assert spec and spec.loader
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

assert mod.PROVIDER_BUDGET >= mod.TIMEOUT
assert mod.PROVIDER_BUDGET <= 240

original_single=mod.run_single
original_budget=mod.PROVIDER_BUDGET
original_monotonic=mod.time.monotonic
try:
    mod.PROVIDER_BUDGET=90
    ticks=iter([0.0, 0.0, 60.0, 60.0, 90.1, 90.1, 90.1])
    mod.time.monotonic=lambda: next(ticks)
    calls=[]
    def fake_single(task, *, timeout_seconds=None):
        calls.append(timeout_seconds)
        return {
            "provider_id":task["provider_id"],
            "provider_name":task["provider_name"],
            "semantic_type":task["semantic_type"],
            "fixture_title":task["fixture"]["title"],
            "fixture":task["fixture"],
            "status":"timeout",
            "debug_stage":"timeout",
            "raw":0,
            "playable":0,
            "verified":0,
            "contradictions":0,
            "duration_ms":60000,
        }
    mod.run_single=fake_single
    task={
        "provider_id":"slow",
        "provider_name":"Slow",
        "semantic_type":"movie",
        "filename":"unused.js",
        "fixture":{"title":"one"},
        "fixtures":[{"title":"one"},{"title":"two"},{"title":"three"}],
    }
    row=mod.run(task)
    assert calls==[90,30],calls
    assert row["sample_count"]==2,row
    assert row["provider_budget_exhausted"] is True,row
    assert row["provider_budget_seconds"]==90,row
finally:
    mod.run_single=original_single
    mod.PROVIDER_BUDGET=original_budget
    mod.time.monotonic=original_monotonic

source=SCRIPT.read_text(encoding="utf-8")
for required in (
    "NIAKVIO_QUICK_YIELD_PROVIDER_BUDGET",
    "provider_budget_exhausted",
    "timeout_seconds=max(1, int(remaining))",
):
    assert required in source,required

print("provider quick-yield total provider budget contract passed")
