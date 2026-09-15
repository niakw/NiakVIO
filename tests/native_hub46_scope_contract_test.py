#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCOPE = ROOT / "automation/evidence/hub-lab-matrix-46.json"
data = json.loads(SCOPE.read_text(encoding="utf-8"))
rows = data.get("rows") or []
ids = {
    str(row.get("manifestId") or row.get("provider") or "").strip().casefold()
    for row in rows if isinstance(row, dict)
    if str(row.get("manifestId") or row.get("provider") or "").strip()
}
declared = int(data.get("hubCount") or 0)
assert declared > 0, declared
assert len(ids) == declared, (len(ids), declared)

os.environ["NIAKVIO_PROVIDER_SCOPE_MATRIX"] = "automation/evidence/hub-lab-matrix-46.json"
sys.path.insert(0, str(ROOT / "scripts"))

import prepare_native_corpus_client as client  # noqa: E402
assert client.provider_scope_ids() == ids

spec = importlib.util.spec_from_file_location("native_gate", ROOT / "scripts/gate_native_declared_provider_matrix.py")
assert spec and spec.loader
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)
assert gate.load_scope_ids(SCOPE) == ids

source = (ROOT / "scripts/prepare_native_ios_reader_acceptance.py").read_text(encoding="utf-8")
assert "scopeProviderIds" in source
assert "provider_scope_ids()" in source
assert "scopeProviderIds.isEmpty() || it.id.lowercase() in scopeProviderIds" in source

workflow_paths = (
    ROOT / ".github/workflows/native-desktop-reader-acceptance.yml",
    ROOT / ".github/workflows/native-mobile-android-reader.yml",
    ROOT / ".github/workflows/native-mobile-ios-reader.yml",
)
legacy_fixed_trio = "interstellar breaking-bad-s01e01 jujutsu-kaisen-s01e01"
for workflow in workflow_paths:
    text = workflow.read_text(encoding="utf-8")
    assert "NIAKVIO_PROVIDER_SCOPE_MATRIX: automation/evidence/hub-lab-matrix-46.json" in text, workflow
    assert "--scope-matrix" in text, workflow
    assert "automation/evidence/hub-lab-matrix-46.json" in text, workflow
    assert legacy_fixed_trio not in text, workflow

assert "rotating_corpus.py" in workflow_paths[0].read_text(encoding="utf-8")
assert "FIELD_ROTATING_CORPUS client=tv" in workflow_paths[1].read_text(encoding="utf-8")
assert "FIELD_ROTATING_CORPUS client=mobile" in workflow_paths[1].read_text(encoding="utf-8")

print(f"native active-scope rotating execution contract tests passed: providers={declared} workflows=3")
