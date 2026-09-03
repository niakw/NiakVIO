#!/usr/bin/env python3
"""Provider v3 minimizer must remain audit-only until semantic gates are proven."""
from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/provider_v3_minimizer.py"

spec = importlib.util.spec_from_file_location("provider_v3_minimizer", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)

report = module.portfolio_report()
assert report["mode"] == "audit-only"
assert report["production_enabled"] is False
assert report["terser_allowed"] is False
assert report["transformations_enabled"] == []
assert report["provider_count"] == 96
assert len(report["providers"]) == 96
manifest = __import__("json").loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
expected = {str(row["filename"]).split("/")[-1] for row in manifest.get("scrapers") or []}
observed = {row["file"] for row in report["providers"]}
assert observed == expected
assert report["totals"]["bytes"] > 0
assert report["totals"]["indentation_bytes"] >= 0

for row in report["providers"]:
    assert row["markers"]["BEGIN NIAKVIO_PROVIDER"] == 1, row["file"]
    assert row["markers"]["END NIAKVIO_PROVIDER"] == 1, row["file"]
    assert row["markers"]["NUVIO_GLOBAL_CORE_START_BOUNDARY_V1"] == 1, row["file"]

with tempfile.TemporaryDirectory() as tmp:
    output = Path(tmp) / "minimizer-audit.json"
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--output", str(output)],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert output.is_file()

forbidden = ROOT / "providers" / "minimizer-audit.json"
proc = subprocess.run(
    [sys.executable, str(SCRIPT), "--output", str(forbidden)],
    cwd=ROOT,
    text=True,
    capture_output=True,
)
assert proc.returncode != 0
assert not forbidden.exists()
assert "may never write inside providers/" in (proc.stdout + proc.stderr)

print("provider v3 minimizer audit-only contract passed")
