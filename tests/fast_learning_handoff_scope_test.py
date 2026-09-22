#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts"/"select_fast_learning_handoff.py"
spec=importlib.util.spec_from_file_location("fast_handoff", SCRIPT)
assert spec and spec.loader
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

with TemporaryDirectory() as td:
    root=Path(td)
    trigger=root/"trigger"
    trigger.write_text(
        "reason: fast-brain-strategy-exhaustion\n"
        "expected_scope: current-fast-repair-handoff-only\n",
        encoding="utf-8",
    )
    handoff={
        "providers":{
            "current-a":{"owner":"LEARN","status":"pending"},
            "current_b":{"owner":"LEARN","status":"pending"},
            "old-one":{"owner":"LEARN","status":"pending"},
            "done-one":{"owner":"LEARN","status":"resolved"},
            "repair-owned":{"owner":"REPAIR","status":"pending"},
        }
    }
    census={"repairQueue":["current-a","current-b","done-one","repair-owned"]}
    assert mod.select(trigger,handoff,census)==["current-a","current-b"]

    trigger.write_text(
        "reason: fair-share-repair-strategy-learning-after-causal-census\n"
        "expected_scope: current-nine-provider-repair-handoff-only\n"
        "execution_mode: targeted-fast-handoff-v6-cohort-stage-bounded-slices-content-addressed-proposal\n",
        encoding="utf-8",
    )
    assert mod.select(trigger,handoff,census)==["current-a","current-b"]

    trigger.write_text(
        "reason: fair-share-repair-strategy-learning-after-causal-census\n"
        "expected_scope: current-nine-provider-repair-handoff-only\n",
        encoding="utf-8",
    )
    assert mod.select(trigger,handoff,census)==[]

    trigger.write_text("reason: scheduled-learning\n",encoding="utf-8")
    assert mod.select(trigger,handoff,census)==[]

source=SCRIPT.read_text(encoding="utf-8")
for required in (
    "fast-brain-strategy-exhaustion",
    "current-fast-repair-handoff-only",
    "targeted-fast-handoff",
    "provider-repair-handoff",
    "repairQueue",
    'str(row.get("owner") or "") != "LEARN"',
    'str(row.get("status") or "") != "pending"',
):
    assert required in source, required

print("fast Learning handoff scope contract passed")
