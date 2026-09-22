#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts"/"run_brain_learning_queue.py"
spec=importlib.util.spec_from_file_location("brain_learning_queue",SCRIPT)
assert spec and spec.loader
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

order=["a1","a2","b1","b2","b3","local"]
plan={
    "groups":[
        {"groupId":"route|html","providers":["a1","a2"]},
        {"groupId":"terminal|embed","providers":["b1","b2","b3"]},
    ]
}
actual,groups=mod.causal_batch_round_robin(order,plan)
assert actual==["a1","b1","local","a2","b2","b3"],actual
assert groups==["route|html","terminal|embed","provider-local:local"],groups
assert sorted(actual)==sorted(order)

source=SCRIPT.read_text(encoding="utf-8")
for required in (
    "causal_batch_round_robin",
    "provider-repair-batch-plan-latest.json",
    "causal-batch-round-robin",
    "fastRepairHandoffCausalBatchCount",
):
    assert required in source,required

print("Brain Learning causal batch round-robin tests passed")
