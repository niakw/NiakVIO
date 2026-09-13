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
assert int(data.get("hubCount") or 0) == 46, data.get("hubCount")
assert len(ids) == 46, len(ids)

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

print("native Hub-46 execution scope contract tests passed: providers=46")
