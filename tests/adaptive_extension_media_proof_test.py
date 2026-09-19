#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
script = ROOT / "scripts" / "provider_patches" / "adaptive_runtime_recovery_v5.py"
spec = importlib.util.spec_from_file_location("adaptive_v5", script)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)

options = {
    "provider_name": "Demo",
    "base_url": "https://site.example",
    "types": ["movie"],
    "max_embeds": 6,
    "max_depth": 4,
}
source = module.apply(
    'module.exports={getStreams:async function(){return [{name:"fake-mp4",url:"https://files.example/Interstellar_2014.mp4",headers:{Referer:"https://site.example/watch/interstellar"}}]}};\n',
    options=options,
)
assert "NUVIO_VERIFIED_MEDIA_RUNTIME_RECOVERY_V5" in source
assert "NUVIO_ADAPTIVE_RUNTIME_RECOVERY_V4" not in source
assert '"runtimeRevision":"generic-core-v3"' in source
assert module.apply(source, options=options) == source

runner = r"""
const vm=require('vm');
const src=process.argv[2],calls=[];
function headers(type,length=0){return{get:(k)=>{k=String(k).toLowerCase();if(k==='content-type')return type;if(k==='content-length')return length?String(length):null;return null},getSetCookie:()=>[]}}
function htmlResponse(url,body){return{ok:true,status:200,url,headers:headers('text/html; charset=utf-8'),text:async()=>body,arrayBuffer:async()=>Buffer.from(body).buffer}}
const hls='#EXTM3U\n#EXT-X-TARGETDURATION:6\n#EXTINF:6,\nseg.ts\n#EXT-X-ENDLIST\n';
const sandbox={module:{exports:{}},exports:{},URL,AbortController,setTimeout,clearTimeout,Uint8Array,Buffer,
 fetch:async(url,opts={})=>{
   url=String(url);calls.push({url,range:opts.headers&&opts.headers.Range||null});
   if(url==='https://files.example/Interstellar_2014.mp4'){
     return htmlResponse(url,'<html><iframe src="https://player.example/embed/abc"></iframe></html>');
   }
   if(url==='https://player.example/embed/abc'){
     return htmlResponse(url,'<script>const player={file:"https://cdn.example/master.m3u8"};</script>');
   }
   if(url==='https://cdn.example/master.m3u8'){
     return {ok:true,status:200,url,headers:headers('text/plain',Buffer.byteLength(hls)),body:null,text:async()=>hls,arrayBuffer:async()=>Uint8Array.from(Buffer.from(hls)).buffer};
   }
   throw new Error('unexpected '+url);
 }};
sandbox.globalThis=sandbox;
vm.runInNewContext(src,sandbox,{timeout:5000});
sandbox.module.exports.getStreams({tmdbId:'157336',mediaType:'movie',title:'Interstellar',year:2014}).then(rows=>{
 console.log(JSON.stringify({rows,calls}));
}).catch(e=>{console.error(e);process.exit(1)});
"""

with tempfile.TemporaryDirectory() as directory:
    path = Path(directory) / "runner.cjs"
    path.write_text(runner, encoding="utf-8")
    result = subprocess.run(["node", str(path), source], capture_output=True, text=True, timeout=25)
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout.strip())

rows = data["rows"]
assert len(rows) == 1, data
assert rows[0]["url"] == "https://cdn.example/master.m3u8", data
assert rows[0]["isDirect"] is True, data
assert rows[0]["url"] != "https://files.example/Interstellar_2014.mp4"

fake_calls = [row for row in data["calls"] if row["url"] == "https://files.example/Interstellar_2014.mp4"]
assert len(fake_calls) >= 2, data
assert fake_calls[0]["range"] == "bytes=0-16383", data
assert any(row["url"] == "https://player.example/embed/abc" for row in data["calls"]), data
assert any(row["url"] == "https://cdn.example/master.m3u8" for row in data["calls"]), data

print("adaptive extension media proof test passed")
