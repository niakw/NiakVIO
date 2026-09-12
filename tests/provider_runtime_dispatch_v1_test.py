#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
PATCH = ROOT / "scripts/provider_patches/global_provider_runtime_dispatch_v1.py"
spec = importlib.util.spec_from_file_location("provider_runtime_dispatch_v1", PATCH)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)

source = r'''
/* BEGIN NIAKVIO_PROVIDER */
/* NIAKVIO_PROVIDER_ID:synthetic */
/* NIAKVIO_PROVIDER_BASE_OWNED_V3 */
;(function(g){
  g.__niakvioProviderRuntimeResolverV1={provider:"synthetic",resolve:async function(args){
    var type=String(args[1]||"").toLowerCase();
    if(type!=="anime")return null;
    return [{url:"https://resolver.example/master.m3u8",name:"resolver"}];
  }};
})(typeof globalThis!=="undefined"?globalThis:this);
module.exports={getStreams:async function(){return [{url:"https://native.example/master.m3u8",name:"native"}]}};
/* NUVIO_GLOBAL_CORE_START_BOUNDARY_V1 */
/* END NIAKVIO_PROVIDER */
'''.lstrip()

patched = mod.apply(source)
assert patched != source
assert patched.count("STARTFIX:CORE.PROVIDER_RUNTIME_DISPATCH.V1") == 1
assert patched.count("CLOSEFIX:CORE.PROVIDER_RUNTIME_DISPATCH.V1") == 1
assert mod.apply(patched) == patched

runner = r'''
const fs=require('fs'),vm=require('vm');
const src=fs.readFileSync(process.argv[1],'utf8');
const box={module:{exports:{}},exports:{},console,URL};box.globalThis=box;
vm.createContext(box);vm.runInContext(src,box);
(async()=>{
 const anime=await box.module.exports.getStreams('1','anime',1,1);
 const movie=await box.module.exports.getStreams('1','movie',1,1);
 console.log(JSON.stringify({anime,movie}));
})().catch(e=>{console.error(e);process.exit(1)});
'''
with tempfile.TemporaryDirectory() as td:
    path=Path(td)/'provider.js'; path.write_text(patched)
    out=subprocess.check_output(['node','-e',runner,str(path)],text=True)
result=json.loads(out)
assert result['anime'][0]['url']=='https://resolver.example/master.m3u8', result
assert result['movie'][0]['url']=='https://native.example/master.m3u8', result
print('provider runtime dispatch v1 tests passed')
