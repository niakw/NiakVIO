#!/usr/bin/env python3
from pathlib import Path
import json
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
script=ROOT/"scripts/stage_provider_batch.py"
sys.path.insert(0,str(ROOT/"scripts"))
from add_provider import staged_existing_entry

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

# add_provider.stage publishes into Global. A catalog-owned France-only identity
# must fail closed instead of being duplicated/leaked into manifest.json.
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

print("Bulk provider onboarding dry-run + Global/France-only collision contract passed")
