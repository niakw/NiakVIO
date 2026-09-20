#!/usr/bin/env python3
from pathlib import Path
import importlib.util
import json
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
module_path=ROOT/"scripts/activate_bulk_proven_providers.py"
spec=importlib.util.spec_from_file_location("activate_bulk_proven_providers_test",module_path)
mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)

with tempfile.TemporaryDirectory() as td:
    td=Path(td)
    paths={
        "MANIFEST":td/"manifest.json",
        "OVERRIDES":td/"provider-overrides.json",
        "PROVENANCE":td/"PROVENANCE.json",
        "HUBS":td/"provider-hubs.json",
        "STATUS":td/"status.json",
        "OUTPUT":td/"activation.json",
    }
    paths["MANIFEST"].write_text(json.dumps({"scrapers":[
        {"id":"a","enabled":False},{"id":"b","enabled":False},{"id":"c","enabled":False}
    ]}),encoding="utf-8")
    paths["OVERRIDES"].write_text(json.dumps({
        "provider_patches":{
            "a":{"manifest_overrides":{"enabled":False}},
            "b":{"manifest_overrides":{"enabled":False}},
            "c":{"manifest_overrides":{"enabled":False}},
        },
        "provider_capabilities":{"a":{},"b":{},"c":{}},
    }),encoding="utf-8")
    paths["PROVENANCE"].write_text(json.dumps({"providers":{
        "a":{"activation_mode":"bulk_onboarding_pending"},
        "b":{"activation_mode":"bulk_onboarding_pending"},
        "c":{"activation_mode":"bulk_onboarding_pending"},
    }}),encoding="utf-8")
    paths["HUBS"].write_text(json.dumps({"providers":{"a":{},"b":{},"c":{}}}),encoding="utf-8")
    paths["STATUS"].write_text(json.dumps({
        "runId":77,"triggerSha":"deadbeef","providers":[
            {"provider":"a","status":"FULL OK","declaredLanes":["movie","tv"],"currentVerifiedLanes":["movie","tv"],"brainCheckRequired":False},
            {"provider":"b","status":"PARTIAL OK","declaredLanes":["movie","tv"],"currentVerifiedLanes":["movie"],"brainCheckRequired":False},
            {"provider":"c","status":"FULL OK","declaredLanes":["anime"],"currentVerifiedLanes":[],"brainCheckRequired":False},
        ]
    }),encoding="utf-8")
    old={name:getattr(mod,name) for name in ("MANIFEST","OVERRIDES","PROVENANCE","HUBS","STATUS","OUTPUT")}
    for name,value in paths.items(): setattr(mod,name,value)
    argv=sys.argv[:]
    sys.argv=[str(module_path)]
    try:
        assert mod.main()==0
    finally:
        sys.argv=argv
        for name,value in old.items(): setattr(mod,name,value)

    activation=json.loads(paths["OUTPUT"].read_text(encoding="utf-8"))
    manifest=json.loads(paths["MANIFEST"].read_text(encoding="utf-8"))
    overrides=json.loads(paths["OVERRIDES"].read_text(encoding="utf-8"))
    provenance=json.loads(paths["PROVENANCE"].read_text(encoding="utf-8"))

assert activation["activatedProviders"]==["a"]
assert activation["activationCount"]==1
assert {x["provider"] for x in activation["blockedProviders"]}=={"b","c"}
rows={x["id"]:x for x in manifest["scrapers"]}
assert rows["a"]["enabled"] is True
assert rows["b"]["enabled"] is False
assert overrides["provider_patches"]["a"]["manifest_overrides"]["enabled"] is True
assert overrides["provider_capabilities"]["a"]["validation"]=="bulk_census_full_ok"
assert provenance["providers"]["a"]["activation_mode"]=="bulk_census_full_ok"
assert provenance["providers"]["a"]["bulk_activation_proof"]["runId"]==77
print("Bulk FULL OK activation gate passed")
