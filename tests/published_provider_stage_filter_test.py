#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
spec=importlib.util.spec_from_file_location("published_stage_builder",ROOT/"scripts"/"build_published_provider_stage.py")
module=importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)

from current_provider_scope import projection_active_provider_ids

with TemporaryDirectory() as td:
    td=Path(td)
    general=td/"manifest.json"
    france=td/"vf.json"
    general.write_text(json.dumps({"scrapers":[{"id":"shared","enabled":True,"filename":"providers/shared.js"}]})+"\n",encoding="utf-8")
    france.write_text(json.dumps({"scrapers":[
        {"id":"shared","enabled":True,"filename":"../providers/shared.js"},
        {"id":"fr-only","enabled":True,"filename":"../providers/fr-only.js"}
    ]})+"\n",encoding="utf-8")
    union=module.projection_rows(general,france)
    assert set(union)=={"shared","fr-only"}
    assert union["fr-only"]["filename"]=="providers/fr-only.js"
    bad=td/"vf-bad.json"
    bad.write_text(json.dumps({"scrapers":[{"id":"shared","enabled":True,"filename":"../providers/other.js"}]})+"\n",encoding="utf-8")
    try:
        module.projection_rows(general,bad)
    except SystemExit as exc:
        assert "projection asset or enabled-state mismatch" in str(exc)
    else:
        raise AssertionError("shared Global/France drift must fail closed")

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

with TemporaryDirectory() as td:
    stage=Path(td)/"stage-all"
    subprocess.run([
        sys.executable,
        str(ROOT/"scripts"/"build_published_provider_stage.py"),
        "--stage",str(stage),
    ],check=True,cwd=ROOT)
    data=json.loads((stage/"candidates.json").read_text(encoding="utf-8"))
    candidates=data.get("candidates") or []
    actual={str(row.get("canonical_id") or "").casefold().replace("_","-") for row in candidates}
    expected=projection_active_provider_ids()
    assert actual==expected,(sorted(actual-expected),sorted(expected-actual))
    assert len(candidates)==len(expected)

source=(ROOT/"scripts"/"build_published_provider_stage.py").read_text(encoding="utf-8")
assert "if requested:" in source
assert "rows=projection_active_provider_rows()" in source
assert "active_provider_rows" not in source
assert "projection_rows(args.manifest,args.france_manifest)" in source
assert source.index("if requested:") < source.index("rows=projection_active_provider_rows()")
workflow=(ROOT/".github/workflows/brain-learning-lab.yml").read_text(encoding="utf-8")
assert 'timeout --signal=TERM --kill-after=5s 30s "${args[@]}"' in workflow

print("published provider stage filter contract passed")
