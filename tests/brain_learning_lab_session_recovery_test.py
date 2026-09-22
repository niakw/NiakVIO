#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts"/"run_brain_learning_queue.py"
spec=importlib.util.spec_from_file_location("brain_learning_queue_session_recovery",SCRIPT)
assert spec and spec.loader
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class FakeProcess:
    def __init__(self, code):
        self.code=code
    def poll(self):
        return self.code

class FakeSession:
    def __init__(self, code):
        self.process=FakeProcess(code)

alive=FakeSession(None)
created=[]
def factory(deadline):
    row=FakeSession(None)
    row.deadline=deadline
    created.append(row)
    return row

same=mod.ensure_learning_lab_session(alive,123.0,factory=factory)
assert same is alive
assert created==[]

dead=FakeSession(0)
fresh=mod.ensure_learning_lab_session(dead,456.0,factory=factory)
assert fresh is created[-1]
assert fresh is not dead
assert fresh.deadline==456.0
assert fresh.process.poll() is None

source=SCRIPT.read_text(encoding="utf-8")
call=source.index("lab_session = ensure_learning_lab_session(")
lab=source.index("final_lab = run_lab(",call)
assert call < lab

print("Brain Learning Lab-session recovery contract passed")
