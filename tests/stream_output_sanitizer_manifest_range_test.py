#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
PATCH = ROOT / "scripts/provider_patches/stream_output_sanitizer_v9.py"

spec = importlib.util.spec_from_file_location("stream_output_sanitizer_v9_test", PATCH)
assert spec is not None and spec.loader is not None
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

BASE = '"use strict";\nglobalThis.getStreams=async()=>globalThis.__rows;\n'
OPTIONS = {
    "probe_direct_media": True,
    "probe_all_urls": True,
    "max_probes": 4,
    "probe_timeout_ms": 1200,
    "min_vod_duration_seconds": 60,
}

provider = mod.apply(BASE, options=OPTIONS)
assert mod.apply(provider, options=OPTIONS) == provider
assert "NUVIO_STREAM_OUTPUT_FULL_MANIFEST_V9" in provider
assert 'return verdict===true?clearPrivateProofs(item.stream):null;' in provider
assert 'status===403||status===404||status===410' in provider

NODE = r'''
const provider=process.argv[2];
const mode=process.argv[3];
function hdrs(ct){return {get:(k)=>String(k).toLowerCase()==='content-type'?ct:''};}
const full=`#EXTM3U
#EXT-X-VERSION:6
#EXT-X-STREAM-INF:BANDWIDTH=2500000,RESOLUTION=1920x1080
1080/index.m3u8
`;
const truncated=`#EXTM3U
#EXT-X-VERSION:6
#EXT-X-STREAM-INF:BANDWIDTH=2500000,RESOLUTION=1920x1080
`;
function response(url,status,body,ct='application/vnd.apple.mpegurl'){
  const bytes=Buffer.from(body||'');
  return {ok:status>=200&&status<300,status,url,headers:hdrs(ct),arrayBuffer:async()=>bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength)};
}
globalThis.__rows=[{url:'https://cdn.example/master.m3u8',name:'Fixture',quality:'1080p'}];
globalThis.fetch=async(url,opts={})=>{
  url=String(url); const headers=opts.headers||{};
  const range=Object.keys(headers).some(k=>String(k).toLowerCase()==='range');
  if(mode==='valid'){
    if(range)return response(url,206,truncated);
    return response(url,200,full);
  }
  if(mode==='403')return response(url,403,'denied','text/html');
  throw new Error('unknown mode '+mode);
};
require(provider);
(async()=>{
  const out=await globalThis.getStreams();
  if(mode==='valid'){
    if(!Array.isArray(out)||out.length!==1)throw new Error('valid full HLS was rejected '+JSON.stringify(out));
    console.log('SANITIZER_V9_FULL_HLS_OK');
  }else{
    if(!Array.isArray(out)||out.length!==0)throw new Error('403 stream survived '+JSON.stringify(out));
    console.log('SANITIZER_V9_403_FAIL_CLOSED_OK');
  }
})().catch(e=>{console.error(e);process.exit(1)});
'''

with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    provider_path = tmp / "provider.cjs"
    runner = tmp / "runner.cjs"
    provider_path.write_text(provider, encoding="utf-8")
    runner.write_text(NODE, encoding="utf-8")
    for mode, marker in (
        ("valid", "SANITIZER_V9_FULL_HLS_OK"),
        ("403", "SANITIZER_V9_403_FAIL_CLOSED_OK"),
    ):
        proc = subprocess.run(
            ["node", str(runner), str(provider_path), mode],
            cwd=ROOT, capture_output=True, text=True, timeout=8, check=False,
        )
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert marker in proc.stdout, proc.stdout

print("stream sanitizer v9 full-manifest + strict-403 tests passed")
