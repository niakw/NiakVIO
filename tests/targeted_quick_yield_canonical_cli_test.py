#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
path=ROOT/"scripts/audit_provider_quick_yield_targeted.py"
spec=importlib.util.spec_from_file_location("targeted_quick_yield",path)
assert spec and spec.loader
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

with tempfile.TemporaryDirectory() as td:
    root=Path(td)
    fake=root/"fake_quick_yield.py"
    fake.write_text(
        """import argparse,json
from pathlib import Path

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--scope')
    p.add_argument('--output',required=True)
    p.add_argument('--provider',action='append',default=[])
    a=p.parse_args()
    rows=[
        {
            'provider_id':provider,
            'semantic_type':'movie',
            'raw':1,
            'playable':1,
            'verified':1,
            'contradictions':0,
            'identity_safe':True,
        }
        for provider in a.provider
    ]
    payload={
        'provider_count':len(a.provider),
        'raw_providers':sorted(a.provider),
        'playable_providers':sorted(a.provider),
        'accepted_playable_providers':sorted(a.provider),
        'verified_providers':sorted(a.provider),
        'wrong_content_providers':[],
        'rows':rows,
    }
    Path(a.output).write_text(json.dumps(payload),encoding='utf-8')
    return 0
""",
        encoding="utf-8",
    )
    providers=root/"providers.json"
    providers.write_text(json.dumps({"providers":["beta","alpha"]}),encoding="utf-8")
    output=root/"out.json"

    # Global-only and France-only published bytes must both be stamped.
    (root/"providers").mkdir()
    (root/"vf").mkdir()
    (root/"providers/alpha.js").write_text("alpha exact JS", encoding="utf-8")
    (root/"providers/beta.js").write_text("beta exact JS", encoding="utf-8")
    (root/"manifest.json").write_text(json.dumps({
        "scrapers":[{"id":"alpha","filename":"providers/alpha.js","enabled":True}]
    }),encoding="utf-8")
    (root/"vf/manifest.json").write_text(json.dumps({
        "scrapers":[{"id":"beta","filename":"../providers/beta.js","enabled":True}]
    }),encoding="utf-8")
    original_root=mod.ROOT
    mod.ROOT=root
    original_base=mod.BASE_PATH
    original_argv=list(sys.argv)
    mod.BASE_PATH=fake
    sys.argv=[str(path),"--providers-json",str(providers),"--output",str(output),"--attempts","2"]
    expected_wrapper_argv=list(sys.argv)
    try:
        rc=mod.main()
        assert rc==0
        assert sys.argv==expected_wrapper_argv, (sys.argv,expected_wrapper_argv)
    finally:
        mod.BASE_PATH=original_base
        mod.ROOT=original_root
        sys.argv=original_argv

    data=json.loads(output.read_text(encoding="utf-8"))
    assert data["providers"]==["alpha","beta"],data
    assert data["attempts"]==2,data
    assert data["raw_providers"]==["alpha","beta"],data
    assert data["playable_providers"]==["alpha","beta"],data
    assert data["verified_providers"]==["alpha","beta"],data
    assert len(data["rows"])==4,data
    expected_sha={
        provider:hashlib.sha256((root/"providers"/(provider+".js")).read_bytes()).hexdigest()
        for provider in ("alpha","beta")
    }
    assert data["provider_bundle_sha256"]==expected_sha,data
    assert all(
        row["provider_artifact_sha256"]==expected_sha[row["provider_id"]]
        for row in data["rows"]
    ),data

source=path.read_text(encoding="utf-8")
assert "mod.build_tasks =" not in source
assert 'sys.argv = [str(BASE_PATH), "--scope", "all", "--output", str(path)]' in source
assert 'sys.argv.extend(["--provider", provider])' in source
assert "sys.argv = original_argv" in source

print("targeted quick-yield canonical CLI contract passed")
