#!/usr/bin/env python3
"""One-shot/signed HLS: root proof is consumed once, then child/segment validation continues."""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
PATCHES = SCRIPTS / "provider_patches"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, PATCHES / filename)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


enrichment = load("one_shot_enrichment", "global_media_enrichment_v1.py")
hls = load("one_shot_hls", "hls_runtime_integrity_v1.py")
sanitizer = load("one_shot_sanitizer", "stream_output_sanitizer_v12.py")

provider = r'''
globalThis.getStreams=async function(){
  return [{name:"signed-player",url:"https://player.example/e/token",headers:{Referer:"https://catalog.example/title"}}];
};
'''
source = enrichment.apply(provider, options={"timeout_ms": 1800})
source = hls.apply(source, options={
    "timeout_ms": 1800,
    "native_probe_timeout_ms": 1500,
    "network_sample_bytes": 32768,
    "inspect_master_facts": True,
})
source = sanitizer.apply(source)

assert "scoped-playback-context-v11-hls-proof-handoff" in source
assert "variant-coherence-v19-core-proof-handoff" in source
assert "function coreHlsProof(stream)" in source
assert "stripCoreHlsProofBody" in source

runtime = r'''
globalThis.__native_fetch=function(){};
let rootCalls=0, childCalls=0, segmentCalls=0;
const master="#EXTM3U\n#EXT-X-STREAM-INF:BANDWIDTH=2500000,RESOLUTION=1280x720\nvideo.m3u8\n";
const media="#EXTM3U\n#EXT-X-TARGETDURATION:60\n#EXTINF:60,\nseg-a.ts\n#EXTINF:60,\nseg-b.ts\n#EXT-X-ENDLIST\n";
function segmentBytes(){
  var a=new Uint8Array(32768);
  for(var i=0;i<a.length;i+=188)a[i]=0x47;
  return a.buffer;
}
globalThis.fetch=async function(url,init){
  const u=String(url),h=(init&&init.headers)||{};
  if(u==="https://player.example/e/token"){
    return {ok:true,status:200,url:u,headers:{get:(k)=>String(k).toLowerCase()==="content-type"?"text/html":""},
      text:async()=>'<script>const source="https://cdn.example/signed/master.m3u8";</script>'};
  }
  if(u==="https://cdn.example/signed/master.m3u8"){
    rootCalls++;
    if(rootCalls>1){
      return {ok:false,status:403,url:u,headers:{get:()=> "text/html"},text:async()=>"<h1>403</h1>"};
    }
    if(h.Referer!=="https://player.example/e/token")throw new Error("missing player Referer on one-shot root: "+JSON.stringify(h));
    return {ok:true,status:200,url:u,headers:{get:(k)=>String(k).toLowerCase()==="content-type"?"application/vnd.apple.mpegurl":""},text:async()=>master};
  }
  if(u==="https://cdn.example/signed/video.m3u8"){
    childCalls++;
    return {ok:true,status:200,url:u,headers:{get:(k)=>String(k).toLowerCase()==="content-type"?"application/vnd.apple.mpegurl":""},text:async()=>media};
  }
  if(u.includes("seg-")){
    segmentCalls++;
    return {ok:true,status:206,url:u,headers:{get:(k)=>String(k).toLowerCase()==="content-type"?"video/mp2t":""},
      arrayBuffer:async()=>segmentBytes()};
  }
  return {ok:false,status:404,url:u,headers:{get:()=> "text/plain"},text:async()=>""};
};
''' + source + r'''
(async()=>{
 const rows=await globalThis.getStreams("95479","anime",1,1);
 console.log(JSON.stringify({rows,rootCalls,childCalls,segmentCalls}));
})().catch(e=>{console.error(e);process.exit(2)});
'''

with tempfile.NamedTemporaryFile("w", suffix=".cjs", delete=False, encoding="utf-8") as handle:
    handle.write(runtime)
    script = Path(handle.name)
try:
    result = subprocess.run(["node", str(script)], capture_output=True, text=True, timeout=20)
finally:
    script.unlink(missing_ok=True)

assert result.returncode == 0, result.stdout + "\n" + result.stderr
payload = json.loads(result.stdout.strip().splitlines()[-1])
assert payload["rootCalls"] == 1, payload
assert payload["childCalls"] >= 1, payload
assert payload["segmentCalls"] >= 1, payload
assert len(payload["rows"]) == 1, payload
row = payload["rows"][0]
assert row["url"] == "https://cdn.example/signed/master.m3u8", row
# The cross-layer body is private/transient. The outer sanitizer also removes
# the proof object itself before anything is exposed to the client.
assert "__nuvioCoreMediaProofV1" not in row, row
assert "body" not in json.dumps(row), row

print("native one-shot HLS root handoff contract passed")
