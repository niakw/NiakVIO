#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
path=ROOT/"scripts/select_residential_provider_replay.py"
spec=importlib.util.spec_from_file_location("select_residential_offline",path)
assert spec and spec.loader
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

with tempfile.TemporaryDirectory() as td:
    root=Path(td)
    (root/"providers").mkdir()
    asset=root/"providers/demo.js"
    asset.write_text("console.log('demo')\n",encoding="utf-8")
    digest=hashlib.sha256(asset.read_bytes()).hexdigest()

    manifest={"scrapers":[{
        "id":"demo","enabled":True,"filename":"providers/demo.js",
    }]}
    vf={"scrapers":[]}
    overrides={
        "provider_patches":{"demo":{"manifest_overrides":{}}},
        "provider_capabilities":{"demo":{
            "validation":"bulk_offline_contract_live_unverified",
        }},
    }
    activation={
        "mode":"bulk_offline_contract_live_unverified",
        "providers":[{
            "provider":"demo",
            "providerSha256":digest,
            "minimizerFixedPoint":True,
            "nodeSyntax":"passed",
            "providerV3Contract":"passed",
            "providerExecutablePlan":"passed",
            "providerIdentityExecutionPlan":"passed",
            "directOriginSyntax":"passed",
            "fullOkClaimed":False,
        }],
    }

    allowed=mod.offline_live_unverified_transport_authority(
        root,manifest,vf,overrides,activation
    )
    assert allowed=={"demo"},allowed

    # Archived ledgers using the old key stay readable, but current production
    # schema is "providers".
    legacy=dict(activation)
    legacy["activatedProviders"]=legacy.pop("providers")
    assert mod.offline_live_unverified_transport_authority(
        root,manifest,vf,overrides,legacy
    )=={"demo"}

    # Byte drift removes transport authority.
    asset.write_text("console.log('drift')\n",encoding="utf-8")
    assert mod.offline_live_unverified_transport_authority(
        root,manifest,vf,overrides,activation
    )==set()

    # Restore bytes, then prove disabled state cannot enter this path.
    asset.write_text("console.log('demo')\n",encoding="utf-8")
    manifest["scrapers"][0]["enabled"]=False
    assert mod.offline_live_unverified_transport_authority(
        root,manifest,vf,overrides,activation
    )==set()

    manifest["scrapers"][0]["enabled"]=True
    activation["providers"][0]["providerIdentityExecutionPlan"]="failed"
    assert mod.offline_live_unverified_transport_authority(
        root,manifest,vf,overrides,activation
    )==set()

print("offline live-unverified residential replay authority contract passed")
