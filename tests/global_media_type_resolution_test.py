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
  return [{
    tmdbId, mediaType, season, episode,
    canonicalMediaType: ctx.canonicalMediaType || "",
    providerMediaType: ctx.providerMediaType || mediaType,
    degraded: ctx.tmdbResolutionDegraded === true
  }];
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
  if(!Array.isArray(value)||!value.length||value[0]==null||value[0].canonicalMediaType!=="anime"||value[0].mediaType!=="tv")throw new Error("Hell Mode semantic/transport split failed");
  const again=await provider.getStreams("280049","series",1,12);
  if(!Array.isArray(again)||!again.length||again[0]==null||again[0].canonicalMediaType!=="anime"||again[0].mediaType!=="tv")throw new Error("anime cache/transport lost");
  if(calls!==1)throw new Error("TMDB lookup was not cached");
})().catch(e=>{console.error(e);process.exit(1)});
""")

# Transient TMDB infrastructure failure is never cached.
run_case(mixed, r"""
let calls=0;
global.fetch=async(url)=>{
  calls++;
  if(calls<=2)throw new Error("temporary TMDB outage");
  return{ok:true,status:200,json:async()=>({
    id:280049,genres:[{id:16,name:"Animation"}],original_language:"ja",
    origin_country:["JP"],keywords:{results:[{name:"anime"}]}
  })};
};
const provider=require(process.argv[2]);
(async()=>{
  const degraded=await provider.getStreams("280049","series",1,11);
  if(!Array.isArray(degraded)||!degraded.length||degraded[0].degraded!==true)throw new Error("first outage did not fail open");
  const recovered=await provider.getStreams("280049","series",1,11);
  if(!Array.isArray(recovered)||!recovered.length||recovered[0].canonicalMediaType!=="anime"||recovered[0].degraded===true)
    throw new Error("transient TMDB outage poisoned later request: "+JSON.stringify(recovered));
  if(calls!==3)throw new Error("transient unavailable TMDB result was cached");
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
  if(!Array.isArray(value)||!value.length||value[0]==null||value[0].mediaType!=="tv"||value[0].degraded!==true)throw new Error("TV fallback must stay executable on TMDB outage");
})().catch(e=>{console.error(e);process.exit(1)});
""")

run_case(anime_only, r"""
global.fetch=async()=>{throw new Error("TMDB unavailable")};
const provider=require(process.argv[2]);
(async()=>{
  const value=await provider.getStreams("280049","series",1,11);
  if(!Array.isArray(value)||!value.length||value[0]==null||value[0].mediaType!=="anime"||value[0].degraded!==true)throw new Error("Anime-only provider must preserve anime transport on metadata outage");
})().catch(e=>{console.error(e);process.exit(1)});
""")

movie_only = mod.apply(BASE, options={"semantic_types": ["movie"]})
run_case(movie_only, r"""
global.fetch=async()=>{throw new Error("TMDB unavailable")};
const provider=require(process.argv[2]);
(async()=>{
  const value=await provider.getStreams("157336","movie",null,null);
  if(!Array.isArray(value)||!value.length||value[0]==null||value[0].mediaType!=="movie"||value[0].degraded!==true)throw new Error("Movie fallback failed");
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

# Capability filtering happens only after TMDB classification.
run_case(tv_only, r"""
let calls=0;
global.fetch=async(url)=>{
  calls++;
  if(!String(url).includes("/movie/157336"))throw new Error("movie classification did not hit TMDB first");
  return{ok:true,status:200,json:async()=>({
    id:157336,title:"Interstellar",release_date:"2014-11-05",
    genres:[{id:18,name:"Drama"}],original_language:"en",
    production_countries:[{iso_3166_1:"US"}],keywords:{keywords:[]}
  })};
};
const provider=require(process.argv[2]);
(async()=>{
  const value=await provider.getStreams("157336","movie");
  if(!Array.isArray(value)||value.length!==0)throw new Error("TV-only provider must reject TMDB-proven movie after lookup");
  if(calls!==1)throw new Error("provider capability was checked before TMDB");
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
  if(!Array.isArray(value)||!value.length||value[0]==null||value[0].mediaType!=="tv"||value[0].degraded)throw new Error("Dark Matter TV classification failed");
})().catch(e=>{console.error(e);process.exit(1)});
""")

purstream_mixed = mod.apply(
    BASE,
    options={
        "semantic_types": ["movie", "tv", "anime"],
        "request_type_aliases": {"anime": "tmdb_namespace"},
    },
)
run_case(purstream_mixed, r"""
global.fetch=async(url)=>{
  url=String(url);
  if(!url.includes("/tv/46260"))throw new Error("Naruto must resolve in TMDB TV namespace: "+url);
  return{ok:true,status:200,json:async()=>({
    id:46260,name:"Naruto",genres:[{id:16,name:"Animation"}],
    original_language:"ja",origin_country:["JP"],keywords:{results:[{name:"anime"}]}
  })};
};
const provider=require(process.argv[2]);
(async()=>{
  const fromAnime=await provider.getStreams("46260","anime",1,1);
  if(!Array.isArray(fromAnime)||!fromAnime.length||fromAnime[0]==null||fromAnime[0].canonicalMediaType!=="anime"||fromAnime[0].mediaType!=="tv")
    throw new Error("Purstream anime must stay semantic anime but use tv transport");
  const fromSeries=await provider.getStreams("46260","series",1,1);
  if(!Array.isArray(fromSeries)||!fromSeries.length||fromSeries[0]==null||fromSeries[0].canonicalMediaType!=="anime"||fromSeries[0].mediaType!=="tv")
    throw new Error("Purstream series anime transport mismatch");
  const fromTv=await provider.getStreams("46260","tv",1,1);
  if(!Array.isArray(fromTv)||!fromTv.length||fromTv[0]==null||fromTv[0].canonicalMediaType!=="anime"||fromTv[0].mediaType!=="tv")
    throw new Error("Purstream tv anime transport mismatch");
})().catch(e=>{console.error(e);process.exit(1)});
""")

run_case(purstream_mixed, r"""
global.fetch=async(url)=>{
  url=String(url);
  if(url.includes("/tv/4242"))return{ok:false,status:404,json:async()=>({})};
  if(url.includes("/movie/4242"))return{ok:true,status:200,json:async()=>({
    id:4242,title:"Anime Movie",release_date:"2026-01-01",
    genres:[{id:16,name:"Animation"}],original_language:"ja",
    production_countries:[{iso_3166_1:"JP"}],keywords:{keywords:[{name:"anime"}]}
  })};
  throw new Error("unexpected TMDB endpoint "+url);
};
const provider=require(process.argv[2]);
(async()=>{
  const value=await provider.getStreams("4242","anime");
  if(!Array.isArray(value)||!value.length||value[0]==null||value[0].canonicalMediaType!=="anime"||value[0].mediaType!=="movie")
    throw new Error("Purstream anime movie must use TMDB movie transport");
})().catch(e=>{console.error(e);process.exit(1)});
""")

run_case(purstream_mixed, r"""
const calls=[];
global.fetch=async(url)=>{
  url=String(url);calls.push(url);
  if(url.includes("/movie/4242"))return{ok:true,status:200,json:async()=>({
    id:4242,title:"Anime Movie",release_date:"2026-01-01",
    genres:[{id:16,name:"Animation"}],original_language:"ja",
    production_countries:[{iso_3166_1:"JP"}],keywords:{keywords:[{name:"anime"}]}
  })};
  throw new Error("unexpected TMDB endpoint "+url);
};
const provider=require(process.argv[2]);
(async()=>{
  const value=await provider.getStreams("4242","movie");
  if(!Array.isArray(value)||!value.length||value[0]==null||value[0].canonicalMediaType!=="anime"||value[0].mediaType!=="movie")
    throw new Error("movie-transported anime film was not canonically reset");
  if(calls.length!==1||!calls[0].includes("/movie/4242"))
    throw new Error("movie hint must only prioritize lookup, not alter canonical result");
})().catch(e=>{console.error(e);process.exit(1)});
""")

# A wrong client movie label must not prevent fallback into the TV namespace.
run_case(mixed, r"""
const calls=[];
global.fetch=async(url)=>{
  url=String(url);calls.push(url);
  if(url.includes("/movie/777001"))return{ok:false,status:404,json:async()=>({})};
  if(url.includes("/tv/777001"))return{ok:true,status:200,json:async()=>({
    id:777001,name:"Recovered Series",first_air_date:"2026-01-01",
    genres:[{id:18,name:"Drama"}],original_language:"en",origin_country:["US"],keywords:{results:[]}
  })};
  throw new Error("unexpected TMDB endpoint "+url);
};
const provider=require(process.argv[2]);
(async()=>{
  const value=await provider.getStreams("777001","movie");
  if(!Array.isArray(value)||!value.length||value[0]==null||value[0].canonicalMediaType!=="tv"||value[0].mediaType!=="tv")
    throw new Error("movie-labelled TV work did not recover through canonical reset");
  if(calls.length!==2)throw new Error("alternate TV namespace was not attempted");
})().catch(e=>{console.error(e);process.exit(1)});
""")

# A wrong client TV/series label must likewise fall back into the movie namespace.
movie_tv_mixed = mod.apply(BASE, options={"semantic_types": ["movie", "tv"]})
run_case(movie_tv_mixed, r"""
const calls=[];
global.fetch=async(url)=>{
  url=String(url);calls.push(url);
  if(url.includes("/tv/777002"))return{ok:false,status:404,json:async()=>({})};
  if(url.includes("/movie/777002"))return{ok:true,status:200,json:async()=>({
    id:777002,title:"Recovered Movie",release_date:"2026-01-01",
    genres:[{id:18,name:"Drama"}],original_language:"en",
    production_countries:[{iso_3166_1:"US"}],keywords:{keywords:[]}
  })};
  throw new Error("unexpected TMDB endpoint "+url);
};
const provider=require(process.argv[2]);
(async()=>{
  const value=await provider.getStreams("777002","series");
  if(!Array.isArray(value)||!value.length||value[0]==null||value[0].canonicalMediaType!=="movie"||value[0].mediaType!=="movie")
    throw new Error("series-labelled movie did not recover through canonical reset");
  if(calls.length!==2)throw new Error("alternate movie namespace was not attempted");
})().catch(e=>{console.error(e);process.exit(1)});
""")

# An input labelled anime is also only a hint. Authoritative ordinary TV metadata wins.
run_case(mixed, r"""
global.fetch=async(url)=>{
  url=String(url);
  if(!url.includes("/tv/777003"))throw new Error("anime hint should prioritize TV but not force anime");
  return{ok:true,status:200,json:async()=>({
    id:777003,name:"Ordinary TV",first_air_date:"2026-01-01",
    genres:[{id:18,name:"Drama"}],original_language:"en",origin_country:["US"],keywords:{results:[]}
  })};
};
const provider=require(process.argv[2]);
(async()=>{
  const value=await provider.getStreams("777003","anime",1,1);
  if(!Array.isArray(value)||!value.length||value[0]==null||value[0].canonicalMediaType!=="tv"||value[0].mediaType!=="tv")
    throw new Error("authoritative TV type did not replace anime input hint");
})().catch(e=>{console.error(e);process.exit(1)});
""")


# The JS-side budget cannot preempt a non-cooperative native bridge, but once a
# native request returns after the deadline it must fail closed immediately and
# must never let the provider chain another stale network request.
TIMEOUT_BASE = r"""
"use strict";
async function getStreams(tmdbId, mediaType) {
  await fetch("https://provider.example/slow-first");
  await fetch("https://provider.example/forbidden-second");
  return [{url:"https://media.example/video.m3u8"}];
}
module.exports = { getStreams };
"""
timeout_bounded = mod.apply(
    TIMEOUT_BASE,
    options={"semantic_types": ["movie"], "provider_timeout_ms": 5000},
)
run_case(timeout_bounded, r"""
let now=1000;
let providerCalls=[];
Date.now=()=>now;
global.fetch=async(url)=>{
  url=String(url);
  if(url.includes("api.themoviedb.org/3/movie/157336")){
    return{ok:true,status:200,json:async()=>({
      id:157336,title:"Interstellar",release_date:"2014-11-05",
      genres:[{id:18,name:"Drama"}],original_language:"en",
      production_countries:[{iso_3166_1:"US"}],keywords:{keywords:[]}
    })};
  }
  providerCalls.push(url);
  if(url.includes("slow-first")){
    now=7000;
    return{ok:true,status:200,text:async()=>"#EXTM3U"};
  }
  throw new Error("provider issued request after execution deadline: "+url);
};
const provider=require(process.argv[2]);
(async()=>{
  const value=await provider.getStreams("157336","movie");
  if(!Array.isArray(value)||value.length!==0)throw new Error("expired provider budget must fail closed");
  if(providerCalls.length!==1||!providerCalls[0].includes("slow-first"))
    throw new Error("provider budget allowed chained request: "+providerCalls.join(","));
})().catch(e=>{console.error(e);process.exit(1)});
""")



# Request context must never stick across one long-lived native JS instance.
# This reproduces the real Android TV failure: first work type used to poison
# every later getStreams call until app cache/process reset.
run_case(purstream_mixed, r"""
const calls=[];
global.__nuvioMediaContext={
  canonicalMediaType:'anime',
  providerMediaType:'anime',
  tmdbMetadata:{id:999999,genres:[{id:16}],original_language:'ja',origin_country:['JP']}
};
global.fetch=async(url)=>{
  url=String(url);calls.push(url);
  if(url.includes('/tv/62425?'))return{ok:true,status:200,json:async()=>({
    id:62425,name:'Dark Matter',genres:[{id:18,name:'Drama'}],
    original_language:'en',origin_country:['CA'],keywords:{results:[]}
  })};
  if(url.includes('/tv/280049?'))return{ok:true,status:200,json:async()=>({
    id:280049,name:'Hell Mode',genres:[{id:16,name:'Animation'}],
    original_language:'ja',origin_country:['JP'],keywords:{results:[{name:'anime'}]}
  })};
  if(url.includes('/movie/4242?'))return{ok:true,status:200,json:async()=>({
    id:4242,title:'Anime Movie',release_date:'2026-01-01',
    genres:[{id:16,name:'Animation'}],original_language:'ja',
    production_countries:[{iso_3166_1:'JP'}],keywords:{keywords:[{name:'anime'}]}
  })};
  if(url.includes('/movie/157336?'))return{ok:true,status:200,json:async()=>({
    id:157336,title:'Interstellar',release_date:'2014-11-05',
    genres:[{id:18,name:'Drama'}],original_language:'en',
    production_countries:[{iso_3166_1:'US'}],keywords:{keywords:[]}
  })};
  throw new Error('unexpected TMDB endpoint '+url);
};
const provider=require(process.argv[2]);
(async()=>{
  const dark1=await provider.getStreams('62425','series',2,1);
  if(!Array.isArray(dark1)||!dark1.length||dark1[0]==null||dark1[0].canonicalMediaType!=='tv'||dark1[0].mediaType!=='tv')
    throw new Error('stale anime context poisoned initial TV request: '+JSON.stringify(dark1));

  const hell=await provider.getStreams('280049','series',1,11);
  if(!Array.isArray(hell)||!hell.length||hell[0]==null||hell[0].canonicalMediaType!=='anime'||hell[0].mediaType!=='tv')
    throw new Error('TV->anime transition failed: '+JSON.stringify(hell));

  const animeMovie=await provider.getStreams('4242','movie');
  if(!Array.isArray(animeMovie)||!animeMovie.length||animeMovie[0]==null||animeMovie[0].canonicalMediaType!=='anime'||animeMovie[0].mediaType!=='movie')
    throw new Error('anime movie semantic/transport split failed: '+JSON.stringify(animeMovie));

  const movie=await provider.getStreams('157336','movie');
  if(!Array.isArray(movie)||!movie.length||movie[0]==null||movie[0].canonicalMediaType!=='movie'||movie[0].mediaType!=='movie')
    throw new Error('anime movie poisoned ordinary movie: '+JSON.stringify(movie));

  const dark2=await provider.getStreams('62425','series',2,2);
  if(!Array.isArray(dark2)||!dark2.length||dark2[0]==null||dark2[0].canonicalMediaType!=='tv'||dark2[0].mediaType!=='tv')
    throw new Error('movie/anime history poisoned later TV request: '+JSON.stringify(dark2));

  if(Object.prototype.hasOwnProperty.call(global,'__nuvioMediaContext'))
    throw new Error('request media context leaked after getStreams completion');
})().catch(e=>{console.error(e);process.exit(1)});
""")

# Concurrent request teardown is generation-scoped. A late old request must not
# delete the newer request's media context/deadline.
CONCURRENT_BASE = r"""
"use strict";
async function getStreams(tmdbId, mediaType, season, episode) {
  const ctx = globalThis.__nuvioMediaContext || {};
  if (tmdbId === "62425") {
    globalThis.__oldStarted = true;
    await globalThis.__oldGate;
  } else if (tmdbId === "280049") {
    globalThis.__newStarted = true;
    await globalThis.__newGate;
  }
  return [{ tmdbId, mediaType, canonicalMediaType: ctx.canonicalMediaType || "", requestToken: ctx.requestToken || 0 }];
}
module.exports = { getStreams };
"""
concurrent = mod.apply(CONCURRENT_BASE, options={"semantic_types": ["tv", "anime"], "provider_timeout_ms": 25000})
run_case(concurrent, r"""
let releaseOld,releaseNew;
global.__oldGate=new Promise(r=>{releaseOld=r});
global.__newGate=new Promise(r=>{releaseNew=r});
global.fetch=async(url)=>{
  url=String(url);
  if(url.includes('/tv/62425?'))return{ok:true,status:200,json:async()=>({
    id:62425,name:'Dark Matter',genres:[{id:18,name:'Drama'}],original_language:'en',origin_country:['CA'],keywords:{results:[]}
  })};
  if(url.includes('/tv/280049?'))return{ok:true,status:200,json:async()=>({
    id:280049,name:'Hell Mode',genres:[{id:16,name:'Animation'}],original_language:'ja',origin_country:['JP'],keywords:{results:[{name:'anime'}]}
  })};
  throw new Error('unexpected endpoint '+url);
};
const provider=require(process.argv[2]);
const spin=async(flag)=>{for(let i=0;i<200&&!global[flag];i++)await new Promise(r=>setImmediate(r));if(!global[flag])throw new Error(flag+' not reached')};
(async()=>{
  const old=provider.getStreams('62425','series',1,1);
  await spin('__oldStarted');
  const newer=provider.getStreams('280049','series',1,1);
  await spin('__newStarted');
  const newerToken=global.__nuvioMediaContext&&global.__nuvioMediaContext.requestToken;
  if(!newerToken)throw new Error('new request token missing');
  releaseOld();
  const oldValue=await old;
  if(!Array.isArray(oldValue)||oldValue.length!==0)throw new Error('late old request was not discarded');
  if(!global.__nuvioMediaContext||global.__nuvioMediaContext.requestToken!==newerToken)
    throw new Error('old request cleaned newer context');
  releaseNew();
  const newValue=await newer;
  if(!Array.isArray(newValue)||!newValue.length||newValue[0].canonicalMediaType!=='anime')
    throw new Error('new request failed after old teardown: '+JSON.stringify(newValue));
  if(Object.prototype.hasOwnProperty.call(global,'__nuvioMediaContext'))throw new Error('final media context leaked');
  if(Object.prototype.hasOwnProperty.call(global,'__nuvioProviderDeadlineMs'))throw new Error('deadline leaked');
  if(Object.prototype.hasOwnProperty.call(global,'__nuvioProviderRequestToken'))throw new Error('request token leaked');
})().catch(e=>{console.error(e);process.exit(1)});
""")

# Reverse direction must be isolated too: anime first must not freeze the instance.
run_case(purstream_mixed, r"""
global.fetch=async(url)=>{
  url=String(url);
  if(url.includes('/tv/280049?'))return{ok:true,status:200,json:async()=>({
    id:280049,name:'Hell Mode',genres:[{id:16,name:'Animation'}],
    original_language:'ja',origin_country:['JP'],keywords:{results:[{name:'anime'}]}
  })};
  if(url.includes('/tv/62425?'))return{ok:true,status:200,json:async()=>({
    id:62425,name:'Dark Matter',genres:[{id:18,name:'Drama'}],
    original_language:'en',origin_country:['CA'],keywords:{results:[]}
  })};
  throw new Error('unexpected TMDB endpoint '+url);
};
const provider=require(process.argv[2]);
(async()=>{
  const anime=await provider.getStreams('280049','anime',1,11);
  if(!Array.isArray(anime)||!anime.length||anime[0]==null||anime[0].canonicalMediaType!=='anime'||anime[0].mediaType!=='tv')
    throw new Error('anime-first request failed');
  const tv=await provider.getStreams('62425','series',2,1);
  if(!Array.isArray(tv)||!tv.length||tv[0]==null||tv[0].canonicalMediaType!=='tv'||tv[0].mediaType!=='tv')
    throw new Error('anime-first instance froze later TV request: '+JSON.stringify(tv));
})().catch(e=>{console.error(e);process.exit(1)});
""")

print("global media resolver: TMDB API authoritative, canonical/transport split, aliases and fail-open verified")
