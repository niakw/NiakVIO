#!/usr/bin/env python3
from pathlib import Path
import json, subprocess, tempfile, sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from apply_provider_overrides import apply_overrides

source=b'''var __provider={getStreams:async function(){return [
 {name:"Movie 1080p Dual-Audio",title:"VFF + VO",url:"https://cdn.example/video.m3u8",headers:{}},
 {name:"bad",url:"https://cdn.example/file.avi"},
 {name:"dup",url:"https://cdn.example/video.m3u8"}
]}};
if (typeof module !== 'undefined' && module.exports) { module.exports = __provider; }
if (__provider && __provider.getStreams) { globalThis.getStreams=__provider.getStreams; }
'''
patched, records=apply_overrides('synthetic',source)
text=patched.decode()
assert 'NUVIO_GLOBAL_STREAM_OUTPUT_GUARD_V1' in text
assert any(x.get('type')=='global_stream_output_guard' for x in records)
with tempfile.TemporaryDirectory() as td:
 p=Path(td)/'provider.js'; p.write_text(text)
 js=f'''const p=require({json.dumps(str(p))}); p.getStreams().then(x=>{{console.log(JSON.stringify(x));}});'''
 out=subprocess.check_output(['node','-e',js],text=True)
 streams=json.loads(out.strip())
 assert len(streams)==1, streams
 s=streams[0]
 assert s['quality']=='1080p', s
 assert s['language']=='MULTI', s
 assert s['headers']['Range']=='bytes=0-', s
 assert s['headers']['Accept']=='*/*', s
 assert s['headers']['User-Agent'], s
print('global stream output guard test passed')
