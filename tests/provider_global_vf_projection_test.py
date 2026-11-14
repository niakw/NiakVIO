#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
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

updated=dict(global_row,version="1.0.1")
mod.sync_global_vf_projection(vf,updated,"multilingual",include_vf=True)
assert [r["id"] for r in vf["scrapers"]].count("multilingual")==1
assert vf["scrapers"][1]["version"]=="1.0.1"

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

source=path.read_text(encoding="utf-8")
assert 'vf = bool_value(request.get("vf"), any(value.startswith("fr") for value in languages))' in source
assert 'sync_global_vf_projection(' in source
assert 'if scope == "global":' in source

print("Global multilingual VF projection contract passed: shared identity, relative path, idempotent membership")
