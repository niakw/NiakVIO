#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
PATCH = ROOT / "scripts" / "provider_patches" / "global_media_type_resolution_v1.py"
spec = importlib.util.spec_from_file_location("global_media_type_resolution_v1", PATCH)
assert spec is not None and spec.loader is not None
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

BASE = '''
"use strict";
async function getStreams(tmdbId, mediaType, season, episode) {
  const ctx = globalThis.__nuvioMediaContext || {};
  return [{
    tmdbId, mediaType, season, episode,
    canonicalMediaType: ctx.canonicalMediaType || "",
    providerMediaType: ctx.providerMediaType || mediaType,
    degraded: ctx.tmdbResolutionDegraded === true
  }];
}
module.exports = { getStreams };
'''

ZERO_BASE = '''
"use strict";
async function getStreams() { return []; }
module.exports = { getStreams };
'''


def run_case(source: str, runner: str) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        provider = tmp_path / "provider.cjs"
        test = tmp_path / "test.cjs"
        provider.write_text(source, encoding="utf-8")
        test.write_text(
            "global.TMDB_API_KEY='0123456789abcdef0123456789abcdef';\n" + runner,
            encoding="utf-8",
        )
        result = subprocess.run(["node", str(test), str(provider)], capture_output=True, text=True)
        assert result.returncode == 0, result.stdout + result.stderr


mixed = mod.apply(BASE, options={"semantic_types": ["tv", "anime"]})
assert "api.themoviedb.org/3/" in mixed
assert "www.themoviedb.org/" not in mixed
assert '"tmdbKeyCipher":' not in mixed
assert '"tmdbKeySalt":' not in mixed
assert "function embeddedKey" not in mixed
assert "NiakVIO/TMDB/v1" not in mixed
assert "external_source=imdb_id" in mixed
assert "alternative_titles" in mixed
assert "language=fr-FR" in mixed
assert 'var providerEvent=invocationEvent(originalArgs);' in mixed
assert 'if(providerEvent!=="launch")return [];' in mixed
assert 'if(!hasProviderOutput(value))return [];' in mixed

run_case(mixed, '''
let calls = 0;
global.fetch = async (url) => {
  calls++;
  const value=String(url);
  if (!value.includes("api.themoviedb.org/3/tv/280049")) throw new Error("wrong TMDB endpoint "+value);
  if (!value.includes("api_key=0123456789abcdef0123456789abcdef")) throw new Error("runtime TMDB API key missing");
  return { ok:true, status:200, json:async()=>({
    id:280049, genres:[{id:16,name:"Animation"}], original_language:"ja",
    origin_country:["JP"], keywords:{results:[{name:"anime"}]}
  }) };
};
const provider=require(process.argv[2]);
(async()=>{
  const value=await provider.getStreams("280049","series",1,11);
  if(!Array.isArray(value)||!value.length||value[0].canonicalMediaType!=="anime"||value[0].mediaType!=="tv")
    throw new Error("anime semantic/TV transport split failed: "+JSON.stringify(value));
  const again=await provider.getStreams("280049","series",1,12);
  if(!Array.isArray(again)||!again.length||again[0].canonicalMediaType!=="anime"||again[0].mediaType!=="tv")
    throw new Error("anime cache/transport lost");
  if(calls!==1)throw new Error("TMDB lookup was not cached: "+calls);
})().catch(e=>{console.error(e);process.exit(1)});
''')

run_case(mixed, '''
let calls=0;
global.__nuvioProviderEvent='discovery';
global.fetch=async()=>{calls++;throw new Error('network forbidden')};
const provider=require(process.argv[2]);
(async()=>{
  const value=await provider.getStreams('280049','series',1,1);
  if(!Array.isArray(value)||value.length!==0)throw new Error('non-launch must return []');
  if(calls!==0)throw new Error('non-launch touched network');
})().catch(e=>{console.error(e);process.exit(1)});
''')

deferred_zero = mod.apply(ZERO_BASE, options={"semantic_types": ["movie", "tv"]})
run_case(deferred_zero, '''
let calls=0;
global.fetch=async()=>{calls++;throw new Error('TMDB must not run for zero output')};
const provider=require(process.argv[2]);
(async()=>{
  const value=await provider.getStreams('1396','series',1,1);
  if(!Array.isArray(value)||value.length!==0)throw new Error('zero output changed');
  if(calls!==0)throw new Error('zero output caused TMDB work');
})().catch(e=>{console.error(e);process.exit(1)});
''')

tv_only = mod.apply(BASE, options={"semantic_types": ["tv"]})
run_case(tv_only, '''
let calls=0;
global.fetch=async(url)=>{
  calls++;
  if(!String(url).includes('/tv/1396?'))throw new Error('unexpected TMDB endpoint '+url);
  return{ok:true,status:200,json:async()=>({
    id:1396,genres:[{id:18,name:'Drama'}],original_language:'en',
    origin_country:['US'],keywords:{results:[]}
  })};
};
const provider=require(process.argv[2]);
(async()=>{
  const value=await provider.getStreams('1396','series',1,1);
  if(!Array.isArray(value)||!value.length||value[0].mediaType!=='tv')throw new Error('ordinary TV output rejected');
  if(calls!==1)throw new Error('positive output must be verified exactly once');
})().catch(e=>{console.error(e);process.exit(1)});
''')

run_case(tv_only, '''
global.fetch=async()=>({ok:true,status:200,json:async()=>({
  id:30984,genres:[{id:16,name:'Animation'}],original_language:'ja',
  origin_country:['JP'],keywords:{results:[{name:'anime'}]}
})});
const provider=require(process.argv[2]);
(async()=>{
  const value=await provider.getStreams('30984','series',1,7);
  if(!Array.isArray(value)||value.length!==0)throw new Error('TV-only provider leaked anime');
})().catch(e=>{console.error(e);process.exit(1)});
''')

run_case(tv_only, '''
global.fetch=async()=>{throw new Error('TMDB unavailable')};
const provider=require(process.argv[2]);
(async()=>{
  const value=await provider.getStreams('62425','series',2,1);
  if(!Array.isArray(value)||!value.length||value[0].mediaType!=='tv'||value[0].degraded!==true)
    throw new Error('TV fail-open fallback failed: '+JSON.stringify(value));
})().catch(e=>{console.error(e);process.exit(1)});
''')

print('global media resolver: runtime-only TMDB credentials, launch gate, canonical/transport split and deferred verification passed')
