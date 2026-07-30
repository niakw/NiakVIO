#!/usr/bin/env python3
from pathlib import Path
import importlib.util

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('patch',ROOT/'scripts/provider_patches/adaptive_domain_recovery.py')
mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
source='module.exports={getStreams:function(){return fetch("https://old.example/api/search?q=x")}};'
out=mod.apply(source,options={'groups':[{'hosts':['old.example'],'candidates':['https://new.example','https://backup.example']}]})
assert 'NUVIO_ADAPTIVE_DOMAIN_RECOVERY_V1' in out
assert 'new.example' not in out  # configuration is encoded, not exposed as brittle literal rewrites
assert out.endswith(source)
out2=mod.apply(out,options={'groups':[{'hosts':['old.example'],'candidates':['https://new.example']}]})
assert out2.count('NUVIO_ADAPTIVE_DOMAIN_RECOVERY_V1:BEGIN') == 1
print('adaptive domain recovery test passed')
