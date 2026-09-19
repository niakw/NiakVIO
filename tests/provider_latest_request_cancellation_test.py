#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / "scripts/provider_patches/global_media_type_resolution_v1.py"
spec = importlib.util.spec_from_file_location("media_type", PATCH)
assert spec is not None and spec.loader is not None
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

base = r'''
"use strict";
async function getStreams(tmdbId, mediaType) {
  try {
    await fetch("https://provider.example/" + tmdbId + "/one");
  } catch (_) {
    // This is the critical regression shape: a stale provider catches cancellation
    // and tries a fallback route after the user has already navigated elsewhere.
    try { await fetch("https://provider.example/" + tmdbId + "/two"); } catch (_) {}
  }
  return [];
}
module.exports = { getStreams };
'''
patched = mod.apply(
    base,
    options={
        "semantic_types": ["movie"],
        "provider_timeout_ms": 10_000,
        "tv_provider_timeout_ms": 10_000,
        "supersede_settle_ms": 1_000,
    },
)

runner = r'''
const calls=[];
function abortedError(){const e=new Error("aborted");e.name="AbortError";return e}
global.navigator={userAgent:"NuvioTV Android TV"};
global.fetch=(url,init={})=>{
  const value=String(url);calls.push(value);
  if(value.includes("/1/one")){
    return new Promise((resolve,reject)=>{
      const signal=init&&init.signal;
      if(signal&&signal.aborted)return reject(abortedError());
      if(signal&&typeof signal.addEventListener==="function")signal.addEventListener("abort",()=>reject(abortedError()),{once:true});
    });
  }
  return Promise.resolve({ok:true,status:200,url:value,headers:{get:()=>"text/plain"},text:async()=>"ok",json:async()=>({})});
};
const provider=require(process.argv[2]);
(async()=>{
  const first=provider.getStreams("1","movie");
  await Promise.resolve();
  const second=provider.getStreams("2","movie");
  await Promise.all([first,second]);
  if(calls.some(v=>v.includes("/1/two")))throw new Error("superseded request launched fallback fetch: "+JSON.stringify(calls));
  if(!calls.some(v=>v.includes("/1/one")))throw new Error("first request never started");
  if(!calls.some(v=>v.includes("/2/one")))throw new Error("new request did not run");
  if(global.__nuvioProviderRequestToken!=null)throw new Error("request token leaked after final invocation");
  console.log("latest provider request cancellation test passed",JSON.stringify(calls));
})().catch(e=>{console.error(e);process.exit(1)});
'''

with tempfile.TemporaryDirectory() as tmp:
    tmp_path = Path(tmp)
    provider = tmp_path / "provider.js"
    test = tmp_path / "test.js"
    provider.write_text(patched, encoding="utf-8")
    test.write_text(runner, encoding="utf-8")
    subprocess.run(["node", str(test), str(provider)], check=True, timeout=20)

source = PATCH.read_text(encoding="utf-8")
for needle in (
    "NUVIO_PROVIDER_LATEST_REQUEST_OWNS_FETCH_V2",
    "abortController(priorController)",
    "await settlePrior(priorDone)",
    "budgetedFetch(fetchBase,requestDeadline,requestToken,requestController)",
):
    assert needle in source, needle

print("provider latest-request cancellation contract passed")
