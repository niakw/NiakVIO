#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import subprocess
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / "scripts/provider_patches/global_media_type_resolution_v1.py"
spec = importlib.util.spec_from_file_location("media_type_failfast_v33", PATCH)
assert spec is not None and spec.loader is not None
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

source = PATCH.read_text(encoding="utf-8")
for needle in (
    "tmdb-data-contract-launch-gate-v33-25s-isolated-failfast",
    'cfg.get("provider_timeout_ms", 25_000)',
    'cfg.get("tv_provider_timeout_ms", 25_000)',
    '"fetchSliceMs"',
    '"maxHardFailures"',
    "function providerFailFastError(status)",
    "function invokeNativeWithBudget(native,self,args,requestController,requestToken)",
):
    assert needle in source, needle


def patch_provider(body: str, *, slice_ms: int = 120, hard_failures: int = 2) -> str:
    return mod.apply(
        body,
        options={
            "semantic_types": ["movie"],
            "provider_timeout_ms": 25_000,
            "tv_provider_timeout_ms": 25_000,
            "fetch_slice_ms": slice_ms,
            "max_hard_failures": hard_failures,
            "supersede_settle_ms": 200,
        },
    )


def run_node(provider_source: str, runner: str, timeout: float = 4.0) -> tuple[str, float]:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        provider = root / "provider.js"
        test = root / "test.js"
        provider.write_text(provider_source, encoding="utf-8")
        test.write_text(runner, encoding="utf-8")
        started = time.monotonic()
        result = subprocess.run(
            ["node", str(test), str(provider)],
            text=True,
            capture_output=True,
            timeout=timeout,
        )
        elapsed = time.monotonic() - started
        if result.returncode:
            raise AssertionError(result.stdout + "\n" + result.stderr)
        return result.stdout, elapsed


# First hard failure must NOT kill a provider: a second route may be valid.
fallback_provider = patch_provider(
    r'''
"use strict";
async function getStreams(){
  for(const suffix of ["first","second"]){
    try{
      const r=await fetch("https://provider.example/"+suffix);
      if(!r.ok)throw new Error("http_"+r.status);
      return [{url:"https://media.example/ok.mp4"}];
    }catch(_){}
  }
  return [];
}
module.exports={getStreams};
''',
    hard_failures=3,
)
fallback_runner = r'''
let calls=[];
global.navigator={userAgent:"Nuvio TV Android"};
global.fetch=async u=>{const x=String(u);calls.push(x);const ok=x.endsWith("/second");return {ok,status:ok?200:403,url:x,headers:{get:()=>"text/plain"},text:async()=>"",json:async()=>({})}};
const p=require(process.argv[2]);
(async()=>{const rows=await p.getStreams("157336","movie");if(rows.length!==1)throw new Error("fallback killed "+JSON.stringify({calls,rows}));if(calls.length!==2)throw new Error("unexpected calls "+JSON.stringify(calls));console.log("FIRST_403_FALLBACK_OK")})().catch(e=>{console.error(e);process.exit(1)});
'''
out, _ = run_node(fallback_provider, fallback_runner)
assert "FIRST_403_FALLBACK_OK" in out

# Repeated hard HTTP failures become fail-fast: later provider fallbacks never hit network.
hard_provider = patch_provider(
    r'''
"use strict";
async function getStreams(){
  for(let i=0;i<7;i++){
    try{const r=await fetch("https://blocked.example/"+i);if(!r.ok)throw new Error("http_"+r.status)}catch(_){}
  }
  return [];
}
module.exports={getStreams};
''',
    hard_failures=3,
)
hard_runner = r'''
let calls=0;
global.navigator={userAgent:"Nuvio Desktop macOS"};
global.fetch=async u=>{calls++;return {ok:false,status:403,url:String(u),headers:{get:()=>"text/html"},text:async()=>"",json:async()=>({})}};
const p=require(process.argv[2]);
(async()=>{const rows=await p.getStreams("157336","movie");if(rows.length)throw new Error("unexpected rows");if(calls!==3)throw new Error("fail-fast did not stop network calls: "+calls);console.log("REPEATED_403_FAILFAST_OK calls="+calls)})().catch(e=>{console.error(e);process.exit(1)});
'''
out, _ = run_node(hard_provider, hard_runner)
assert "REPEATED_403_FAILFAST_OK" in out

# A native fetch bridge that ignores AbortSignal forever gets a short per-fetch slice;
# repeated stalls stop before the 25 s provider budget is consumed.
stall_provider = patch_provider(
    r'''
"use strict";
async function getStreams(){
  for(let i=0;i<6;i++){
    try{await fetch("https://dead.example/"+i)}catch(_){}
  }
  return [];
}
module.exports={getStreams};
''',
    slice_ms=120,
    hard_failures=2,
)
stall_runner = r'''
let calls=0;
global.navigator={userAgent:"Nuvio TV Android"};
global.fetch=()=>{calls++;return new Promise(()=>{})};
const p=require(process.argv[2]);
(async()=>{const started=Date.now();const rows=await p.getStreams("157336","movie");const elapsed=Date.now()-started;if(rows.length)throw new Error("unexpected rows");if(calls!==2)throw new Error("stalled network calls="+calls);if(elapsed>900)throw new Error("dead provider too slow "+elapsed);console.log("STALL_FAILFAST_OK elapsed="+elapsed+" calls="+calls)})().catch(e=>{console.error(e);process.exit(1)});
'''
out, elapsed = run_node(stall_provider, stall_runner)
assert "STALL_FAILFAST_OK" in out
assert elapsed < 2.0

# Independent provider executions: start a dead provider process, then prove a healthy
# provider returns immediately instead of waiting for the dead provider's budget.
healthy_provider = patch_provider(
    'module.exports={getStreams:async()=>{const r=await fetch("https://healthy.example/ok");return r.ok?[{url:"https://media.example/healthy.mp4"}]:[]}};\n',
)
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    dead = root / "dead.js"
    healthy = root / "healthy.js"
    dead_runner = root / "dead-runner.js"
    healthy_runner = root / "healthy-runner.js"
    dead.write_text(stall_provider, encoding="utf-8")
    healthy.write_text(healthy_provider, encoding="utf-8")
    dead_runner.write_text(
        'global.navigator={userAgent:"Nuvio TV Android"};global.fetch=()=>new Promise(()=>{});const p=require(process.argv[2]);p.getStreams("1","movie").then(r=>{console.log("DEAD_DONE "+r.length)}).catch(e=>{console.error(e);process.exit(1)});',
        encoding="utf-8",
    )
    healthy_runner.write_text(
        'global.navigator={userAgent:"Nuvio TV Android"};global.fetch=async u=>({ok:true,status:200,url:String(u),headers:{get:()=>"video/mp4"},text:async()=>"",json:async()=>({})});const p=require(process.argv[2]);p.getStreams("2","movie").then(r=>{if(r.length!==1)throw new Error("healthy lost");console.log("HEALTHY_DONE")}).catch(e=>{console.error(e);process.exit(1)});',
        encoding="utf-8",
    )
    dead_proc = subprocess.Popen(["node", str(dead_runner), str(dead)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    time.sleep(0.03)
    healthy_started = time.monotonic()
    healthy_result = subprocess.run(["node", str(healthy_runner), str(healthy)], text=True, capture_output=True, timeout=2)
    healthy_elapsed = time.monotonic() - healthy_started
    if healthy_result.returncode:
        raise AssertionError(healthy_result.stdout + "\n" + healthy_result.stderr)
    assert "HEALTHY_DONE" in healthy_result.stdout
    assert healthy_elapsed < 0.8, healthy_elapsed
    dead_out, dead_err = dead_proc.communicate(timeout=2)
    if dead_proc.returncode:
        raise AssertionError(dead_out + "\n" + dead_err)
    assert "DEAD_DONE 0" in dead_out

print("provider execution fail-fast v33 contract passed")
