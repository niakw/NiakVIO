#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts"/"run_brain_learning_queue.py"
spec=importlib.util.spec_from_file_location("brain_learning_child_isolation",SCRIPT)
assert spec and spec.loader
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def registry_payload():
    return {
        "candidates":[{
            "key":"published:demo",
            "canonical_id":"demo",
            "local_path":"providers/demo.js",
            "sha256":"a"*64,
        }]
    }


def mutate_registry(path: Path):
    value=json.loads(path.read_text(encoding="utf-8"))
    value["candidates"][0]["repair_history"]=[{"accepted":True,"profile":"synthetic"}]
    path.write_text(json.dumps(value),encoding="utf-8")


with tempfile.TemporaryDirectory() as tmp:
    tmp=Path(tmp)
    stage=tmp/"stage"
    stage.mkdir()
    registry=stage/"candidates.json"
    registry.write_text(json.dumps(registry_payload()),encoding="utf-8")
    output=tmp/"attempt-114"
    state=tmp/"state.json"
    state.write_text("{}",encoding="utf-8")

    calls=[]
    original_run=mod.run
    try:
        def fake_run(cmd,*,env,deadline,cwd=mod.ROOT,allow_fail=False):
            calls.append(list(cmd))
            if "run_brain_learning_sandbox.py" in " ".join(cmd):
                mutate_registry(registry)
                output.mkdir(parents=True,exist_ok=True)
                (output/"repair-report.json").write_text(json.dumps({
                    "rounds":[{"attempts":[{"profile":"search_contract_inference_v1"}],"accepted":[]}],
                    "brain":{"plans":{}},
                }),encoding="utf-8")
                # Reproduce the real failure: child dies before health-results.json.
                return subprocess.CompletedProcess(cmd,1,"","synthetic crash")
            raise AssertionError("validator must not run for incomplete child")
        mod.run=fake_run
        result=mod.repair_attempt("demo",stage,registry,output,state,time.time()+30)
    finally:
        mod.run=original_run

    assert result["accepted"]==0,result
    assert result["validationStatus"]=="rejected_incomplete_child",result
    assert "missing_health_results" in result["validationReason"],result
    assert json.loads(registry.read_text(encoding="utf-8"))==registry_payload()
    assert len(calls)==1,calls

with tempfile.TemporaryDirectory() as tmp:
    tmp=Path(tmp)
    stage=tmp/"stage"
    stage.mkdir()
    registry=stage/"candidates.json"
    registry.write_text(json.dumps(registry_payload()),encoding="utf-8")
    output=tmp/"attempt-2"
    state=tmp/"state.json"
    state.write_text("{}",encoding="utf-8")
    calls=[]
    original_run=mod.run
    try:
        def fake_run_validator(cmd,*,env,deadline,cwd=mod.ROOT,allow_fail=False):
            calls.append(list(cmd))
            joined=" ".join(cmd)
            if "run_brain_learning_sandbox.py" in joined:
                mutate_registry(registry)
                output.mkdir(parents=True,exist_ok=True)
                (output/"repair-report.json").write_text(json.dumps({
                    "rounds":[{"attempts":[{"profile":"search_contract_inference_v1"}],"accepted":[{"provider":"demo"}]}],
                    "accepted_repairs":1,
                    "brain":{"plans":{}},
                }),encoding="utf-8")
                (output/"health-results.json").write_text(json.dumps({"mode":"quick","results":[]}),encoding="utf-8")
                return subprocess.CompletedProcess(cmd,0,"","")
            if "validate_automatic_repair_results.py" in joined:
                raise RuntimeError("synthetic validator rejection")
            raise AssertionError(joined)
        mod.run=fake_run_validator
        result=mod.repair_attempt("demo",stage,registry,output,state,time.time()+30)
    finally:
        mod.run=original_run

    assert result["accepted"]==0,result
    assert result["validationStatus"]=="rejected_validator",result
    assert json.loads(registry.read_text(encoding="utf-8"))==registry_payload()
    assert len(calls)==2,calls

print("Brain Learning child isolation contract passed")
