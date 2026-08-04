#!/usr/bin/env python3
from __future__ import annotations
import importlib.util
import json
import subprocess
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
patch_path=ROOT/'scripts/provider_patches/stream_output_sanitizer.py'
spec=importlib.util.spec_from_file_location('stream_output_sanitizer',patch_path)
mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)

base='module.exports={getStreams:async()=>[{url:"https://s1.fsvid.lol/troll/master.m3u8",type:"hls"},{url:"https://media.example/long.m3u8",type:"hls"}]};'
patched=mod.apply(base,options={
    'blocked_hosts':['fstream.top'],
    'blocked_path_patterns':['/troll/'],
    'probe_direct_media':True,
    'min_vod_duration_seconds':60,
    'max_probes':6,
})
assert 'NUVIO_STREAM_OUTPUT_SANITIZER_V4' in patched

runner=r'''
const vm=require('vm');
const source=process.argv[2];
function response(url,text){
  const bytes=new TextEncoder().encode(text);
  return {ok:true,status:200,url,headers:{get:(k)=>k.toLowerCase()==='content-type'?'application/vnd.apple.mpegurl':''},body:null,arrayBuffer:async()=>bytes.buffer};
}
const short='#EXTM3U\n#EXT-X-TARGETDURATION:3\n#EXTINF:2.0,\na.ts\n#EXTINF:2.0,\nb.ts\n#EXT-X-ENDLIST\n';
const long='#EXTM3U\n#EXT-X-TARGETDURATION:10\n'+Array.from({length:7},(_,i)=>`#EXTINF:10.0,\n${i}.ts\n`).join('')+'#EXT-X-ENDLIST\n';
const sandbox={module:{exports:{}},exports:{},URL,AbortController,TextEncoder,Uint8Array,setTimeout,clearTimeout,fetch:async(url)=>response(String(url),String(url).includes('long')?long:short)};
sandbox.globalThis=sandbox;
vm.runInNewContext(source,sandbox,{timeout:5000});
Promise.resolve(sandbox.module.exports.getStreams()).then(result=>{console.log(JSON.stringify(result));}).catch(error=>{console.error(error);process.exit(1)});
'''
with tempfile.TemporaryDirectory() as tmp:
    js=Path(tmp)/'runner.cjs'; js.write_text(runner)
    proc=subprocess.run(['node',str(js),patched],capture_output=True,text=True,timeout=20)
    assert proc.returncode==0,proc.stderr
    result=json.loads(proc.stdout.strip().splitlines()[-1])
    assert [row['url'] for row in result]==['https://media.example/long.m3u8'],result
print('short HLS preview guard tests passed')
