#!/usr/bin/env python3
"""Deep Core must observe the exact active Global+France projection union."""
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from current_provider_scope import projection_active_provider_ids, projection_active_provider_rows

builder_source = (ROOT / "scripts" / "build_published_provider_stage.py").read_text(encoding="utf-8")
report_source = (ROOT / "scripts" / "build_observational_health_report.py").read_text(encoding="utf-8")
workflow = (ROOT / ".github" / "workflows" / "sync.yml").read_text(encoding="utf-8")

assert "projection_active_provider_rows" in builder_source
assert "rows=projection_active_provider_rows()" in builder_source
assert "rows=active_provider_rows()" not in builder_source
assert "projection_active_provider_count" in report_source
assert "projection_active_provider_rows" in report_source
assert "runtime_visible_provider_count" not in report_source
assert "build_published_provider_stage.py --stage staging-published" in workflow
assert "--manifest manifest.json" in workflow

rows = projection_active_provider_rows()
expected_ids = projection_active_provider_ids()
assert rows
assert {str(row.get("id") or "").strip().casefold().replace("_", "-") for row in rows} == expected_ids

spec = importlib.util.spec_from_file_location(
    "build_observational_health_report",
    ROOT / "scripts" / "build_observational_health_report.py",
)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

raw = {
    "mode": "deep",
    "counts": {"synthetic": len(rows)},
    "results": [
        {
            "canonical_id": row["id"],
            "status": "synthetic",
            "score": 0,
            "evidence": {},
        }
        for row in rows
    ],
}

with tempfile.TemporaryDirectory(prefix="niakvio-deep-union-") as tmp:
    tmp = Path(tmp)
    results = tmp / "health-results.json"
    output = tmp / "health-report.json"
    results.write_text(json.dumps(raw) + "\n", encoding="utf-8")
    old = sys.argv
    try:
        sys.argv = [
            str(ROOT / "scripts" / "build_observational_health_report.py"),
            "--results", str(results),
            "--manifest", str(ROOT / "manifest.json"),
            "--output", str(output),
        ]
        assert module.main() == 0
    finally:
        sys.argv = old

    report = json.loads(output.read_text(encoding="utf-8"))
    observed = {str(row.get("id") or "").strip().casefold().replace("_", "-") for row in report["providers"]}
    assert observed == expected_ids
    assert report["published_providers"] == len(expected_ids)

print(f"CORE_DEEP_PROJECTION_UNION_OK providers={len(expected_ids)}")
