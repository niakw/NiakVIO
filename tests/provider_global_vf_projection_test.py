#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
import json
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
path=ROOT/"scripts"/"add_provider.py"
spec=importlib.util.spec_from_file_location("add_provider_vf_projection_test",path)
assert spec and spec.loader
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

france_only={
    "id":"france-only",
    "name":"France Only",
    "filename":"../provider-disabled/france-only--nuvio--x.js",
    "enabled":False,
}
vf={"scrapers":[dict(france_only)]}
global_row={
    "id":"multilingual",
    "name":"Multilingual",
    "filename":"provider-disabled/multilingual--nuvio--abc.js",
    "enabled":False,
    "contentLanguage":["en","fr"],
    "supportedTypes":["movie","tv"],
    "disabledPlatforms":[],
}

mod.sync_global_vf_projection(vf,global_row,"multilingual",include_vf=True)
assert [r["id"] for r in vf["scrapers"]] == ["france-only","multilingual"]
projected=vf["scrapers"][1]
assert projected["filename"]=="../provider-disabled/multilingual--nuvio--abc.js"
assert projected["contentLanguage"]==["en","fr"]

updated=dict(
    global_row,
    version="1.0.1",
    name="🎬 Multilingual",
    logo="https://raw.githubusercontent.com/niakw/NiakVIO/main/assets/providers/96x96/multilingual.webp",
)
mod.sync_global_vf_projection(vf,updated,"multilingual",include_vf=True)
assert [r["id"] for r in vf["scrapers"]].count("multilingual")==1
assert vf["scrapers"][1]["version"]=="1.0.1"
assert vf["scrapers"][1]["name"]==updated["name"]
assert vf["scrapers"][1]["logo"]==updated["logo"]

mod.sync_global_vf_projection(vf,updated,"multilingual",include_vf=False)
assert [r["id"] for r in vf["scrapers"]]==["france-only"]
assert vf["scrapers"][0]==france_only

duplicate={"scrapers":[dict(global_row),dict(global_row)]}
try:
    mod.sync_global_vf_projection(duplicate,global_row,"multilingual",include_vf=True)
except ValueError as exc:
    assert "duplicate VF projection rows" in str(exc)
else:
    raise AssertionError("duplicate shared VF rows were accepted")

stage_path=ROOT/"scripts"/"stage_provider_batch.py"
stage_spec=importlib.util.spec_from_file_location("stage_provider_batch_vf_projection_test",stage_path)
assert stage_spec and stage_spec.loader
stage_mod=importlib.util.module_from_spec(stage_spec)
stage_spec.loader.exec_module(stage_mod)
with tempfile.TemporaryDirectory() as td:
    td=Path(td)
    vf_path=td/"vf"/"manifest.json"
    vf_path.parent.mkdir(parents=True,exist_ok=True)
    vf_path.write_text(json.dumps({"scrapers":[
        {"id":"france-only","filename":"../provider-disabled/france-only.js"},
        {"id":"multilingual","filename":"../provider-disabled/old.js"},
    ]}),encoding="utf-8")
    original=stage_mod.add_provider.VF_MANIFEST
    stage_mod.add_provider.VF_MANIFEST=vf_path
    try:
        stage_mod.sync_finalized_shared_vf_filename("multilingual","provider-disabled/newhash.js")
    finally:
        stage_mod.add_provider.VF_MANIFEST=original
    rows=json.loads(vf_path.read_text(encoding="utf-8"))["scrapers"]
    assert rows[0]["filename"]=="../provider-disabled/france-only.js"
    assert rows[1]["filename"]=="../provider-disabled/newhash.js"

source=path.read_text(encoding="utf-8")
assert 'vf = bool_value(request.get("vf"), any(value.startswith("fr") for value in languages))' in source
assert 'sync_global_vf_projection(' in source
assert 'if scope == "global":' in source

branding_source=(ROOT/"scripts"/"provider_branding_assets.py").read_text(encoding="utf-8")
assert "from add_provider import sync_global_vf_projection" in branding_source
assert "shared_vf_ids" in branding_source
assert "sync_global_vf_projection(" in branding_source
assert "provider_id in shared_vf_ids" in branding_source

print("Global multilingual VF projection contract passed: shared identity, relative path, idempotent membership, branding parity")
