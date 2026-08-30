#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / "scripts" / "provider_patches" / "global_media_type_resolution_v1.py"
spec = importlib.util.spec_from_file_location("global_media_type_resolution_v1", PATCH)
assert spec is not None and spec.loader is not None
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

BASE = r"""
"use strict";
async function getStreams(tmdbId, mediaType, season, episode) {
  const ctx = globalThis.__nuvioMediaContext || {};
  return [{ tmdbId, mediaType, season, episode, degraded: ctx.tmdbResolutionDegraded === true }];
}
module.exports = { getStreams };
"""

def run_case(source: str, runner: str) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        provider = tmp_path / "provider.cjs"
        test = tmp_path / "test.cjs"
        provider.write_text(source, encoding="utf-8")
        test.write_text(runner, encoding="utf-8")
        result = subprocess.run(["node", str(test), str(provider)], capture_output=True, text=True)
        assert result.returncode == 0, result.stdout + result.stderr

mixed = mod.apply(BASE, options={"semantic_types": ["tv", "anime"]})
assert "api.themoviedb.org/3/" in mixed
assert "www.themoviedb.org/" not in mixed
assert "tmdbKeyCipher" in mixed
assert "external_source=imdb_id" in mixed
assert "alternative_titles" in mixed
assert "language=fr-FR" in mixed

run_case(mixed, r"""
let calls = 0;
global.fetch = async (url) => {
  calls++;
  if (!String(url).includes("api.themoviedb.org/3/tv/280049")) throw new Error("wrong TMDB endpoint "+url);
  if (!String(url).includes("api_key=")) throw new Error("embedded TMDB API key missing");
  return { ok:true, status:200, json:async()=>({
    id:280049, genres:[{id:16,name:"Animation"}], original_language:"ja",
    origin_country:["JP"], keywords:{results:[{name:"anime"}]}
  }) };
};
const provider=require(process.argv[2]);
(async()=>{
  const value=await provider.getStreams("280049","series",1,11);
  if(!value.length||value[0].mediaType!=="anime")throw new Error("Hell Mode was not refined to anime");
  const again=await provider.getStreams("280049","series",1,12);
  if(!again.length||again[0].mediaType!=="anime")throw new Error("anime cache lost");
  if(calls!==1)throw new Error("TMDB lookup was not cached");
})().catch(e=>{console.error(e);process.exit(1)});
""")

tv_only = mod.apply(BASE, options={"semantic_types": ["tv"]})
run_case(tv_only, r"""
global.fetch=async()=>({ok:true,status:200,json:async()=>({
  id:30984,genres:[{id:16,name:"Animation"}],original_language:"ja",
  origin_country:["JP"],keywords:{results:[{name:"anime"}]}
})});
const provider=require(process.argv[2]);
(async()=>{
  const value=await provider.getStreams("30984","series",1,7);
  if(!Array.isArray(value)||value.length!==0)throw new Error("TV-only provider must reject TMDB-proven anime");
})().catch(e=>{console.error(e);process.exit(1)});
""")

anime_only = mod.apply(BASE, options={"semantic_types": ["anime"]})
run_case(anime_only, r"""
global.fetch=async()=>({ok:true,status:200,json:async()=>({
  id:1396,genres:[{id:18,name:"Drama"}],original_language:"en",origin_country:["US"],keywords:{results:[]}
})});
const provider=require(process.argv[2]);
(async()=>{
  const value=await provider.getStreams("1396","series",1,1);
  if(!Array.isArray(value)||value.length!==0)throw new Error("Anime-only provider must reject TMDB-proven ordinary TV");
})().catch(e=>{console.error(e);process.exit(1)});
""")

run_case(tv_only, r"""
global.fetch=async()=>{throw new Error("TMDB unavailable")};
const provider=require(process.argv[2]);
(async()=>{
  const value=await provider.getStreams("62425","series",2,1);
  if(!value.length||value[0].mediaType!=="tv"||value[0].degraded!==true)throw new Error("TV fallback must stay executable on TMDB outage");
})().catch(e=>{console.error(e);process.exit(1)});
""")

run_case(anime_only, r"""
global.fetch=async()=>{throw new Error("TMDB unavailable")};
const provider=require(process.argv[2]);
(async()=>{
  const value=await provider.getStreams("280049","series",1,11);
  if(!value.length||value[0].mediaType!=="anime"||value[0].degraded!==true)throw new Error("Anime provider must fail open on metadata outage");
})().catch(e=>{console.error(e);process.exit(1)});
""")

movie_only = mod.apply(BASE, options={"semantic_types": ["movie"]})
run_case(movie_only, r"""
global.fetch=async()=>{throw new Error("TMDB unavailable")};
const provider=require(process.argv[2]);
(async()=>{
  const value=await provider.getStreams("157336","movie",null,null);
  if(!value.length||value[0].mediaType!=="movie"||value[0].degraded!==true)throw new Error("Movie fallback failed");
})().catch(e=>{console.error(e);process.exit(1)});
""")


# IMDb is normalized by Core before the ProviderBase sees the request.
run_case(mixed, r"""
const calls=[];
global.fetch=async(url)=>{
  url=String(url);calls.push(url);
  if(url.includes('/find/tt0903747?')){
    if(!url.includes('external_source=imdb_id'))throw new Error('IMDb lookup missing external_source');
    return{ok:true,status:200,json:async()=>({
      movie_results:[],
      tv_results:[{id:1396,name:'Breaking Bad',original_name:'Breaking Bad',first_air_date:'2008-01-20'}]
    })};
  }
  if(url.includes('/tv/1396?')){
    if(!url.includes('append_to_response=keywords,alternative_titles,external_ids'))throw new Error('full TMDB enrichment missing');
    if(!url.includes('language=fr-FR'))throw new Error('Core localized TMDB lookup missing');
    return{ok:true,status:200,json:async()=>({
      id:1396,name:'Breaking Bad',original_name:'Breaking Bad',first_air_date:'2008-01-20',
      genres:[{id:18,name:'Drama'}],original_language:'en',origin_country:['US'],
      keywords:{results:[]},alternative_titles:{results:[]},external_ids:{imdb_id:'tt0903747'}
    })};
  }
  throw new Error('unexpected TMDB endpoint '+url);
};
const provider=require(process.argv[2]);
(async()=>{
  const value=await provider.getStreams('tt0903747','series',1,1);
  if(!value.length)throw new Error('IMDb Core resolution returned no provider call');
  if(value[0].tmdbId!=='1396')throw new Error('ProviderBase did not receive resolved TMDB id: '+JSON.stringify(value[0]));
  if(value[0].mediaType!=='tv')throw new Error('IMDb Core resolution did not preserve canonical TV type');
  if(calls.length!==2)throw new Error('IMDb Core resolution should use find + one full metadata request: '+calls.join('\n'));
})().catch(e=>{console.error(e);process.exit(1)});
""")

# Conclusive API identity remains authoritative on ordinary TV.
run_case(mixed, r"""
global.fetch=async(url)=>{
  if(!String(url).includes("/tv/62425"))throw new Error("Dark Matter left TV namespace");
  return{ok:true,status:200,json:async()=>({
    id:62425,genres:[{id:18,name:"Drama"}],original_language:"en",origin_country:["CA"],keywords:{results:[]}
  })};
};
const provider=require(process.argv[2]);
(async()=>{
  const value=await provider.getStreams("62425","series",2,1);
  if(!value.length||value[0].mediaType!=="tv"||value[0].degraded)throw new Error("Dark Matter TV classification failed");
})().catch(e=>{console.error(e);process.exit(1)});
""")

print("global media resolver: TMDB API authoritative, semantic safeguard preserved, infra fail-open verified")
