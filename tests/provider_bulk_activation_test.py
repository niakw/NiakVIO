#!/usr/bin/env python3
from pathlib import Path
import hashlib
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
        "CATALOG":td/"provider_catalog.json",
        "OVERRIDES":td/"provider-overrides.json",
        "PROVENANCE":td/"PROVENANCE.json",
        "HUBS":td/"provider-hubs.json",
        "STATUS":td/"status.json",
        "OUTPUT":td/"activation.json",
    }
    paths["MANIFEST"].write_text(json.dumps({"scrapers":[
        {"id":"a","enabled":False,"filename":"provider-disabled/a.js"},{"id":"b","enabled":False,"filename":"provider-disabled/b.js"},{"id":"c","enabled":False,"filename":"provider-disabled/c.js"}
    ]}),encoding="utf-8")
    paths["CATALOG"].write_text(json.dumps({"providers":[
        {"canonicalId":"a","scraper":{"id":"a","enabled":False,"filename":"provider-disabled/a.js"},"projections":{"general":True,"vf":False}},
        {"canonicalId":"b","scraper":{"id":"b","enabled":False,"filename":"provider-disabled/b.js"},"projections":{"general":True,"vf":False}},
        {"canonicalId":"c","scraper":{"id":"c","enabled":False,"filename":"provider-disabled/c.js"},"projections":{"general":True,"vf":False}},
        {"canonicalId":"d","scraper":{"id":"d","enabled":False,"filename":"provider-disabled/d.js"},"projections":{"general":False,"vf":True}},
    ]}),encoding="utf-8")
    paths["OVERRIDES"].write_text(json.dumps({
        "provider_patches":{
            "a":{"manifest_overrides":{"enabled":False}},
            "b":{"manifest_overrides":{"enabled":False}},
            "c":{"manifest_overrides":{"enabled":False}},
            "d":{"manifest_overrides":{"enabled":False}},
        },
        "provider_capabilities":{"a":{},"b":{},"c":{},"d":{}},
    }),encoding="utf-8")
    paths["PROVENANCE"].write_text(json.dumps({"providers":{
        "a":{"activation_mode":"bulk_onboarding_pending","published_filename":"provider-disabled/a.js","base_filename":"provider-bases/a--base.js"},
        "b":{"activation_mode":"bulk_onboarding_pending","published_filename":"provider-disabled/b.js","base_filename":"provider-bases/b--base.js"},
        "c":{"activation_mode":"bulk_onboarding_pending","published_filename":"provider-disabled/c.js","base_filename":"provider-bases/c--base.js"},
        "d":{"activation_mode":"bulk_onboarding_pending","published_filename":"provider-disabled/d.js","base_filename":"provider-bases/d--base.js"},
    }}),encoding="utf-8")
    paths["HUBS"].write_text(json.dumps({"providers":{"a":{},"b":{},"c":{},"d":{}}}),encoding="utf-8")
    (td/"provider-disabled/provider-bases").mkdir(parents=True)
    for pid in ("a","b","c","d"):
        (td/f"provider-disabled/{pid}.js").write_bytes(("provider-"+pid).encode())
        (td/f"provider-disabled/provider-bases/{pid}--base.js").write_bytes(("base-"+pid).encode())
    paths["STATUS"].write_text(json.dumps({
        "runId":77,"triggerSha":"deadbeef","providers":[
            {"provider":"a","status":"FULL OK","testedThisRun":True,"declaredLanes":["movie","tv"],"currentVerifiedLanes":["movie","tv"],"brainCheckRequired":False},
            {"provider":"b","status":"PARTIAL OK","testedThisRun":True,"declaredLanes":["movie","tv"],"currentVerifiedLanes":["movie"],"brainCheckRequired":False},
            {"provider":"c","status":"FULL OK","testedThisRun":False,"declaredLanes":["anime"],"currentVerifiedLanes":["anime"],"brainCheckRequired":False},
            {"provider":"d","status":"FULL OK","testedThisRun":True,"declaredLanes":["movie","tv"],"currentVerifiedLanes":["movie","tv"],"brainCheckRequired":False},
        ]
    }),encoding="utf-8")
    old={name:getattr(mod,name) for name in ("MANIFEST","CATALOG","OVERRIDES","PROVENANCE","HUBS","STATUS","OUTPUT")}
    old_root=mod.ROOT
    old_digest=mod.pending_artifact_digest
    mod.ROOT=td
    mod.pending_artifact_digest=lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    for name,value in paths.items(): setattr(mod,name,value)
    argv=sys.argv[:]
    sys.argv=[str(module_path)]
    try:
        assert mod.main()==0
    finally:
        sys.argv=argv
        for name,value in old.items(): setattr(mod,name,value)
        mod.ROOT=old_root
        mod.pending_artifact_digest=old_digest

    activation=json.loads(paths["OUTPUT"].read_text(encoding="utf-8"))
    manifest=json.loads(paths["MANIFEST"].read_text(encoding="utf-8"))
    overrides=json.loads(paths["OVERRIDES"].read_text(encoding="utf-8"))
    provenance=json.loads(paths["PROVENANCE"].read_text(encoding="utf-8"))
    catalog=json.loads(paths["CATALOG"].read_text(encoding="utf-8"))

assert activation["activatedProviders"]==["a","d"]
assert activation["activationCount"]==2
assert activation["activationScopes"]=={"a":"global","d":"france"}
assert {x["provider"] for x in activation["blockedProviders"]}=={"b","c"}
blocked={x["provider"]:x for x in activation["blockedProviders"]}
assert blocked["c"]["reason"]=="full_ok_not_fresh_this_run"
rows={x["id"]:x for x in manifest["scrapers"]}
assert rows["a"]["enabled"] is True
assert rows["a"]["filename"]=="providers/a.js"
assert rows["b"]["enabled"] is False
assert rows["b"]["filename"]=="provider-disabled/b.js"
assert overrides["provider_patches"]["a"]["manifest_overrides"]["enabled"] is True
assert overrides["provider_capabilities"]["a"]["validation"]=="bulk_census_full_ok"
assert provenance["providers"]["a"]["activation_mode"]=="bulk_census_full_ok"
assert provenance["providers"]["a"]["bulk_activation_proof"]["runId"]==77
assert provenance["providers"]["a"]["bulk_activation_proof"]["proofSource"]=="onboarding-pending-status"
assert provenance["providers"]["a"]["bulk_activation_proof"]["providerSha256"]==hashlib.sha256(b"provider-a").hexdigest()
assert provenance["providers"]["d"]["bulk_activation_proof"]["scope"]=="france"
assert provenance["providers"]["a"]["published_filename"]=="providers/a.js"
assert provenance["providers"]["d"]["published_filename"]=="providers/d.js"
assert (td/"providers/a.js").is_file() and (td/"provider-bases/a--base.js").is_file()
assert (td/"providers/d.js").is_file() and (td/"provider-bases/d--base.js").is_file()
assert (td/"provider-disabled/b.js").is_file() and (td/"provider-disabled/c.js").is_file()
cat={x["canonicalId"]:x for x in catalog["providers"]}
assert cat["d"]["scraper"]["enabled"] is True
assert cat["d"]["scraper"]["filename"]=="providers/d.js"
assert "d" not in rows
print("Bulk FULL OK activation gate passed")
