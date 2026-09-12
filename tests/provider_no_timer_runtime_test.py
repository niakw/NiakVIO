#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / "scripts/provider_patches/global_media_type_resolution_v1.py"
spec = importlib.util.spec_from_file_location("media_type_no_timer", PATCH)
assert spec is not None and spec.loader is not None
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

base = r'''
"use strict";
async function getStreams(id) {
  await fetch("https://provider.example/" + id);
  return [{url:"https://media.example/"+id+".mp4"}];
}
module.exports={getStreams};
'''
patched = mod.apply(
    base,
    options={
        "semantic_types": ["movie"],
        "provider_timeout_ms": 25_000,
        "tv_provider_timeout_ms": 25_000,
        "fetch_slice_ms": 7_000,
        "max_hard_failures": 3,
        "supersede_settle_ms": 700,
    },
)

runner = r'''
global.setTimeout=undefined;
global.clearTimeout=undefined;
global.navigator={userAgent:"Nuvio Desktop macOS"};
const calls=[];
global.fetch=(url)=>{
  const u=String(url);calls.push(u);
  if(u.endsWith("/first"))return new Promise(()=>{});
  return Promise.resolve({ok:true,status:200,url:u,headers:{get:()=>"video/mp4"},text:async()=>"",json:async()=>({})});
};
const p=require(process.argv[2]);
(async()=>{
  const first=p.getStreams("first","movie");
  await Promise.resolve();
  const second=p.getStreams("second","movie");
  const rows=await second;
  const stale=await first;
  if(!Array.isArray(rows)||rows.length!==1||!String(rows[0].url).includes("second.mp4"))throw new Error("latest result missing "+JSON.stringify(rows));
  if(!Array.isArray(stale)||stale.length!==0)throw new Error("stale result leaked "+JSON.stringify(stale));
  if(global.__nuvioProviderRequestToken!=null)throw new Error("request token leaked");
  console.log("NO_TIMER_RUNTIME_OK "+JSON.stringify(calls));
})().catch(e=>{console.error(e);process.exit(1)});
'''

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    provider = root / "provider.js"
    test = root / "test.js"
    provider.write_text(patched, encoding="utf-8")
    test.write_text(runner, encoding="utf-8")
    subprocess.run(["node", str(test), str(provider)], check=True, timeout=5)

source = PATCH.read_text(encoding="utf-8")
assert 'if(typeof setTimeout!=="function"){await Promise.resolve();return}' in source
assert 'typeof setTimeout!=="function"||slice<=0' in source
assert 'typeof clearTimeout==="function"' in source
assert 'Promise.race([base.apply(this,args),abortPromise])' in source
print("provider no-timer runtime contract passed")
