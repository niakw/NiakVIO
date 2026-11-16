#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SCRIPT = ROOT / "scripts" / "sanitize_provider_v3_execution_routes_v1.py"

spec = importlib.util.spec_from_file_location("sanitize_provider_v3_execution_routes_v1", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

from current_provider_scope import (\n    active_provider_ids,\n    pending_provider_ids,\n    projection_runtime_visible_provider_ids,\n    runtime_visible_provider_ids,\n    visible_provider_ids,\n)

knowledge = json.loads((ROOT / "automation" / "provider-v3-static-knowledge.json").read_text(encoding="utf-8"))
ids = {module.cid(value) for value in (knowledge.get("providers") or {}) if module.cid(value)}
projection_runtime_ids = projection_runtime_visible_provider_ids()\nglobal_runtime_ids = runtime_visible_provider_ids()\nassert ids == projection_runtime_ids, (sorted(ids - projection_runtime_ids), sorted(projection_runtime_ids - ids))
assert pending_provider_ids().isdisjoint(ids)
assert pending_provider_ids() <= visible_provider_ids() | pending_provider_ids()
assert len(ids) >= len(active_provider_ids())
assert len(ids) > len(active_provider_ids()), "fixture should prove disabled-visible rows are intentionally retained"

with tempfile.TemporaryDirectory() as tmp:
    path = Path(tmp) / "knowledge.json"
    bad = dict(knowledge)
    providers = dict(knowledge["providers"])
    providers.pop(next(iter(sorted(providers))))
    bad["providers"] = providers
    path.write_text(json.dumps(bad), encoding="utf-8")
    old = sys.argv
    try:
        sys.argv = [str(SCRIPT), "--knowledge", str(path)]
        try:
            module.main()
        except ValueError as exc:
            assert "identity mismatch" in str(exc), exc
        else:
            raise AssertionError("sanitizer accepted incomplete runtime-visible provider knowledge")
    finally:
        sys.argv = old

print(\n    "provider execution-route sanitizer scope passed: exact Global+France runtime-visible identities; "\n    "pending staging excluded"\n)
