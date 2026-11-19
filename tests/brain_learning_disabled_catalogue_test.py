#!/usr/bin/env python3
"""A disabled published provider is retained for Brain learning but never runnable."""
from __future__ import annotations
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
src = ROOT / "scripts" / "discover_candidates.py"
spec = importlib.util.spec_from_file_location("discover_candidates", src)
assert spec and spec.loader
sys.path.insert(0, str(src.parent))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

rows = mod.local_catalog_baseline_entries(ROOT)
by_id = {str(row.get("id") or ""): row for row in rows}
catalog = json.loads((ROOT / "provider_catalog.json").read_text("utf-8"))
assert len(by_id) == len(catalog["providers"]), "canonical catalogue rows missing before discovery"
disabled_ids = [
    pid for pid, entry in by_id.items()
    if entry.get("enabled") is False
]
assert disabled_ids, "expected disabled catalogue learning fixtures"
for pid in disabled_ids:
    path, disabled = mod.resolve_catalogue_learning_source(ROOT, by_id[pid])
    assert disabled, pid
    assert path.is_file() and path.parent == ROOT / "provider-disabled", pid

enabled = [entry for entry in by_id.values() if entry.get("enabled") is not False]
assert enabled
path, disabled = mod.resolve_catalogue_learning_source(ROOT, enabled[0])
assert not disabled and path.parent == ROOT / "providers"

with tempfile.TemporaryDirectory() as folder:
    stage = Path(folder) / "stage"
    # The real disabled-file code must be read only as static knowledge. The
    # staged JS is regenerated via NiakVIO-owned clean ProviderBase and remains
    # excluded from repair/publication and both production manifests.
    result = subprocess.run(
        [sys.executable, str(src),
         "--stage", str(stage),
         "--clean-reconstruction",
         "--local-catalog-only",
         "--provider", disabled_ids[0]],
        cwd=ROOT, text=True, capture_output=True, timeout=60,
    )
    assert result.returncode == 0, result.stdout[-1500:] + "\n" + result.stderr[-1500:]
    staged = json.loads((stage / "candidates.json").read_text("utf-8"))
    assert len(staged["candidates"]) == 1
    row = staged["candidates"][0]
    assert row["canonical_id"] == disabled_ids[0]
    assert row["metadata"]["enabled"] is False
    assert row["catalogue_disabled"] is True
    assert row["repair_allowed"] is False
    assert row["publication_allowed"] is False
    assert row["baseline_origin"] == "disabled_catalogue_static_learning"
    assert row["upstream_code_executed"] is False
    assert row["candidate_code_origin"] == "new-niakvio-clean-seed"
    data = (stage / row["local_path"]).read_bytes()
    archived_source, _ = mod.resolve_catalogue_learning_source(ROOT, by_id[disabled_ids[0]])
    assert data != archived_source.read_bytes(), "archived JS was re-used as executable seed"
    assert b"NIAKVIO_PROVIDER_BASE_OWNED_V3" in data

print(f"Brain Learning disabled catalogue preservation passed: disabled={len(disabled_ids)}")
