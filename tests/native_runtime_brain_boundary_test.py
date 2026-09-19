#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCOPE = ROOT / "scripts/scope_native_reader_learning_runtime.py"
WORKFLOWS = [
    ROOT / ".github/workflows/native-tv-route-reader.yml",
    ROOT / ".github/workflows/native-mobile-android-reader.yml",
    ROOT / ".github/workflows/native-mobile-ios-reader.yml",
    ROOT / ".github/workflows/native-desktop-reader-acceptance.yml",
]
BRAIN = ROOT / ".github/workflows/brain-learning-lab.yml"

scope = SCOPE.read_text(encoding="utf-8")
workflows = [path.read_text(encoding="utf-8") for path in WORKFLOWS]
brain = BRAIN.read_text(encoding="utf-8")
for required in (
    "gate_native_cross_client_runtime.cjs",
    "FIELD_NATIVE_READER_RUNTIME_PREBRAIN_GATE",
    '"--require-clients", "mobile,tv"',
    '"--min-comparisons", "3"',
    "incomplete pre-Brain runtime evidence",
):
    assert required in scope, required

# Native device Labs are evidence-only and never run pre-Brain mutation logic.
# Cross-client/runtime scoping remains a fail-closed reusable primitive, while the
# independent Brain workflow consumes sanitized native-reader summaries later.
scope_call = "scope_native_reader_learning_runtime.py filter"
for workflow in workflows:
    assert scope_call not in workflow
    assert "Materialize bounded generic Brain mutations" not in workflow
    assert "build_native_reader_brain_repair.py" not in workflow
assert "--native-summary brain-learning-input/native-reader-summary.json" in brain
assert "build_native_reader_learning_summary.py" in brain

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
