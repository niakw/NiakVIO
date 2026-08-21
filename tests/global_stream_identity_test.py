#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / "scripts/provider_patches/global_stream_identity_v1.py"
PRESENTATION = ROOT / "scripts/provider_patches/global_stream_presentation_v1.py"

spec = importlib.util.spec_from_file_location("global_stream_identity", PATCH)
assert spec and spec.loader
identity = importlib.util.module_from_spec(spec)
spec.loader.exec_module(identity)

pspec = importlib.util.spec_from_file_location("global_stream_presentation", PRESENTATION)
assert pspec and pspec.loader
presentation = importlib.util.module_from_spec(pspec)
pspec.loader.exec_module(presentation)

base = r'''module.exports={getStreams:async function(){return [
 {name:'Server 1',title:'Jujutsu Kaisen S01E01',url:'https://cdn.example/Jujutsu-Kaisen-S01E01.mp4'},
 {name:'Server 2',title:'Naruto Shippuden S01E01',url:'https://cdn.example/Naruto-Shippuden-S01E01.mp4'},
 {name:'Server 3',title:'Jujutsu Kaisen S01E02',url:'https://cdn.example/Jujutsu-Kaisen-S01E02.mp4'},
 {name:'Server 4',url:'https://cdn.example/opaque-93af1.m3u8'}
]}};'''

patched = identity.apply(base, context={"provider_id": "example"})
assert "NUVIO_GLOBAL_STREAM_IDENTITY_V1" in patched
assert identity.apply(patched, context={"provider_id": "example"}) == patched

# The final Core presentation composes identity first, so every provider rebuilt
# through the global presentation hook gets the same TV/Mobile/Desktop filtering.
finalized = presentation.apply(base, context={"provider_id": "example"})
assert "NUVIO_GLOBAL_STREAM_IDENTITY_V1" in finalized
assert "NUVIO_GLOBAL_STREAM_PRESENTATION_V1" in finalized
assert finalized.index("NUVIO_GLOBAL_STREAM_IDENTITY_V1") < finalized.index("NUVIO_GLOBAL_STREAM_PRESENTATION_V1")

runner = r'''
const assert=require('assert');
global.fetch=async function(url){
  url=String(url);
  if(!url.includes('api.themoviedb.org/3/tv/95479')) throw new Error('unexpected fetch '+url);
  return {ok:true,status:200,json:async()=>({id:95479,name:'Jujutsu Kaisen',original_name:'呪術廻戦',first_air_date:'2020-10-03'})};
};
PATCHED
(async()=>{
  const rows=await module.exports.getStreams({tmdbId:'95479',mediaType:'anime',title:'Jujutsu Kaisen',year:2020,season:1,episode:1});
  assert.deepEqual(rows.map(x=>x.url),[
    'https://cdn.example/Jujutsu-Kaisen-S01E01.mp4',
    'https://cdn.example/opaque-93af1.m3u8'
  ],JSON.stringify(rows));
  console.log(JSON.stringify(rows));
})().catch(e=>{console.error(e);process.exit(1)});
'''.replace('PATCHED', patched)

with tempfile.NamedTemporaryFile('w', suffix='.cjs', encoding='utf-8', delete=False) as handle:
    handle.write(runner)
    path = Path(handle.name)
try:
    proc = subprocess.run(['node', str(path)], cwd=ROOT, text=True, capture_output=True, timeout=20)
    assert proc.returncode == 0, proc.stdout + proc.stderr
finally:
    path.unlink(missing_ok=True)

# Film request must reject an explicit episodic filename, while generic opaque
# media is retained because the guard is positive-mismatch-only, not guesswork.
movie_source = "module.exports={getStreams:async()=>[{url:'https://cdn.example/Other-Show-S02E04.mp4'},{name:'Server 1',url:'https://cdn.example/a8f.m3u8'}]};"
movie_patched = identity.apply(movie_source, context={"provider_id": "example"})
movie_runner = r'''
global.fetch=async()=>({ok:true,json:async()=>({id:157336,title:'Interstellar',original_title:'Interstellar',release_date:'2014-11-05'})});
PATCHED
module.exports.getStreams({tmdbId:'157336',mediaType:'movie',title:'Interstellar',year:2014}).then(rows=>{if(rows.length!==1||!rows[0].url.endsWith('/a8f.m3u8'))process.exit(2)}).catch(()=>process.exit(3));
'''.replace('PATCHED', movie_patched)
with tempfile.NamedTemporaryFile('w', suffix='.cjs', encoding='utf-8', delete=False) as handle:
    handle.write(movie_runner)
    movie_path = Path(handle.name)
try:
    proc = subprocess.run(['node', str(movie_path)], cwd=ROOT, text=True, capture_output=True, timeout=20)
    assert proc.returncode == 0, proc.stdout + proc.stderr
finally:
    movie_path.unlink(missing_ok=True)

print('global stream identity tests passed')
