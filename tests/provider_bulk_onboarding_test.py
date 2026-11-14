#!/usr/bin/env python3
from pathlib import Path
import json
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
script=ROOT/"scripts/stage_provider_batch.py"
sys.path.insert(0,str(ROOT/"scripts"))
from add_provider import staged_existing_entry, normalized_scope, relocate_bulk_pending_artifacts
from stage_provider_batch import safe_pending_restage_ids

with tempfile.TemporaryDirectory() as td:
    td=Path(td)
    req=td/"batch.json"; out=td/"summary.json"
    req.write_text(json.dumps({"providers":[
        {
            "id":"bulk-scale-contract-provider-zz999",
            "name":"Bulk Scale Contract Provider",
            "types":["movie","tv"],
            "languages":["en"],
            "strategy":"mixed_embed_resolver",
            "direct":"https://example.invalid"
        }
    ]}),encoding="utf-8")
    subprocess.run([
        "python",str(script),"--request",str(req),"--output",str(out),"--dry-run"
    ],cwd=ROOT,check=True)
    value=json.loads(out.read_text(encoding="utf-8"))

assert value["providerCount"]==1
assert value["newProviderCount"]==1
assert value["mode"]=="dry-run"
assert value["networkDiscoveryExecuted"] is False
assert value["nativeLabExecuted"] is False
assert value["activationAttempted"] is False
assert value["strategies"]=={"mixed_embed_resolver":1}
assert value["declaredTypeCounts"]=={"movie":1,"tv":1}
assert value["scopeCounts"]=={"global":1}
assert normalized_scope("vf")=="france"
assert normalized_scope("global")=="global"

# Global and France-only identities are distinct authorities and collisions fail closed.
with tempfile.TemporaryDirectory(prefix="niakvio-onboard-scope-") as td:
    root=Path(td)
    france={
        "id":"france-reserved",
        "name":"France reserved",
        "filename":"providers/france-reserved--v3.js",
        "enabled":False,
        "contentLanguage":["fr"],
        "supportedTypes":["movie"],
        "disabledPlatforms":[],
    }
    (root/"provider_catalog.json").write_text(json.dumps({
        "sourceOfTruth":True,
        "providers":[{
            "canonicalId":"france-reserved",
            "scraper":france,
            "projections":{"general":False,"vf":True},
        }],
    }),encoding="utf-8")
    manifest={"scrapers":[{"id":"global-existing","filename":"providers/global-existing.js"}]}
    assert staged_existing_entry("new-global",manifest,replace_existing=False,root=root)=={}
    assert staged_existing_entry("global-existing",manifest,replace_existing=True,root=root)["id"]=="global-existing"
    try:
        staged_existing_entry("global-existing",manifest,replace_existing=False,root=root)
    except ValueError as exc:
        assert "already exists" in str(exc)
    else:
        raise AssertionError("Global duplicate accepted without replace_existing")
    for replace in (False,True):
        try:
            staged_existing_entry("france-reserved",manifest,replace_existing=replace,root=root)
        except ValueError as exc:
            assert "France-only catalog scope" in str(exc)
        else:
            raise AssertionError("France-only identity leaked into Global staging")

    vf_manifest={"scrapers":[france]}
    assert staged_existing_entry("france-reserved",manifest,replace_existing=True,root=root,scope="france",vf_manifest=vf_manifest)["id"]=="france-reserved"
    assert staged_existing_entry("new-france",manifest,replace_existing=False,root=root,scope="france",vf_manifest=vf_manifest)=={}
    try:
        staged_existing_entry("global-existing",manifest,replace_existing=False,root=root,scope="france",vf_manifest=vf_manifest)
    except ValueError as exc:
        assert "Global scope" in str(exc)
    else:
        raise AssertionError("Global identity duplicated into France-only staging")

with tempfile.TemporaryDirectory(prefix="niakvio-bulk-pending-path-") as td:
    root=Path(td)
    (root/"providers").mkdir()
    (root/"provider-bases").mkdir()
    published=root/"providers/demo--nuvio--abc.js"
    base=root/"provider-bases/demo--base--abc.js"
    published.write_bytes(b"provider")
    base.write_bytes(b"base")
    relative=relocate_bulk_pending_artifacts(
        "providers/demo--nuvio--abc.js",
        "provider-bases/demo--base--abc.js",
        root=root,
    )
    assert relative=="provider-disabled/demo--nuvio--abc.js"
    assert not published.exists() and not base.exists()
    assert (root/relative).read_bytes()==b"provider"
    assert (root/"provider-disabled/provider-bases/demo--base--abc.js").read_bytes()==b"base"

print("Bulk provider onboarding dry-run + Global/France-only scope contract passed")

pending_manifest={"scrapers":[{"id":"pending-demo","enabled":False,"filename":"provider-disabled/pending-demo.js"},{"id":"disabled-demo","enabled":False,"filename":"provider-disabled/disabled-demo.js"},{"id":"active-demo","enabled":True,"filename":"providers/active-demo.js"}]}
pending_provenance={"providers":{"pending-demo":{"activation_mode":"bulk_onboarding_pending"},"disabled-demo":{"activation_mode":"disabled_retained"},"active-demo":{"activation_mode":"bulk_onboarding_pending"}}}
assert safe_pending_restage_ids(pending_manifest,{"scrapers":[]},pending_provenance)=={"pending-demo"}
print("Bulk pending restage authority is fail-closed outside inactive onboarding identities")
