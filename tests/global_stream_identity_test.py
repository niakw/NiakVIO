#!/usr/bin/env python3
from __future__ import annotations
import importlib.util
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
 {name:'Server 4',title:'Ryomen Sukuna S01E01',url:'https://cdn.example/Ryomen-Sukuna-S01E01.mp4'},
 {name:'Server 5',url:'https://cdn.example/opaque-93af1.m3u8'}
]}};'''

patched = identity.apply(base, context={"provider_id": "example"})
assert "NUVIO_GLOBAL_STREAM_IDENTITY_V1" in patched
assert "cross-client-positive-mismatch-anime-confirmed-v3" in patched
assert identity.apply(patched, context={"provider_id": "example"}) == patched

# The final Core presentation composes facts + identity before presentation, so
# every provider rebuilt for TV/Mobile/Desktop receives the same identity guard.
finalized = presentation.apply(base, context={"provider_id": "example"})
assert "NUVIO_GLOBAL_STREAM_FACTS_V1" in finalized
assert "NUVIO_GLOBAL_STREAM_IDENTITY_V1" in finalized
assert "NUVIO_GLOBAL_STREAM_PRESENTATION_V1" in finalized
assert finalized.index("NUVIO_GLOBAL_STREAM_FACTS_V1") < finalized.index("NUVIO_GLOBAL_STREAM_IDENTITY_V1")
assert finalized.index("NUVIO_GLOBAL_STREAM_IDENTITY_V1") < finalized.index("NUVIO_GLOBAL_STREAM_PRESENTATION_V1")

runner = r'''
const assert=require('assert');
const searches=[];
function response(data){return {ok:true,status:200,json:async()=>data};}
global.fetch=async function(raw){
  const url=String(raw);
  if(url.includes('/tv/95479/season/1/episode/1?')){
    return response({id:1,name:'Ryomen Sukuna'});
  }
  if(url.includes('/tv/95479?')){
    return response({id:95479,name:'Jujutsu Kaisen',original_name:'呪術廻戦',first_air_date:'2020-10-03',external_ids:{imdb_id:'tt12343534'}});
  }
  if(url.includes('/search/tv?')){
    const q=new URL(url).searchParams.get('query')||'';
    searches.push(q);
    if(q.toLowerCase().includes('naruto')&&q.toLowerCase().includes('shippuden')){
      return response({results:[{id:31910,name:'Naruto Shippuden',original_name:'Naruto: Shippûden',first_air_date:'2007-02-15'}]});
    }
    return response({results:[]});
  }
  throw new Error('unexpected fetch '+url);
};
PATCHED
(async()=>{
  const expected=[
    'https://cdn.example/Jujutsu-Kaisen-S01E01.mp4',
    'https://cdn.example/Ryomen-Sukuna-S01E01.mp4',
    'https://cdn.example/opaque-93af1.m3u8'
  ];
  // Desktop/Mobile object-shaped request.
  for (const mediaType of ['anime','tv']) {
    const rows=await module.exports.getStreams({tmdbId:'95479',imdbId:'tt12343534',mediaType,title:'Jujutsu Kaisen',year:2020,season:1,episode:1});
    assert.deepEqual(rows.map(x=>x.url),expected,mediaType+':object:'+JSON.stringify(rows));
  }
  // NuvioTV historically invokes providers positionally. The same wrong-anime row
  // must be rejected even though title/year are absent from the direct call; TMDB
  // identity enrichment supplies them and keeps TV/Desktop behavior aligned.
  const tvRows=await module.exports.getStreams('95479','anime',1,1);
  assert.deepEqual(tvRows.map(x=>x.url),expected,'anime:positional:'+JSON.stringify(tvRows));
  assert(searches.filter(q=>q.toLowerCase().includes('naruto')).length>=3,JSON.stringify(searches));
  console.log(JSON.stringify({searches}));
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

# Explicit media IDs are the strongest positive contradiction and do not depend on
# title heuristics. Opaque stream with another TMDB id is rejected; opaque stream
# without identity evidence is retained.
id_source = "module.exports={getStreams:async()=>[{url:'https://cdn.example/a.m3u8',tmdbId:'999999'},{url:'https://cdn.example/b.m3u8'}]};"
id_patched = identity.apply(id_source, context={"provider_id": "example"})
id_runner = r'''
global.fetch=async raw=>{const u=String(raw);if(u.includes('/movie/157336?'))return {ok:true,json:async()=>({id:157336,title:'Interstellar',original_title:'Interstellar',release_date:'2014-11-05'})};return {ok:true,json:async()=>({results:[]})}};
PATCHED
module.exports.getStreams({tmdbId:'157336',mediaType:'movie',title:'Interstellar',year:2014}).then(rows=>{if(rows.length!==1||!rows[0].url.endsWith('/b.m3u8'))process.exit(2)}).catch(()=>process.exit(3));
'''.replace('PATCHED', id_patched)
with tempfile.NamedTemporaryFile('w', suffix='.cjs', encoding='utf-8', delete=False) as handle:
    handle.write(id_runner)
    id_path = Path(handle.name)
try:
    proc = subprocess.run(['node', str(id_path)], cwd=ROOT, text=True, capture_output=True, timeout=20)
    assert proc.returncode == 0, proc.stdout + proc.stderr
finally:
    id_path.unlink(missing_ok=True)

# Film request must reject an explicit episodic filename, while generic opaque
# media remains because the guard is positive-mismatch-only, not guesswork.
movie_source = "module.exports={getStreams:async()=>[{url:'https://cdn.example/Other-Show-S02E04.mp4'},{name:'Server 1',url:'https://cdn.example/a8f.m3u8'}]};"
movie_patched = identity.apply(movie_source, context={"provider_id": "example"})
movie_runner = r'''
global.fetch=async raw=>{const u=String(raw);if(u.includes('/movie/157336?'))return {ok:true,json:async()=>({id:157336,title:'Interstellar',original_title:'Interstellar',release_date:'2014-11-05'})};return {ok:true,json:async()=>({results:[]})}};
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

print('global stream identity TV/anime dual-route regression tests passed')
