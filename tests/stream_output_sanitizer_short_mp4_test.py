#!/usr/bin/env python3
from __future__ import annotations
import importlib.util, subprocess, sys, tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
PATCH=ROOT/"scripts/provider_patches/stream_output_sanitizer.py"
spec=importlib.util.spec_from_file_location("stream_output_sanitizer_short_mp4",PATCH)
assert spec and spec.loader
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)

base=r'''module.exports={getStreams:async()=>[
 {name:"short",url:"https://media.example/short.mp4"},
 {name:"full",url:"https://media.example/full.mp4"}
]};'''
patched=mod.apply(base,options={"probe_all_urls":True,"probe_direct_media":True,"max_probes":8,"probe_timeout_ms":1200,"min_vod_duration_seconds":60})
assert '"implementationVersion":10' in patched

runner=r'''
const assert=require("assert");
function put32(b,o,v){b[o]=(v>>>24)&255;b[o+1]=(v>>>16)&255;b[o+2]=(v>>>8)&255;b[o+3]=v&255}
function mp4(seconds){
 const b=new Uint8Array(128);
 put32(b,0,24);b.set([102,116,121,112],4);
 put32(b,24,32);b.set([109,118,104,100],28);b[32]=0;
 put32(b,44,1000);put32(b,48,seconds*1000);
 return b;
}
function response(url,seconds){const b=mp4(seconds);return {ok:true,status:206,url,headers:{get:n=>String(n).toLowerCase()==="content-type"?"video/mp4":""},arrayBuffer:async()=>b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength)}}
global.fetch=async u=>String(u).includes("short.mp4")?response(String(u),10):response(String(u),120);
PATCHED
module.exports.getStreams("1","movie").then(rows=>{
 assert.deepEqual(rows.map(x=>x.name),["full"],JSON.stringify(rows));
 console.log("SHORT_MP4_REJECT_OK");
}).catch(e=>{console.error(e);process.exit(1)});
'''.replace("PATCHED",patched)
with tempfile.NamedTemporaryFile("w",suffix=".cjs",encoding="utf-8",delete=False) as h:
    h.write(runner);p=Path(h.name)
try:
    done=subprocess.run(["node",str(p)],cwd=ROOT,text=True,capture_output=True,timeout=10,check=False)
    assert done.returncode==0,done.stdout+done.stderr
    assert "SHORT_MP4_REJECT_OK" in done.stdout
finally:
    p.unlink(missing_ok=True)
print("stream output sanitizer rejects short MP4 duration proof")
