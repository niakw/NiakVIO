#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
script=ROOT/"scripts/stamp_provider_census_artifact_hashes.py"
spec=importlib.util.spec_from_file_location("stamp_census_hashes",script)
assert spec and spec.loader
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

with tempfile.TemporaryDirectory() as td:
    root=Path(td)
    (root/"providers").mkdir()
    asset=root/"providers"/"demo.js"
    asset.write_text("console.log('demo')\n",encoding="utf-8")
    digest=hashlib.sha256(asset.read_bytes()).hexdigest()

    global_manifest={"scrapers":[{"id":"demo","enabled":True,"filename":"providers/demo.js"}]}
    vf_manifest={"scrapers":[{"id":"demo","enabled":True,"filename":"../providers/demo.js"}]}
    hashes=mod.active_hashes(root,[global_manifest,vf_manifest])
    assert hashes=={"demo":digest},hashes

    status={"schemaVersion":3,"providers":[{
        "provider":"demo","status":"FULL OK","testedThisRun":True,
        "currentVerifiedLanes":["movie"],
    }]}
    stamped=mod.stamp(status,hashes)
    assert stamped["artifactHashSchemaVersion"]==1
    assert stamped["activeArtifactHashCount"]==1
    assert stamped["providers"][0]["providerArtifactSha256"]==digest
    verified=mod.verify_existing(stamped,hashes)
    assert verified["providers"][0]["providerArtifactSha256"]==digest

    asset.write_text("console.log('changed-after-census')\n",encoding="utf-8")
    changed_hashes=mod.active_hashes(root,[global_manifest,vf_manifest])
    try:
        mod.verify_existing(stamped,changed_hashes)
    except ValueError as exc:
        assert "differ from source-tested census bytes" in str(exc),exc
    else:
        raise AssertionError("changed production bytes inherited stale census proof")
    asset.write_text("console.log('demo')\n",encoding="utf-8")

    # The same provider cannot silently point at different executable bytes
    # between Global and France.
    other=root/"providers"/"other.js"
    other.write_text("console.log('other')\n",encoding="utf-8")
    bad_vf={"scrapers":[{"id":"demo","enabled":True,"filename":"../providers/other.js"}]}
    try:
        mod.active_hashes(root,[global_manifest,bad_vf])
    except ValueError as exc:
        assert "conflicting active artifact hashes" in str(exc)
    else:
        raise AssertionError("projection byte conflict was accepted")

print("all-scope census artifact hash ledger contract passed")
