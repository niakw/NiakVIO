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
PATCH = ROOT / "scripts/provider_patches/hls_runtime_integrity_v1.py"

spec = importlib.util.spec_from_file_location("hls_runtime_integrity_v1", PATCH)
assert spec is not None and spec.loader is not None
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

MASTER = """#EXTM3U
#EXT-X-VERSION:6
#EXT-X-MEDIA:TYPE=AUDIO,GROUP-ID=\"aud\",NAME=\"English\",LANGUAGE=\"en\",DEFAULT=YES,AUTOSELECT=YES,URI=\"audio-en.m3u8\"
#EXT-X-MEDIA:TYPE=AUDIO,GROUP-ID=\"aud\",NAME=\"French\",LANGUAGE=\"fr\",DEFAULT=NO,AUTOSELECT=YES,URI=\"audio-fr.m3u8\"
#EXT-X-STREAM-INF:BANDWIDTH=2200000,RESOLUTION=1280x720,AUDIO=\"aud\"
720.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=5200000,RESOLUTION=1920x1080,AUDIO=\"aud\"
1080.m3u8
"""
MEDIA = """#EXTM3U
#EXT-X-TARGETDURATION:10
#EXTINF:10.0,
seg.ts
#EXT-X-ENDLIST
"""


def generated(options: dict) -> str:
    base = '"use strict";\nglobalThis.getStreams=async()=>globalThis.__rows;\n'
    return mod.apply(base, options=options)


NODE = r'''
const fs=require('fs');
const mode=process.argv[3];
const master=fs.readFileSync(process.argv[4],'utf8');
const media=fs.readFileSync(process.argv[5],'utf8');
function headers(ct){return {get:(k)=>String(k).toLowerCase()==='content-type'?ct:''};}
function textResponse(url,body,ct='application/vnd.apple.mpegurl'){
  return {ok:true,status:200,url,headers:headers(ct),text:async()=>body};
}
function tsResponse(url){
  const b=Buffer.alloc(376);b[0]=0x47;b[188]=0x47;
  return {ok:true,status:200,url,headers:headers('video/mp2t'),arrayBuffer:async()=>b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength)};
}
if(mode==='browser'||mode==='native'){
  globalThis.__rows=[{url:'https://media.example/master.m3u8',name:'Purstream',quality:'720p',resolution:'1280x720',language:'VF'}];
  if(mode==='native')globalThis.__native_fetch=function(){};
  globalThis.fetch=async(url)=>{
    url=String(url);
    if(url.endsWith('/master.m3u8'))return textResponse(url,master);
    if(url.endsWith('/720.m3u8')||url.endsWith('/1080.m3u8')||url.endsWith('/audio-en.m3u8')||url.endsWith('/audio-fr.m3u8'))return textResponse(url,media);
    if(url.endsWith('/seg.ts'))return tsResponse(url);
    throw new Error('unexpected fetch '+url);
  };
}else if(mode==='playimdb403'){
  globalThis.__rows=[{url:'https://dead.example/video.mp4',name:'PlayIMDb',quality:'1080p'}];
  globalThis.__native_fetch=function(){};
  globalThis.fetch=async(url)=>({ok:false,status:403,url:String(url),headers:headers('text/html'),text:async()=>''});
}else throw new Error('unknown mode');
require(process.argv[2]);
(async()=>{
  const out=await globalThis.getStreams();
  if(mode==='playimdb403'){
    if(!Array.isArray(out)||out.length!==0)throw new Error('403 row survived '+JSON.stringify(out));
    console.log('PLAYIMDB_403_FAIL_CLOSED_OK');
    return;
  }
  if(!Array.isArray(out)||out.length!==1)throw new Error('unexpected rows '+JSON.stringify(out));
  const row=out[0];
  if(row.quality!=='1080p')throw new Error('quality not upgraded '+JSON.stringify(row));
  if(Number(row.height)!==1080)throw new Error('height missing '+JSON.stringify(row));
  if(row.sourceQuality!=='720p')throw new Error('provider quality not preserved '+JSON.stringify(row));
  if(row.sourceResolution!=='1280x720')throw new Error('provider resolution not preserved '+JSON.stringify(row));
  if(row.language!=='MULTI')throw new Error('multi language not derived '+JSON.stringify(row));
  if(row.sourceLanguage!=='VF')throw new Error('provider language not preserved '+JSON.stringify(row));
  const langs=(row.audioTracks||[]).map(x=>x.language).sort().join(',');
  if(langs!=='en,fr')throw new Error('audio tracks missing '+JSON.stringify(row));
  console.log('HLS_MASTER_FACTS_OK mode='+mode+' quality='+row.quality+' audio='+langs);
})().catch(e=>{console.error(e);process.exit(1)});
'''

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    runner = root / "runner.cjs"
    master = root / "master.m3u8"
    media = root / "media.m3u8"
    runner.write_text(NODE, encoding="utf-8")
    master.write_text(MASTER, encoding="utf-8")
    media.write_text(MEDIA, encoding="utf-8")

    facts_provider = root / "facts.cjs"
    facts_provider.write_text(generated({
        "inspect_master_facts": True,
        "probe_first_segment_native": True,
        "native_probe_max_rows": 2,
        "native_probe_timeout_ms": 1200,
        "timeout_ms": 1200,
        "max_children": 2,
    }), encoding="utf-8")
    for mode in ("browser", "native"):
        result = subprocess.run(
            ["node", str(runner), str(facts_provider), mode, str(master), str(media)],
            cwd=ROOT, capture_output=True, text=True, timeout=6, check=False,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert f"HLS_MASTER_FACTS_OK mode={mode}" in result.stdout, result.stdout

    strict_provider = root / "strict.cjs"
    strict_provider.write_text(generated({
        "probe_all_urls": True,
        "fail_closed_unknown": True,
        "probe_first_segment_native": True,
        "native_probe_max_rows": 2,
        "native_probe_timeout_ms": 900,
        "timeout_ms": 900,
    }), encoding="utf-8")
    result = subprocess.run(
        ["node", str(runner), str(strict_provider), "playimdb403", str(master), str(media)],
        cwd=ROOT, capture_output=True, text=True, timeout=6, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PLAYIMDB_403_FAIL_CLOSED_OK" in result.stdout

cfg = json.loads((ROOT / "provider-overrides.json").read_text(encoding="utf-8"))
providers = cfg["provider_patches"]
for provider_id in ("purstream", "streamzo", "castle"):
    hls = providers[provider_id]["core_options"]["hls_runtime_integrity"]
    assert hls["inspect_master_facts"] is True, (provider_id, hls)
play = providers["playimdb"]["core_options"]["hls_runtime_integrity"]
assert play["probe_all_urls"] is True and play["fail_closed_unknown"] is True, play

print("bounded HLS master facts + PlayIMDb strict 403 tests passed")
