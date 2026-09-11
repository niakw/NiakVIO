#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
PATCH = SCRIPTS / "provider_patches/coflix_rest_runtime_v1.py"
spec = importlib.util.spec_from_file_location("coflix_rest_runtime_v1", PATCH)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

BASE = 'async function getStreams(){return [{url:"https://legacy.invalid"}]}; if(typeof module!=="undefined")module.exports={getStreams};\n'
out = module.apply(BASE)
assert module.apply(out) == out
assert "NIAKVIO_COFLIX_REST_RUNTIME_V1" in out
assert "master.m3u8?t=" not in out

harness = out + r'''
;(async()=>{
  let calls=[];
  globalThis.fetch=async function(url,opts){
    url=String(url);calls.push(url);
    if(url.includes('/wp-json/coflix/v1/resolve?')){
      const q=new URL(url).searchParams;
      const type=q.get('type');
      if(type==='tv' && q.get('tmdb')==='95479') return {ok:true,status:200,url,headers:{get:()=> 'application/json'},json:async()=>({ok:true,mode:'iframe',servers:[{i:0,direct:false}]})};
      return {ok:true,status:200,url,headers:{get:()=> 'application/json'},json:async()=>({ok:true,mode:'direct',host:'Vidzy',lang:'VF',type:'hls',play:'https://u.test/master.m3u8',servers:[{i:0,direct:true}]})};
    }
    if(url==='https://u.test/master.m3u8') return {ok:true,status:200,url,headers:{get:()=> 'application/vnd.apple.mpegurl'},text:async()=> '#EXTM3U\n#EXT-X-STREAM-INF:BANDWIDTH=1,RESOLUTION=1920x1080\nchild.m3u8\n'};
    return {ok:false,status:404,url,headers:{get:()=> 'text/plain'},text:async()=> 'not found'};
  };
  globalThis.__nuvioMediaContext={canonicalMediaType:'movie',tmdbId:'157336'};
  let rows=await module.exports.getStreams('157336','movie');
  if(rows.length!==1||rows[0].url!=='https://u.test/master.m3u8'||rows[0].quality!=='1080p')throw new Error('movie resolver failed');
  if(!calls.some(x=>x.includes('tmdb=157336')&&x.includes('type=movie')))throw new Error('movie query missing');
  calls=[];globalThis.__nuvioMediaContext={canonicalMediaType:'tv',tmdbId:'1396',season:1,episode:1};
  rows=await module.exports.getStreams('1396','tv',1,1);
  if(rows.length!==1||!calls.some(x=>x.includes('season=1')&&x.includes('episode=1')))throw new Error('tv resolver failed');
  calls=[];globalThis.__nuvioMediaContext={canonicalMediaType:'tv',tmdbId:'1396'};
  rows=await module.exports.getStreams('1396','tv');if(rows.length!==0||calls.length!==0)throw new Error('tv missing episode must fail before network');
  calls=[];globalThis.__nuvioMediaContext={canonicalMediaType:'movie',tmdbId:'tt0816692'};
  rows=await module.exports.getStreams('tt0816692','movie');if(rows.length!==0||calls.length!==0)throw new Error('IMDb must fail before network');
  calls=[];globalThis.__nuvioMediaContext={canonicalMediaType:'anime',tmdbId:'95479',season:1,episode:1};
  rows=await module.exports.getStreams('95479','tv',1,1);if(rows.length!==0)throw new Error('iframe-only anime must fail closed');
  console.log('COFLIX_REST_RUNTIME_V1_OK movie=1 tv=1 raw_tmdb=1 imdb_network=0 missing_episode_network=0 iframe_fail_closed=1 signed_persisted=0');
})().catch(e=>{console.error(e);process.exit(1)});
'''

with tempfile.TemporaryDirectory() as td:
    path = Path(td) / "coflix-test.cjs"
    path.write_text(harness, encoding="utf-8")
    result = subprocess.run(["node", str(path)], cwd=ROOT, text=True, capture_output=True)
    if result.returncode:
        raise AssertionError(result.stdout + result.stderr)
    assert "COFLIX_REST_RUNTIME_V1_OK" in result.stdout
    print(result.stdout.strip())
