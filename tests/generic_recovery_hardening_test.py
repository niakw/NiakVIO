#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# Historical peer domains must participate in generic candidate selection.
hubs = load("hubs", ROOT / "scripts" / "resolve_provider_hubs.py")
candidates, _ = hubs.gather_candidates(
    "demo",
    {
        "direct_candidates": ["https://demo.current"],
        "historical_terminal_candidates": ["https://demo.backup"],
        "sources": [],
        "manifest_status": "Actif",
    },
    {},
    "quick",
    0.1,
)
assert any(
    row.get("url") == "https://demo.backup" and row.get("source_type") == "historical_peer"
    for row in candidates
)

# Runtime domain failover must retry a configured peer on HTTP 403.
domain = load("domain", ROOT / "scripts" / "provider_patches" / "adaptive_domain_recovery.py")
source = 'module.exports={getStreams:async()=>{var r=await globalThis.fetch("https://old.example/api/x");return [{url:r.url,status:r.status}]}};'
patched = domain.apply(
    source,
    options={"groups": [{"hosts": ["old.example"], "candidates": ["https://new.example"]}]},
)
runner = r'''
const vm=require("vm");
const src=process.argv[2], calls=[];
function response(url,status){return {url,status,ok:status>=200&&status<300,headers:{get:()=>"application/json"},text:async()=>"{}",json:async()=>({})};}
const box={module:{exports:{}},exports:{},Buffer,URL,fetch:async function(u){u=String(u);calls.push(u);return response(u,u.includes("old.example")?403:200)}};
vm.runInNewContext(src,box);
box.module.exports.getStreams().then(v=>console.log(JSON.stringify({calls,v}))).catch(e=>{console.error(e);process.exit(1)});
'''
with tempfile.TemporaryDirectory() as td:
    p = Path(td) / "run.cjs"
    p.write_text(runner, encoding="utf-8")
    cp = subprocess.run(["node", str(p), patched], capture_output=True, text=True, timeout=10, check=True)
    data = json.loads(cp.stdout.strip().splitlines()[-1])
assert "https://new.example/api/x" in data["calls"], data
assert data["v"][0]["status"] == 200, data

# Adaptive V4 must capture a player/API URL visited by native code, replay the
# exact route across a sibling endpoint family, and never fall back to a blocked
# fake-media URL.
v4 = load("v4", ROOT / "scripts" / "provider_patches" / "adaptive_runtime_recovery_v4.py")
base = '''module.exports={getStreams:async function(q){await globalThis.fetch("https://demoendpointold.workers.dev/api/stream/token/abc");return [{url:"https://cdn.invalid/troll/master.m3u8"}]}};'''
out = v4.apply(
    base,
    options={
        "provider_name": "Demo",
        "base_url": "https://demo.example",
        "endpoint_origins": [
            "https://demoendpointold.workers.dev",
            "https://demoendpointnew.workers.dev",
        ],
        "types": ["movie"],
        "search_paths": [],
        "direct_paths": [],
        "blocked_path_patterns": ["/troll/"],
        "timeout_ms": 3000,
    },
)
assert '"runtimeRevision":"generic-core-v2"' in out
runner2 = r'''
const vm=require("vm"); const src=process.argv[2], calls=[];
function headers(type){return {get:(k)=>String(k).toLowerCase()==="content-type"?type:null,getSetCookie:()=>[]};}
function res(url,status,type){return {url,status,ok:status>=200&&status<300,headers:headers(type),body:null,text:async()=>"",json:async()=>({}),arrayBuffer:async()=>new ArrayBuffer(0)};}
const box={
  module:{exports:{}},exports:{},Buffer,URL,AbortController,ArrayBuffer,Uint8Array,setTimeout,clearTimeout,
  fetch:async function(input){
    let u=typeof input==="string"?input:String(input&&input.url||input);calls.push(u);
    if(u.includes("demoendpointold.workers.dev"))return res(u,500,"text/plain");
    if(u.includes("demoendpointnew.workers.dev"))return res(u,200,"video/mp4");
    if(u.includes("api.themoviedb.org"))return res(u,404,"application/json");
    return res(u,404,"text/plain");
  }
};
vm.runInNewContext(src,box);
box.module.exports.getStreams({tmdbId:"157336",mediaType:"movie",title:"Demo",year:2024}).then(v=>console.log(JSON.stringify({calls,v}))).catch(e=>{console.error(e);process.exit(1)});
'''
with tempfile.TemporaryDirectory() as td:
    p = Path(td) / "run.cjs"
    p.write_text(runner2, encoding="utf-8")
    cp = subprocess.run(["node", str(p), out], capture_output=True, text=True, timeout=15, check=True)
    data = json.loads(cp.stdout.strip().splitlines()[-1])
assert any("demoendpointnew.workers.dev/api/stream/token/abc" in u for u in data["calls"]), data
assert data["v"], data
assert data["v"][0]["url"].startswith("https://demoendpointnew.workers.dev/api/stream/token/abc"), data
assert all("/troll/" not in row.get("url", "") for row in data["v"]), data

print("generic recovery hardening test passed")
