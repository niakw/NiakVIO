#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCOPE = ROOT / "scripts/scope_native_reader_learning_runtime.py"
WORKFLOW = ROOT / ".github/workflows/native-android-route-reader.yml"

scope = SCOPE.read_text(encoding="utf-8")
workflow = WORKFLOW.read_text(encoding="utf-8")
for required in (
    "gate_native_cross_client_runtime.cjs",
    "FIELD_NATIVE_READER_RUNTIME_PREBRAIN_GATE",
    '"--require-clients", "mobile,tv"',
    '"--min-comparisons", "3"',
    "incomplete pre-Brain runtime evidence",
):
    assert required in scope, required

scope_call = "scope_native_reader_learning_runtime.py filter"
brain_step = "Materialize bounded generic Brain mutations across three representative routes"
assert scope_call in workflow
assert brain_step in workflow
assert workflow.index(scope_call) < workflow.index(brain_step)

with tempfile.TemporaryDirectory(dir=ROOT) as raw:
    temp = Path(raw)
    source = temp / "state.json"
    output = temp / "scoped.json"
    source.write_text(json.dumps({"nativeReaderRepairMemory": {"entries": []}}), encoding="utf-8")
    env = dict(os.environ)
    env.pop("GITHUB_WORKSPACE", None)
    run = subprocess.run([
        "python3", str(SCOPE), "filter",
        "--state", str(source),
        "--runtime-fingerprint", "tv=abc;mobile=def",
        "--output", str(output),
    ], cwd=ROOT, env=env, text=True, capture_output=True)
    assert run.returncode == 0, run.stdout + run.stderr
    assert output.is_file()

print("native runtime pre-Brain boundary contract passed")
