#!/usr/bin/env python3
from pathlib import Path
import importlib.util
import json
import tempfile

ROOT=Path(__file__).resolve().parents[1]
module_path=ROOT/"scripts/audit_provider_quick_yield.py"
spec=importlib.util.spec_from_file_location("audit_provider_quick_yield_new_scope",module_path)
mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)

with tempfile.TemporaryDirectory() as td:
    td=Path(td)
    manifest=td/"manifest.json"
    status=td/"status.json"
    manifest.write_text(json.dumps({"scrapers":[
        {"id":"green"},
        {"id":"red"},
        {"id":"brand-new"},
    ]}),encoding="utf-8")
    status.write_text(json.dumps({"providers":[
        {"provider":"green","status":"FULL OK"},
        {"provider":"red","status":"ROUTE PROVEN"},
    ]}),encoding="utf-8")
    old_manifest=mod.MANIFEST
    mod.MANIFEST=manifest
    try:
        selected,scope=mod._scope_provider_filter("unresolved",status,[])
    finally:
        mod.MANIFEST=old_manifest

assert scope=="unresolved"
assert selected=={"red","brand-new"},selected
print("Newly onboarded providers enter unresolved census scope")
