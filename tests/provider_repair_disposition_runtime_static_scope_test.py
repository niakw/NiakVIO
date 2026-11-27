#!/usr/bin/env python3
"""Repair disposition must not turn onboarding-pending rows into Brain runtime authority."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import finalize_provider_repair_disposition_v1_impl as disposition
from current_provider_scope import (
    pending_provider_ids,
    projection_runtime_visible_provider_ids,
)

runtime_ids = projection_runtime_visible_provider_ids()
knowledge = json.loads(
    (ROOT / "automation/provider-v3-static-knowledge.json").read_text(encoding="utf-8")
)
rows = knowledge.get("providers")
assert isinstance(rows, dict)
scoped = disposition.runtime_scoped_static_rows(
    rows,
    runtime_ids,
    require_complete=True,
)
assert set(scoped) == runtime_ids
pending = pending_provider_ids()
assert not (pending & set(scoped)), sorted(pending & set(scoped))

fixture = {
    "runtime-a": {"model": {}},
    "retained-b": {"model": {}},
    "pending-c": {"model": {}},
}
filtered = disposition.runtime_scoped_static_rows(
    fixture,
    {"runtime-a", "retained-b"},
    require_complete=True,
)
assert set(filtered) == {"runtime-a", "retained-b"}
try:
    disposition.runtime_scoped_static_rows(
        {"runtime-a": {"model": {}}},
        {"runtime-a", "retained-b"},
        require_complete=True,
    )
except SystemExit as exc:
    assert "missing from static knowledge" in str(exc)
else:
    raise AssertionError("missing runtime static authority was accepted")

counter = {
    "providerCount": 3,
    "routeReconstruction": {"providerCount": 3},
}
disposition.refresh_static_provider_counts(counter, 2)
assert counter["providerCount"] == 2
assert counter["routeReconstruction"]["providerCount"] == 2

print(
    "Repair disposition runtime/static scope passed: "
    f"runtime={len(runtime_ids)} pending_excluded={len(pending)}"
)
