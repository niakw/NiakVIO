#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRESENTATION = ROOT / "scripts/provider_patches/global_stream_presentation_v1.py"
SANITIZER = ROOT / "scripts/provider_patches/stream_output_sanitizer_v6.py"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

presentation = load(PRESENTATION, "presentation")
sanitizer = load(SANITIZER, "sanitizer")

base = r'''
"use strict";
async function getStreams() {
  return [
    {name:"Purstream",title:"Purstream",quality:"Inconnue",resolution:"1920x1080",url:"https://cdn.example/direct.mp4"},
    {name:"StreamZo",title:"StreamZo",quality:"Unknown",url:"https://cdn.example/master.m3u8"}
  ];
}
module.exports={getStreams};
'''

patched = presentation.apply(base, context={"provider_id": "purstream"})
patched = sanitizer.apply(
    patched,
    options={
        "probe_all_urls": True,
        "probe_direct_media": True,
        "max_probes": 8,
        "probe_timeout_ms": 3000,
        "min_vod_duration_seconds": 60,
    },
    context={"provider_id": "purstream"},
)

runner = r'''
const playlist="#EXTM3U\n#EXT-X-STREAM-INF:BANDWIDTH=5000000,RESOLUTION=1920x1080\nhttps://cdn.example/1080.m3u8\n";
function headers(type){return{get:(key)=>String(key).toLowerCase()==="content-type"?type:""}}
global.fetch=async(url)=>{
  const u=String(url);
  if(u.endsWith("direct.mp4")){
    const bytes=new Uint8Array([0,0,0,24,102,116,121,112,105,115,111,109]);
    return{ok:true,status:200,url:u,headers:headers("video/mp4"),arrayBuffer:async()=>bytes.buffer};
  }
  if(u.endsWith("master.m3u8")){
    const bytes=new TextEncoder().encode(playlist);
    return{ok:true,status:200,url:u,headers:headers("application/vnd.apple.mpegurl"),arrayBuffer:async()=>bytes.buffer};
  }
  throw new Error("unexpected "+u);
};
const provider=require(process.argv[2]);
(async()=>{
  const rows=await provider.getStreams("157336","movie");
  if(rows.length!==2)throw new Error("rows lost "+JSON.stringify(rows));
  if(rows[0].quality!=="1080p")throw new Error("resolution fact quality not recovered: "+JSON.stringify(rows[0]));
  if(rows[1].quality!=="1080p")throw new Error("HLS master quality not recovered: "+JSON.stringify(rows[1]));
  for(const row of rows){
    if(/unknown|inconnue?/i.test(String(row.quality||"")))throw new Error("placeholder quality leaked: "+JSON.stringify(row));
  }
  console.log("TV stream quality recovery passed",JSON.stringify(rows.map(r=>r.quality)));
})().catch(e=>{console.error(e);process.exit(1)});
'''

with tempfile.TemporaryDirectory() as tmp:
    tmp_path = Path(tmp)
    provider = tmp_path / "provider.js"
    test = tmp_path / "test.js"
    provider.write_text(patched, encoding="utf-8")
    test.write_text(runner, encoding="utf-8")
    subprocess.run(["node", str(test), str(provider)], check=True, timeout=20)

facts_source=(ROOT/"scripts/provider_patches/global_stream_facts_v1.py").read_text(encoding="utf-8")
san_source=(ROOT/"scripts/provider_patches/stream_output_sanitizer_v5.py").read_text(encoding="utf-8")
assert "NUVIO_STREAM_QUALITY_RECOVERY_V2" in facts_source
assert "NUVIO_STREAM_QUALITY_RECOVERY_V2" in san_source
assert "RESOLUTION" in san_source
print("stream quality recovery TV contract passed")
