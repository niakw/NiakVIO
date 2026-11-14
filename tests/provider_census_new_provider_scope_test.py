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
    old_pending=mod.pending_provider_ids
    mod.MANIFEST=manifest
    mod.pending_provider_ids=lambda:{"brand-new"}
    try:
        selected,scope=mod._scope_provider_filter("unresolved",status,[])
        assert scope=="unresolved"
        assert selected=={"red"},selected
        try:
            mod._scope_provider_filter("unresolved",status,["brand-new"])
        except ValueError:
            pass
        else:
            raise AssertionError("pending provider accepted without explicit onboarding authority")
        targeted,target_scope=mod._scope_provider_filter("unresolved",status,["brand-new"],allow_pending_targets=True)
        assert targeted=={"brand-new"} and target_scope=="explicit"
    finally:
        mod.MANIFEST=old_manifest
        mod.pending_provider_ids=old_pending

print("New onboarding pending scope requires explicit census authority")
