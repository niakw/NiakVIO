#!/usr/bin/env python3
"""Repository continuity gate for durable positive Brain programs.

The committed durable memory must already contain every historical strict
accepted program that the current compiler can still recover. Recovery itself is
tested separately; this test prevents a future evidence-only commit from
silently resetting the committed memory to an older/empty state.
"""
from __future__ import annotations

import importlib.util
import json
import shutil
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "recover_brain_positive_program_memory.py"
MEMORY = ROOT / "automation" / "brain-positive-program-memory.json"

spec = importlib.util.spec_from_file_location("recover_positive_repo", SCRIPT)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)


def fingerprints(path: Path) -> set[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return {
        str(row.get("fingerprint") or "")
        for row in data.get("entries") or []
        if isinstance(row, dict) and str(row.get("fingerprint") or "")
    }


reports = sorted(
    path
    for path in (ROOT / "automation").glob("provider-brain-repair-*.json")
    if path.is_file() and path.name != "provider-brain-repair-latest.json"
)

with tempfile.TemporaryDirectory() as raw:
    candidate = Path(raw) / "brain-positive-program-memory.json"
    shutil.copyfile(MEMORY, candidate)
    before = fingerprints(candidate)
    result = mod.recover(reports, memory_path=candidate)
    after = fingerprints(candidate)

assert before == after, {
    "missingRecoverableFingerprints": sorted(after - before),
    "before": len(before),
    "after": len(after),
    "recovery": result,
}
assert result["durableRecordCount"] == len(before), result

print(
    "Brain positive program repository continuity passed "
    f"records={len(before)} providers={','.join(result['durableProviders']) or 'none'}"
)
