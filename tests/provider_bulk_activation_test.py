#!/usr/bin/env python3
from pathlib import Path
import base64
import hashlib
import importlib.util
import json
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str((ROOT/"scripts").resolve()))
module_path=ROOT/"scripts/activate_bulk_proven_providers.py"
spec=importlib.util.spec_from_file_location("activate_bulk_proven_providers_test",module_path)
mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)

def provider_bundle(pid:str)->bytes:
    fix_id=f"PROVIDER.{pid.upper()}.CONFIG.V1"
    model={"providerId":pid,"strategy":"direct_media","officialSite":f"https://{pid}.example","origins":[f"https://{pid}.example"],"identityInput":{"mode":"tmdb_direct","requiresTmdbBeforeRun":False,"requiredFields":["tmdbId","mediaType"]}}
    payload=json.dumps(model,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
    encoded=base64.urlsafe_b64encode(payload).decode("ascii")
    return (
        "/* BEGIN NIAKVIO_PROVIDER */\n"
        f"/* NIAKVIO_PROVIDER_ID:{pid} */\n"
        "/* NIAKVIO_PROVIDER_BASE_OWNED_V3 */\n"
        f"/* STARTFIX:{fix_id} */\n"
        f"/* FIXDATA:{fix_id}:{encoded} */\n"
        "void 0;\n"
        f"/* CLOSEFIX:{fix_id} */\n"
        "async function getStreams(){return [];}\n"
        "/* END NIAKVIO_PROVIDER */\n"
    ).encode()


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
        "STATIC_KNOWLEDGE":td/"automation/provider-v3-static-knowledge.json",
        "VERSION_FLOORS":td/"provider-version-floors.json",
    }
    (td/".github/provider-onboarding").mkdir(parents=True)
    (td/"automation").mkdir(parents=True)
    paths["STATIC_KNOWLEDGE"].write_text(json.dumps({"schemaVersion":1,"providers":{}}),encoding="utf-8")
    paths["VERSION_FLOORS"].write_text(json.dumps({"schema_version":1,"providers":{}}),encoding="utf-8")
    (td/".github/provider-portfolio-policy.json").write_text(json.dumps({
        "portfolio":{"target_global_active":1,"target_france_active":1}
    }),encoding="utf-8")
    (td/".github/provider-onboarding/batch.json").write_text(json.dumps({
        "providers":[
            {"id":"a","inventory_rank":1,"inventory_score":100},
            {"id":"b","inventory_rank":2,"inventory_score":99},
            {"id":"d","inventory_rank":1,"inventory_score":100},
        ],
        "deferredProviders":[]
    }),encoding="utf-8")
    paths["MANIFEST"].write_text(json.dumps({"scrapers":[
        {"id":"a","enabled":False,"filename":"provider-disabled/a.js","version":"1.0.0"},{"id":"b","enabled":False,"filename":"provider-disabled/b.js","version":"1.0.0"},{"id":"c","enabled":False,"filename":"provider-disabled/c.js","version":"1.0.0"},{"id":"e","enabled":False,"filename":"provider-disabled/e.js","version":"1.0.0"}
    ]}),encoding="utf-8")
    paths["CATALOG"].write_text(json.dumps({"providers":[
        {"canonicalId":"a","scraper":{"id":"a","enabled":False,"filename":"provider-disabled/a.js"},"projections":{"general":True,"vf":False}},
        {"canonicalId":"b","scraper":{"id":"b","enabled":False,"filename":"provider-disabled/b.js"},"projections":{"general":True,"vf":False}},
        {"canonicalId":"c","scraper":{"id":"c","enabled":False,"filename":"provider-disabled/c.js"},"projections":{"general":True,"vf":False}},
        {"canonicalId":"d","scraper":{"id":"d","enabled":False,"filename":"provider-disabled/d.js","version":"1.0.0","supportedTypes":["anime","tv"],"canonicalSupportedTypes":["anime"]},"projections":{"general":False,"vf":True}},
        {"canonicalId":"e","scraper":{"id":"e","enabled":False,"filename":"provider-disabled/e.js"},"projections":{"general":True,"vf":False}},
    ]}),encoding="utf-8")
    paths["OVERRIDES"].write_text(json.dumps({
        "provider_patches":{
            "a":{"manifest_overrides":{"enabled":False},"provider_lego_scripts":["scripts/provider_patches/example_runtime_v1.py"]},
            "b":{"manifest_overrides":{"enabled":False}},
            "c":{"manifest_overrides":{"enabled":False}},
            "d":{"manifest_overrides":{"enabled":False}},
            "e":{"manifest_overrides":{"enabled":False}},
        },
        "provider_capabilities":{"a":{},"b":{},"c":{},"d":{},"e":{}},
    }),encoding="utf-8")
    paths["PROVENANCE"].write_text(json.dumps({"providers":{
        "a":{"activation_mode":"bulk_onboarding_pending","published_filename":"provider-disabled/a.js","base_filename":"provider-bases/a--base.js"},
        "b":{"activation_mode":"bulk_onboarding_pending","published_filename":"provider-disabled/b.js","base_filename":"provider-bases/b--base.js"},
        "c":{"activation_mode":"bulk_onboarding_pending","published_filename":"provider-disabled/c.js","base_filename":"provider-bases/c--base.js"},
        "d":{"activation_mode":"bulk_onboarding_pending","published_filename":"provider-disabled/d.js","base_filename":"provider-bases/d--base.js"},
        "e":{"activation_mode":"bulk_onboarding_pending","published_filename":"provider-disabled/e.js","base_filename":"provider-bases/e--base.js"},
    }}),encoding="utf-8")
    paths["HUBS"].write_text(json.dumps({"providers":{"a":{},"b":{},"c":{},"d":{},"e":{}}}),encoding="utf-8")
    (td/"provider-disabled/provider-bases").mkdir(parents=True)
    for pid in ("a","b","c","d","e"):
        (td/f"provider-disabled/{pid}.js").write_bytes(provider_bundle(pid))
        (td/f"provider-disabled/provider-bases/{pid}--base.js").write_bytes(("base-"+pid).encode())
    paths["STATUS"].write_text(json.dumps({
        "runId":77,"triggerSha":"deadbeef","providers":[
            {"provider":"a","status":"FULL OK","testedThisRun":True,"declaredLanes":["movie","tv"],"currentVerifiedLanes":["movie","tv"],"brainCheckRequired":False},
            {"provider":"b","status":"FULL OK","testedThisRun":True,"declaredLanes":["movie","tv"],"currentVerifiedLanes":["movie","tv"],"brainCheckRequired":False},
            {"provider":"c","status":"FULL OK","testedThisRun":False,"declaredLanes":["anime"],"currentVerifiedLanes":["anime"],"brainCheckRequired":False},
            {"provider":"d","status":"FULL OK","testedThisRun":True,"declaredLanes":["movie","tv"],"currentVerifiedLanes":["movie","tv"],"brainCheckRequired":False},
            {"provider":"e","status":"FULL OK","testedThisRun":True,"declaredLanes":["movie"],"currentVerifiedLanes":["movie"],"brainCheckRequired":False},
        ]
    }),encoding="utf-8")
    old={name:getattr(mod,name) for name in ("MANIFEST","CATALOG","OVERRIDES","PROVENANCE","HUBS","STATUS","OUTPUT","STATIC_KNOWLEDGE","VERSION_FLOORS")}
    old_root=mod.ROOT
    old_digest=mod.pending_artifact_digest
    old_proof_digest=mod.proof_source_artifact_digest
    mod.ROOT=td
    mod.pending_artifact_digest=lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    mod.proof_source_artifact_digest=lambda trigger,relative: hashlib.sha256((td/relative).read_bytes()).hexdigest()
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
        mod.proof_source_artifact_digest=old_proof_digest

    activation=json.loads(paths["OUTPUT"].read_text(encoding="utf-8"))
    manifest=json.loads(paths["MANIFEST"].read_text(encoding="utf-8"))
    overrides=json.loads(paths["OVERRIDES"].read_text(encoding="utf-8"))
    provenance=json.loads(paths["PROVENANCE"].read_text(encoding="utf-8"))
    catalog=json.loads(paths["CATALOG"].read_text(encoding="utf-8"))
    # Capture filesystem postconditions while TemporaryDirectory still exists.
    # JSON assertions can run after cleanup; path-existence assertions cannot.
    filesystem_postconditions={
        "a_provider":(td/"providers/a.js").is_file(),
        "a_base":(td/"provider-bases/a--base.js").is_file(),
        "d_provider":(td/"providers/d.js").is_file(),
        "d_base":(td/"provider-bases/d--base.js").is_file(),
        "b_pending":(td/"provider-disabled/b.js").is_file(),
        "c_pending":(td/"provider-disabled/c.js").is_file(),
        "e_pending":(td/"provider-disabled/e.js").is_file(),
    }

assert activation["activatedProviders"]==["a","d"]
assert activation["activationCount"]==2
assert activation["activationScopes"]=={"a":"global","d":"france"}
assert {x["provider"] for x in activation["blockedProviders"]}=={"b","c","e"}
blocked={x["provider"]:x for x in activation["blockedProviders"]}
assert blocked["b"]["reason"]=="portfolio_projection_capacity_reached"
assert blocked["b"]["projections"]==["global"]
assert blocked["c"]["reason"]=="full_ok_not_fresh_this_run"
assert blocked["e"]["reason"]=="portfolio_priority_missing"
assert activation["portfolio"]["targetGlobal"]==1
assert activation["portfolio"]["targetFrance"]==1
assert activation["portfolio"]["activeGlobalBefore"]==0
assert activation["portfolio"]["activeFranceBefore"]==0
assert activation["portfolio"]["activeGlobalAfter"]==1
assert activation["portfolio"]["activeFranceAfter"]==1
rows={x["id"]:x for x in manifest["scrapers"]}
assert rows["a"]["enabled"] is True
assert rows["a"]["filename"]=="providers/a.js"
assert rows["b"]["enabled"] is False
assert rows["b"]["filename"]=="provider-disabled/b.js"
assert "enabled" not in (overrides["provider_patches"]["a"].get("manifest_overrides") or {})
assert "enabled" not in (overrides["provider_patches"]["d"].get("manifest_overrides") or {})
assert overrides["provider_capabilities"]["a"]["validation"]=="bulk_census_full_ok"
assert overrides["provider_patches"]["a"]["identity_input"]=={
    "mode":"tmdb_direct",
    "requires_tmdb_before_run":False,
    "required_fields":["tmdbId","mediaType"],
}
assert "learned_routes" not in overrides["provider_patches"]["a"]
assert provenance["providers"]["a"]["activation_mode"]=="bulk_census_full_ok"
assert provenance["providers"]["a"]["bulk_activation_proof"]["runId"]==77
assert provenance["providers"]["a"]["bulk_activation_proof"]["proofSource"]=="onboarding-pending-status"
assert provenance["providers"]["a"]["bulk_activation_proof"]["providerSha256"]==hashlib.sha256(provider_bundle("a")).hexdigest()
assert provenance["providers"]["d"]["bulk_activation_proof"]["scope"]=="france"
assert provenance["providers"]["a"]["published_filename"]=="providers/a.js"
assert provenance["providers"]["d"]["published_filename"]=="providers/d.js"
assert filesystem_postconditions["a_provider"] and filesystem_postconditions["a_base"], filesystem_postconditions
assert filesystem_postconditions["d_provider"] and filesystem_postconditions["d_base"], filesystem_postconditions
assert filesystem_postconditions["b_pending"] and filesystem_postconditions["c_pending"] and filesystem_postconditions["e_pending"], filesystem_postconditions
cat={x["canonicalId"]:x for x in catalog["providers"]}
assert cat["d"]["scraper"]["enabled"] is True
assert cat["d"]["scraper"]["filename"]=="providers/d.js"
assert cat["d"]["scraper"]["supportedTypes"]==["anime"]
assert "canonicalSupportedTypes" not in cat["d"]["scraper"]
assert "d" not in rows
print("Bulk FULL OK activation gate passed")
