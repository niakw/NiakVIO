#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT=Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/"manifest.json").read_text(encoding="utf-8"))
rows=[
    row for row in manifest.get("scrapers") or []
    if isinstance(row,dict)
    and row.get("enabled") is not False
    and str(row.get("filename") or "").startswith("providers/")
]
assert len(rows)>=2
target=str(rows[0]["id"]).strip().casefold().replace("_","-")

with TemporaryDirectory() as td:
    stage=Path(td)/"stage"
    subprocess.run([
        sys.executable,
        str(ROOT/"scripts"/"build_published_provider_stage.py"),
        "--stage",str(stage),
        "--provider",target,
    ],check=True,cwd=ROOT)
    data=json.loads((stage/"candidates.json").read_text(encoding="utf-8"))
    candidates=data.get("candidates") or []
    assert len(candidates)==1,data
    assert str(candidates[0].get("canonical_id") or "").casefold().replace("_","-")==target
    assert candidates[0].get("published_exact_bytes") is True
    assert candidates[0].get("repair_allowed") is False


source=(ROOT/"scripts"/"build_published_provider_stage.py").read_text(encoding="utf-8")
assert "if requested:" in source
assert "rows=active_provider_rows()" in source
assert source.index("if requested:") < source.index("rows=active_provider_rows()")
workflow=(ROOT/".github/workflows/brain-learning-lab.yml").read_text(encoding="utf-8")
assert 'timeout --signal=TERM --kill-after=5s 30s "${args[@]}"' in workflow

print("published provider stage filter contract passed")
