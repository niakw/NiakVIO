#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT=Path(__file__).resolve().parents[1]

with TemporaryDirectory() as td:
    root=Path(td)
    handoff=root/"handoff.json"
    health=root/"health.json"
    out=root/"out.json"
    handoff.write_text(json.dumps({"providers":["a","b"]}),encoding="utf-8")
    health.write_text(json.dumps({
        "candidate_count":2,
        "results":[
            {"canonical_id":"a","status":"no_streams"},
            {"canonical_id":"b","status":"runtime_error"},
        ],
    }),encoding="utf-8")
    subprocess.run([
        sys.executable,
        str(ROOT/"scripts"/"validate_fast_learning_health_scope.py"),
        "--handoff",str(handoff),
        "--health",str(health),
        "--output",str(out),
    ],check=True,cwd=ROOT)
    payload=json.loads(out.read_text(encoding="utf-8"))
    assert payload["providerCount"]==2
    assert payload["providers"]==["a","b"]
    assert payload["fullCatalogueCoverageRequired"] is False

historical=(ROOT/"engine_v2"/"scripts"/"build-historical-learning.mjs").read_text(encoding="utf-8")
for required in (
    "--provider-filter",
    "providerFilter.size === 0 || providerFilter.has(providerId)",
    "providerFilterApplied",
):
    assert required in historical, required

print("Fast-Handoff targeted health/historical scope tests passed")
