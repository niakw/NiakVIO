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
ENGINE = ROOT / "engine_v2/src/stream-presentation.mjs"

spec = importlib.util.spec_from_file_location("hls_runtime_integrity_v1", PATCH)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

base = r'''
module.exports={getStreams:async()=>[{
  name:"Kehflix - Inconnue",
  title:"Kehflix - Inconnue",
  quality:"Inconnue",
  url:"https://media.example/master.m3u8",
  type:"hls"
}]};
'''
patched = module.apply(base, {
    "inspect_master_facts": True,
    "probe_first_segment_native": True,
    "native_probe_max_rows": 4,
    "native_probe_timeout_ms": 1500,
    "minimum_vod_duration_seconds": 90,
})

master = """#EXTM3U
#EXT-X-MEDIA:TYPE=AUDIO,GROUP-ID="aud",NAME="Korean",LANGUAGE="ko",CHANNELS="2",URI="audio-ko.m3u8"
#EXT-X-MEDIA:TYPE=SUBTITLES,GROUP-ID="subs",NAME="French",LANGUAGE="fr",URI="sub-fr.m3u8"
#EXT-X-STREAM-INF:BANDWIDTH=6200000,AVERAGE-BANDWIDTH=5800000,RESOLUTION=1440x720,CODECS="avc1.64001f,mp4a.40.2",FRAME-RATE=23.976,VIDEO-RANGE=SDR,AUDIO="aud",SUBTITLES="subs"
video-720.m3u8
"""
media = """#EXTM3U
#EXT-X-MEDIA-SEQUENCE:1
#EXTINF:6,
seg.ts
"""

runner = r'''
const {pathToFileURL}=require('url');
const fs=require('fs');
const provider=require(process.argv[2]);
const enginePath=process.argv[3];
const master=fs.readFileSync(process.argv[4],'utf8');
const media=fs.readFileSync(process.argv[5],'utf8');
function headers(ct){return {get:(k)=>String(k).toLowerCase()==='content-type'?ct:''};}
function textResponse(url,body){return {ok:true,status:200,url,headers:headers('application/vnd.apple.mpegurl'),text:async()=>body};}
function tsResponse(url){const b=Buffer.alloc(376);b[0]=0x47;b[188]=0x47;return {ok:true,status:200,url,headers:headers('video/mp2t'),arrayBuffer:async()=>b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength)};}
globalThis.__native_fetch=function(){};
globalThis.fetch=async function(url){
  url=String(url);
  if(url.endsWith('/master.m3u8'))return textResponse(url,master);
  if(url.endsWith('/video-720.m3u8')||url.endsWith('/audio-ko.m3u8')||url.endsWith('/sub-fr.m3u8'))return textResponse(url,media);
  if(url.endsWith('/seg.ts'))return tsResponse(url);
  throw new Error('unexpected '+url);
};
(async()=>{
  const rows=await provider.getStreams('1','anime',1,1);
  if(!Array.isArray(rows)||rows.length!==1)throw new Error('HLS row missing '+JSON.stringify(rows));
  const raw=rows[0];
  if(Array.isArray(raw.subtitles)&&raw.subtitles.some(x=>x&&!x.url))throw new Error('integrated HLS subtitle leaked into external subtitles '+JSON.stringify(raw));
  if(!Array.isArray(raw.hlsMasterSubtitleTracks)||raw.hlsMasterSubtitleTracks[0]?.language!=='fr')throw new Error('integrated HLS subtitle metadata missing '+JSON.stringify(raw));
  const mod=await import(pathToFileURL(enginePath).href);
  const presented=mod.presentStreamCandidate(raw,{title:'Example Anime',year:2026,mediaType:'anime',originalLanguage:'ko'},{id:'kehflix',name:'Kehflix'});
  console.log(JSON.stringify(presented));
})().catch(e=>{console.error(e);process.exit(1)});
'''

with tempfile.TemporaryDirectory() as tmp:
    root=Path(tmp)
    provider=root/"provider.cjs"
    run=root/"runner.cjs"
    master_file=root/"master.m3u8"
    media_file=root/"media.m3u8"
    provider.write_text(patched,encoding="utf-8")
    run.write_text(runner,encoding="utf-8")
    master_file.write_text(master,encoding="utf-8")
    media_file.write_text(media,encoding="utf-8")
    result=subprocess.run(
        ["node",str(run),str(provider),str(ENGINE),str(master_file),str(media_file)],
        cwd=ROOT,capture_output=True,text=True,timeout=12,check=False,
    )

assert result.returncode==0,result.stdout+result.stderr
row=json.loads(result.stdout.strip().splitlines()[-1])
assert row["name"]=="Kehflix - 720p",row
assert "Inconnue" not in row["name"] and "Unknown" not in row["name"],row
required={"720p-hd","hls","avc","23.976fps","video-bitrate","aac","2.0","lang-ko","sub-fr","sdr"}
missing=required-set(row.get("badgeIds") or [])
assert not missing,(missing,row)
for needle in ("AVC","23.976 fps","HLS","AAC","2.0","5.8 Mbps max","Korean"):
    assert needle in row.get("description",""),(needle,row)
print("HLS master facts reach title/badges while integrated subtitles stay outside external caption contract")
