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
PATCH = SCRIPTS / "provider_patches/voiranime_homes_runtime_v1.py"
spec = importlib.util.spec_from_file_location("voiranime_homes_runtime_v1", PATCH)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

BASE = 'async function getStreams(){return [{url:"https://legacy.invalid"}]}; if(typeof module!=="undefined")module.exports={getStreams};\n'
out = module.apply(BASE)
assert module.apply(out) == out
assert "NIAKVIO_VOIRANIME_HOMES_RUNTIME_V1" in out
assert "embed-wojoffwz42ri" not in out
assert "master.m3u8?t=" not in out

harness = out + r'''
;(async()=>{
  let calls=[];
  globalThis.fetch=async function(url,opts){
    url=String(url);calls.push({url,opts:opts||{}});
    if(url==='https://voiranime.homes/engine/ajax/search.php'){
      const body=String((opts||{}).body||'');if(!body.includes('query=Jujutsu%20Kaisen'))throw new Error('wrong search body');
      return {ok:true,status:200,url,headers:{get:()=> 'text/html'},text:async()=> `<div class='search-item' onclick="location.href='/1498036-jujutsu-kaisen-saison-2-2023.html'"><div class='search-content'><h3 class='search-title'>Jujutsu Kaisen - Saison 2</h3></div></div><div class='search-item' onclick="location.href='/1497198-jujutsu-kaisen-saison-1-2020.html'"><div class='search-content'><h3 class='search-title'>Jujutsu Kaisen - Saison 1</h3></div></div>`};
    }
    if(url==='https://voiranime.homes/engine/ajax/manga_episodes_api.php?id=1497198') return {ok:true,status:200,url,headers:{get:()=> 'application/json'},text:async()=> JSON.stringify({vf:{'1':{vidzy:'https://vidzy.test/embed-a.html',luluvid:'https://lulu.test/e/a'}},vostfr:{'1':{vidzy:'https://vidzy.test/embed-b.html'}},info:{'1':{title:'Ryomen Sukuna'}}})};
    if(url==='https://vidzy.test/embed-a.html') return {ok:true,status:200,url,headers:{get:()=> 'text/html'},text:async()=> `<script>var x="https:\/\/s1.test\/vf\/master.m3u8?token=runtime";</script>`};
    if(url==='https://vidzy.test/embed-b.html') return {ok:true,status:200,url,headers:{get:()=> 'text/html'},text:async()=> `<script>var x="https:\/\/s1.test\/sub\/master.m3u8";</script>`};
    if(url==='https://lulu.test/e/a') return {ok:true,status:200,url,headers:{get:()=> 'text/html'},text:async()=> '<html>no direct media</html>'};
    if(url.startsWith('https://s1.test/')) return {ok:true,status:200,url,headers:{get:()=> 'application/vnd.apple.mpegurl'},text:async()=> '#EXTM3U\n#EXT-X-STREAM-INF:BANDWIDTH=1,RESOLUTION=1280x720\nchild.m3u8\n'};
    return {ok:false,status:404,url,headers:{get:()=> 'text/plain'},text:async()=> 'no'};
  };
  globalThis.__nuvioMediaContext={canonicalMediaType:'anime',tmdbId:'95479',season:1,episode:1,tmdbMetadata:{name:'Jujutsu Kaisen'}};
  let rows=await module.exports.getStreams('95479','tv',1,1);
  if(rows.length!==2)throw new Error('expected VF + VOSTFR direct HLS, got '+rows.length);
  if(!rows.some(x=>x.language==='VF'&&x.url.includes('/vf/master.m3u8')))throw new Error('missing VF');
  if(!rows.some(x=>x.language==='VOSTFR'&&x.url.includes('/sub/master.m3u8')))throw new Error('missing VOSTFR');
  if(!calls.some(x=>x.url.endsWith('id=1497198')))throw new Error('season-aware provider id selection failed');
  calls=[];globalThis.__nuvioMediaContext={canonicalMediaType:'tv',tmdbId:'1396',season:1,episode:1,tmdbMetadata:{name:'Breaking Bad'}};
  rows=await module.exports.getStreams('1396','tv',1,1);if(rows.length!==0||calls.length!==0)throw new Error('non-anime must fail before network');
  calls=[];globalThis.__nuvioMediaContext={canonicalMediaType:'anime',tmdbId:'95479',season:1,episode:1,tmdbMetadata:{}};
  rows=await module.exports.getStreams('95479','tv',1,1);if(rows.length!==0||calls.length!==0)throw new Error('missing title must fail before network');
  calls=[];globalThis.__nuvioMediaContext={canonicalMediaType:'anime',tmdbId:'95479',tmdbMetadata:{name:'Jujutsu Kaisen'}};
  rows=await module.exports.getStreams('95479','movie');if(rows.length!==0||calls.length!==0)throw new Error('unproved anime-movie lane must fail before network');
  console.log('VOIRANIME_HOMES_RUNTIME_V1_OK vf=1 vostfr=1 season_id=1497198 canonical_gate_network=0 movie_debt_fail_closed=1 signed_persisted=0');
})().catch(e=>{console.error(e);process.exit(1)});
'''

with tempfile.TemporaryDirectory() as td:
    path = Path(td) / "voiranime-test.cjs"
    path.write_text(harness, encoding="utf-8")
    result = subprocess.run(["node", str(path)], cwd=ROOT, text=True, capture_output=True)
    if result.returncode:
        raise AssertionError(result.stdout + result.stderr)
    assert "VOIRANIME_HOMES_RUNTIME_V1_OK" in result.stdout
    print(result.stdout.strip())
