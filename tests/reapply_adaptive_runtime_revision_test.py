#!/usr/bin/env python3
from __future__ import annotations
import importlib.util
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path); module=importlib.util.module_from_spec(spec)
    assert spec.loader is not None; spec.loader.exec_module(module); return module
adaptive=load('adaptive_v4',ROOT/'scripts/provider_patches/adaptive_runtime_recovery_v4.py')
reapply=load('reapply_overrides',ROOT/'scripts/reapply_published_overrides.py')
options={'provider_name':'Demo','base_url':'https://demo.example','types':['movie'],'search_paths':['/?s={query}'],'direct_paths':['/{slug}']}
base='module.exports={getStreams:async()=>[]};\n'
expected=adaptive.apply(base,options=options)
marker=next(line for line in expected.splitlines() if 'NUVIO_ADAPTIVE_RUNTIME_RECOVERY_V4:' in line)
legacy=expected.replace(marker,'/* NUVIO_ADAPTIVE_RUNTIME_RECOVERY_V4:legacy00000000 */',1)
provenance={'local_patches':[{'type':'patch_profile','profile':'adaptive_runtime_recovery','phase':'runtime','options':options}]}
upgraded,records=reapply.reapply_adaptive_runtime_revision(legacy.encode(),provenance)
assert upgraded.decode()==expected
assert records and records[0]['runtime_revision']=='generic-core-v2'
unchanged,records=reapply.reapply_adaptive_runtime_revision(base.encode(),provenance)
assert unchanged.decode()==base and records==[]
unchanged,records=reapply.reapply_adaptive_runtime_revision(legacy.encode(),{'local_patches':[]})
assert unchanged.decode()==legacy and records==[]
print('adaptive runtime revision reapply test passed')
