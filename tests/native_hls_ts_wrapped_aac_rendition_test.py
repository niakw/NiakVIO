#!/usr/bin/env python3
"""Source-owned HLS audio proof: TS-wrapped .aac is not a corrupt ADTS stream.

Reproduces the *class* of NuvioTV/Purstream Interstellar observation:
a master and video segments validate, while an external audio playlist points
to a .aac path that actually serves MPEG-TS. No private media URLs or real
third-party service are used. The real client still owns playback acceptance.
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
p = ROOT / "scripts/provider_patches/hls_runtime_integrity_v1.py"
spec = importlib.util.spec_from_file_location("hls_audio_transport", p)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

base = r"""globalThis.getStreams=async function(){
 return [{url:"https://fixture.invalid/master.m3u8",type:"hls",
   name:"fixture 1080p MULTI",
   headers:{Referer:"https://fixture.invalid/title",Origin:"https://fixture.invalid"}}];
};"""
options = {
    "timeout_ms": 2000,
    "max_children": 4,
    "probe_first_segment_native": True,
    "native_probe_max_rows": 2,
    "native_probe_timeout_ms": 1500,
    "network_sample_bytes": 65536,
    "inspect_master_facts": True,
    "fail_closed_unknown": True,
}
patched = module.apply(base, options)
assert "NIAKVIO_HLS_TS_WRAPPED_AAC_RENDITION_V20" in patched
assert module.apply(patched, options) == patched, "HLS managed Lego must reach fixed point"
assert "function tsElementaryProof(bytes)" in patched
assert "aac_ts_audio_unverified" in patched
assert "audioPresent===true" in patched

runtime = r"""
const assert=require('node:assert/strict');
globalThis.__native_fetch=function(){}; // same native HLS probe selection as official TV
function packet(pid,pusi,payload){
 const b=new Uint8Array(188);b.fill(0xff);
 b[0]=0x47;b[1]=(pusi?0x40:0)|((pid>>8)&0x1f);
 b[2]=pid&0xff;b[3]=0x10;
 let p=4;if(pusi)b[p++]=0;
 for(let i=0;i<payload.length&&p<188;i++)b[p++]=payload[i];
 return b;
}
const pat=Uint8Array.from([
 0x00,0xb0,0x0d,0x00,0x01,0xc1,0x00,0x00,
 0x00,0x01,0xe1,0x00,0,0,0,0
]);
function transport(types){
 const es=types.flatMap((type,i)=>[type,0xe1,0x01+i,0xf0,0x00]);
 const length=0x12+5*(types.length-1);
 const pmt=Uint8Array.from([
 0x02,0xb0,length,0x00,0x01,0xc1,0x00,0x00,
 0xe1,0x01,0xf0,0x00,...es,0,0,0,0
 ]);
 const a=packet(0,true,pat),b=packet(0x100,true,pmt);
 const ts=new Uint8Array(376);ts.set(a,0);ts.set(b,188);
 return ts;
}
const videoTs=transport([0x1b,0x0f]);  // video and audio PMT
const audioTs=transport([0x0f]);       // separate audio-only PMT, MPEG-TS bytes
const videoOnlyTs=transport([0x1b]);   // invalid .aac: video but no audio
const syncOnlyTs=new Uint8Array(376);syncOnlyTs[0]=0x47;syncOnlyTs[188]=0x47;
const rawAdts=Uint8Array.from([0xff,0xf1,0x50,0x80,0x00,0x1f,0xfc,0x11,0x22]);
const master=[
 '#EXTM3U','#EXT-X-VERSION:6',
 '#EXT-X-MEDIA:TYPE=AUDIO,GROUP-ID="aud",NAME="Français",LANGUAGE="fr",DEFAULT=YES,URI="fr.m3u8"',
 '#EXT-X-MEDIA:TYPE=AUDIO,GROUP-ID="aud",NAME="English",LANGUAGE="en",DEFAULT=NO,URI="en.m3u8"',
 '#EXT-X-STREAM-INF:BANDWIDTH=4800000,RESOLUTION=1920x1080,CODECS="avc1.640028,mp4a.40.2",AUDIO="aud"',
 'video.m3u8',''
].join('\n');
const videoMedia=[
 '#EXTM3U','#EXT-X-VERSION:6','#EXT-X-TARGETDURATION:300',
 '#EXTINF:300,','video-000.ts','#EXTINF:300,','video-001.ts',
 '#EXT-X-ENDLIST',''
].join('\n');
function audioMedia(lang){
 return [
 '#EXTM3U','#EXT-X-VERSION:6','#EXT-X-TARGETDURATION:300',
 '#EXTINF:300,',lang+'-000.aac','#EXTINF:300,',lang+'-001.aac',
 '#EXT-X-ENDLIST',''
 ].join('\n');
}
let mode='ts-audio',calls=[];
function response(url,ct,text,bytes){
 return {ok:true,status:bytes?206:200,url,
  headers:{get:()=>ct},
  text:async()=>text||'',
  arrayBuffer:async()=>{
   const b=bytes||new Uint8Array(0);
   return b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength);
  }
 };
}
globalThis.fetch=async function(url,init){
 const u=String(url);calls.push({url:u,headers:{...(init&&init.headers||{})}});
 if(u.endsWith('master.m3u8'))return response(u,'application/vnd.apple.mpegurl',master);
 if(u.endsWith('video.m3u8'))return response(u,'application/vnd.apple.mpegurl',videoMedia);
 if(/\/(?:fr|en)\.m3u8$/.test(u))return response(u,'application/vnd.apple.mpegurl',
    audioMedia(u.endsWith('/fr.m3u8')?'fr':'en'));
 if(/\/video-00[01]\.ts$/.test(u))return response(u,'video/mp2t','',videoTs);
 if(/\/(?:fr|en)-00[01]\.aac$/.test(u)){
  const bytes=mode==='ts-audio'?audioTs:
    mode==='adts'?rawAdts:
    mode==='video-only'?videoOnlyTs:
    mode==='sync-only'?syncOnlyTs:
    new TextEncoder().encode('<!doctype html><html>blocked</html>');
  return response(u,mode==='html'?'text/html':'audio/aac','',bytes);
 }
 throw Error('unexpected request category: '+u.replace(/^https?:\/\/[^/]+/,'[HOST]'));
};
PATCHED
(async()=>{
 for(const candidate of ['ts-audio','adts','video-only','sync-only','html']){
  mode=candidate;calls=[];
  const rows=await globalThis.getStreams('157336','movie');
  const accepted=candidate==='ts-audio'||candidate==='adts';
  assert.equal(rows.length,accepted?1:0,candidate+' returned wrong row count');
  assert.equal(calls.filter(x=>/video-00[01]\.ts$/.test(x.url)).length,2,
    'must validate video transport before rendition: '+candidate);
  if(accepted){
   assert.equal(rows[0].url,'https://fixture.invalid/master.m3u8');
   assert.equal(rows[0].headers.Referer,'https://fixture.invalid/title');
   assert.equal(calls.filter(x=>/\/(?:fr|en)-00[01]\.aac$/.test(x.url)).length,4,
      'must prove both French and English audio renditions');
   assert.ok(!JSON.stringify(rows).includes('__nuvioCoreMediaProofV1'),
     'do not expose temporary signed master proof');
  }
 }
 console.log('FIELD_HLS_TS_WRAPPED_AAC_V20 real_ts_audio=true adts=true video_only_rejected=true sync_only_rejected=true html_rejected=true two_languages_probed=true');
})().catch(e=>{console.error(e);process.exit(1)});
"""
with tempfile.NamedTemporaryFile("w", suffix=".cjs", encoding="utf-8", delete=False) as f:
    f.write(runtime.replace("PATCHED", patched))
    script = Path(f.name)
try:
    result = subprocess.run(
        ["node", str(script)], cwd=ROOT, capture_output=True, text=True, timeout=20,
    )
    assert result.returncode == 0, result.stdout + "\n" + result.stderr
    assert "FIELD_HLS_TS_WRAPPED_AAC_V20" in result.stdout, result.stdout
    print(result.stdout.strip())
finally:
    script.unlink(missing_ok=True)
