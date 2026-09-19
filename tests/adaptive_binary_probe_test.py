#!/usr/bin/env python3
from __future__ import annotations
import importlib.util
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
script = ROOT / "scripts/provider_patches/adaptive_runtime_recovery_v4.py"
spec = importlib.util.spec_from_file_location("v4", script)
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)
source = mod.apply(
    'module.exports={getStreams:async function(){return [{name:"opaque",url:"https://cdn.example/media/token",headers:{Referer:"https://site.example/watch/1"}}]}};\n',
    options={"provider_name":"Demo","base_url":"https://site.example","types":["movie"],"max_embeds":4},
)
runner = r"""
const vm=require('vm');
const src=process.argv[2],calls=[];
const bytes=Uint8Array.from([0,0,0,24,102,116,121,112,105,115,111,109,0,0,0,0]);
const headers={get:(k)=>{k=k.toLowerCase();if(k==='content-type')return'application/octet-stream';if(k==='content-length')return String(bytes.length);return null},getSetCookie:()=>[]};
const sandbox={module:{exports:{}},exports:{},URL,AbortController,setTimeout,clearTimeout,Uint8Array,fetch:async(url,o={})=>{calls.push({url:String(url),range:o.headers&&o.headers.Range});return{ok:true,status:206,url:'https://cdn.example/final/opaque',headers,arrayBuffer:async()=>bytes.buffer,text:async()=>{throw new Error('binary body must not be consumed as text')}}}};
sandbox.globalThis=sandbox;
vm.runInNewContext(src,sandbox,{timeout:5000});
sandbox.module.exports.getStreams({tmdbId:'1',mediaType:'movie',title:'Demo',year:2020}).then(rows=>console.log(JSON.stringify({rows,calls}))).catch(e=>{console.error(e);process.exit(1)});
"""
with tempfile.TemporaryDirectory() as d:
    runner_path=Path(d)/"runner.cjs"
    runner_path.write_text(runner,encoding="utf-8")
    result=subprocess.run(["node",str(runner_path),source],capture_output=True,text=True,timeout=20)
    assert result.returncode==0,result.stderr
    data=json.loads(result.stdout.strip())
    assert len(data["rows"])==1,data
    row=data["rows"][0]
    assert row["url"]=="https://cdn.example/final/opaque"
    assert row["isDirect"] is True
    assert data["calls"][0]["range"]=="bytes=0-16383",data

source_unsafe = mod.apply(
    'module.exports={getStreams:async function(){return [{name:"opaque",url:"https://cdn.example/media/unsafe",headers:{Referer:"https://site.example/watch/1"}}]}};\n',
    options={"provider_name":"Demo","base_url":"https://site.example","types":["movie"],"max_embeds":4},
)
unsafe_runner = r"""
const vm=require('vm');
const src=process.argv[2],calls=[];let textCalls=0,arrayCalls=0;
const headers={get:(k)=>k.toLowerCase()==='content-type'?'application/octet-stream':null,getSetCookie:()=>[]};
const sandbox={module:{exports:{}},exports:{},URL,AbortController,setTimeout,clearTimeout,Uint8Array,fetch:async(url,o={})=>{calls.push({url:String(url),range:o.headers&&o.headers.Range});return{ok:true,status:200,url:String(url),headers,text:async()=>{textCalls++;throw new Error('must not read unsafe binary as text')},arrayBuffer:async()=>{arrayCalls++;throw new Error('must not buffer unbounded binary')}}}};
sandbox.globalThis=sandbox;
vm.runInNewContext(src,sandbox,{timeout:5000});
sandbox.module.exports.getStreams({tmdbId:'1',mediaType:'movie',title:'Demo',year:2020}).then(rows=>console.log(JSON.stringify({rows,calls,textCalls,arrayCalls}))).catch(e=>{console.error(e);process.exit(1)});
"""
with tempfile.TemporaryDirectory() as d:
    p=Path(d)/"unsafe.cjs";p.write_text(unsafe_runner,encoding="utf-8")
    result=subprocess.run(["node",str(p),source_unsafe],capture_output=True,text=True,timeout=20)
    assert result.returncode==0,result.stderr
    data=json.loads(result.stdout.strip())
    assert data["rows"]==[],data
    assert data["textCalls"]==0,data
    assert data["arrayCalls"]==0,data
    assert data["calls"][0]["range"]=="bytes=0-16383",data

print("adaptive bounded binary probe test passed")
