#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
catalog = json.loads((ROOT / "provider_catalog.json").read_text(encoding="utf-8"))
candidates = []
for entry in catalog.get("providers") or []:
    if not isinstance(entry, dict) or not isinstance(entry.get("scraper"), dict):
        continue
    projections = entry.get("projections") if isinstance(entry.get("projections"), dict) else {}
    scraper = entry["scraper"]
    canonical = str(entry.get("canonicalId") or "").strip().casefold().replace("_", "-")
    if canonical and scraper.get("enabled") is not False and projections.get("vf") is True and projections.get("general") is False:
        candidates.append(canonical)
assert candidates, "catalogue must expose at least one active France-only provider"

target = sorted(candidates)[0]
env = os.environ.copy()
env["NUVIO_PROVIDER_FILTER"] = target
result = subprocess.run(
    [sys.executable, str(ROOT / "tests/global_stream_output_guard_test.py")],
    cwd=ROOT,
    env=env,
    text=True,
    capture_output=True,
    check=False,
)
assert result.returncode == 0, (
    f"France-only targeted stream guard failed for {target}\n"
    f"stdout={result.stdout[-4000:]}\nstderr={result.stderr[-4000:]}"
)
assert "scope=targeted" in result.stdout, result.stdout
print(f"Global stream output guard catalogue scope contract passed target={target} authority=provider_catalog")
