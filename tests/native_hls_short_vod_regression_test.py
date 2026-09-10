#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
PATCH = ROOT / "scripts/provider_patches/hls_runtime_integrity_v1.py"

spec = importlib.util.spec_from_file_location("hls_runtime_integrity", PATCH)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

base = r'''globalThis.getStreams=async function(){
 return [{url:"https://media.example/media.m3u8",type:"hls",headers:{Referer:"https://player.example/watch",Origin:"https://player.example"}}];
};'''
patched = module.apply(base, {"timeout_ms": 2000})
assert '"probeFirstSegmentNative":true' in patched
assert '"minimumVodDurationSeconds":90' in patched
assert '"implementationRevision":"native-vod-duration-proof-v9"' in patched


def run_node(source: str) -> None:
    with tempfile.NamedTemporaryFile('w', suffix='.cjs', encoding='utf-8', delete=False) as handle:
        handle.write(source)
        path = Path(handle.name)
    try:
        proc = subprocess.run(['node', str(path)], cwd=ROOT, text=True, capture_output=True, timeout=20)
        assert proc.returncode == 0, proc.stdout + proc.stderr
    finally:
        path.unlink(missing_ok=True)

# 23-second finite VOD: structurally valid HLS, functionally a preview/decoy.
run_node(r'''
const assert=require('assert');
let calls=0;
globalThis.__native_fetch=function(){};
globalThis.fetch=async function(url){
 calls++;
 if(url.endsWith('media.m3u8'))return {ok:true,status:200,url,headers:{get:()=> 'application/vnd.apple.mpegurl'},text:async()=> '#EXTM3U\n#EXT-X-TARGETDURATION:13\n#EXTINF:10,\na.ts\n#EXTINF:13,\nb.ts\n#EXT-X-ENDLIST\n'};
 throw new Error('short finite VOD must stop before segment fetch');
};
PATCHED
(async()=>{const rows=await globalThis.getStreams('1','movie');assert.equal(rows.length,0,JSON.stringify(rows));assert.equal(calls,1,'short VOD should stop after playlist proof')})().catch(e=>{console.error(e);process.exit(1)});
'''.replace('PATCHED', patched))

# 120-second finite VOD remains valid and receives a bounded first-segment probe.
run_node(r'''
const assert=require('assert');
let calls=0;
globalThis.__native_fetch=function(){};
function response(url,contentType,text,bytes){return {ok:true,status:200,url,headers:{get:n=>String(n).toLowerCase()==='content-type'?contentType:''},text:async()=>text||'',arrayBuffer:async()=>{const b=bytes||new Uint8Array(0);return b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength)}}}
const ts=new Uint8Array(376);ts[0]=0x47;ts[188]=0x47;
globalThis.fetch=async function(url){
 calls++;
 if(url.endsWith('media.m3u8'))return response(url,'application/vnd.apple.mpegurl','#EXTM3U\n#EXT-X-TARGETDURATION:60\n#EXTINF:60,\na.ts\n#EXTINF:60,\nb.ts\n#EXT-X-ENDLIST\n');
 if(url.endsWith('a.ts'))return response(url,'video/mp2t','',ts);
 throw new Error('unexpected '+url);
};
PATCHED
(async()=>{const rows=await globalThis.getStreams('1','movie');assert.equal(rows.length,1,JSON.stringify(rows));assert.equal(calls,2,'full VOD should probe playlist + first segment')})().catch(e=>{console.error(e);process.exit(1)});
'''.replace('PATCHED', patched))

print('native HLS rejects 23-second finite VOD and preserves 120-second VOD')
