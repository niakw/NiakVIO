#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / "scripts" / "provider_patches" / "global_media_type_resolution_v1.py"
spec = importlib.util.spec_from_file_location("global_media_type_resolution_v1", PATCH)
assert spec is not None and spec.loader is not None
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

base = r'''
"use strict";
async function getStreams(tmdbId, mediaType, season, episode) {
  return [{ tmdbId, mediaType, season, episode }];
}
module.exports = { getStreams };
'''
patched = mod.apply(base, options={"semantic_types": ["tv", "anime"]})
assert "NUVIO_GLOBAL_MEDIA_TYPE_RESOLUTION_V1" in patched
assert "TMDB_API_KEY" in patched
assert "TMDB_ACCESS_TOKEN" in patched
assert "series" in patched and "show" in patched and "other" in patched

runner = r'''
global.TMDB_API_KEY = String(1);
global.fetch = async (url) => ({
  ok: true,
  json: async () => ({
    id: 46260,
    genres: [{id:16,name:"Animation"}],
    original_language: "ja",
    origin_country: ["JP"],
    keywords: {results:[{name:"anime"}]}
  })
});
const provider = require(process.argv[2]);
(async () => {
  const seriesAnime = await provider.getStreams("46260", "series", 1, 1);
  if (seriesAnime[0].mediaType !== "anime") throw new Error("series anime was not refined to anime");

  delete global.TMDB_API_KEY;
  global.fetch = async () => ({
    ok: true,
    text: async () => "<html><a href='/genre/18-drama'>Drama</a><b>Original Language</b> English</html>"
  });
  const ordinarySeries = await provider.getStreams("1396", "series", 1, 1);
  if (ordinarySeries[0].mediaType !== "tv") throw new Error("series alias did not default to tv");

})().catch((error) => { console.error(error); process.exit(1); });
'''
# Object-form validation needs a provider that accepts the object contract.
object_base = r'''
"use strict";
async function getStreams(arg) { return [arg]; }
module.exports = { getStreams };
'''
object_patched = mod.apply(object_base, options={"semantic_types": ["tv", "anime"]})

with tempfile.TemporaryDirectory() as tmp:
    tmp_path = Path(tmp)
    provider = tmp_path / "provider.js"
    object_provider = tmp_path / "provider-object.js"
    test = tmp_path / "test.js"
    provider.write_text(patched, encoding="utf-8")
    object_provider.write_text(object_patched, encoding="utf-8")

    # Positional Nuvio contract is tested independently from the object compatibility contract.
    test.write_text(runner, encoding="utf-8")
    subprocess.run(["node", str(test), str(provider)], check=True)

    object_runner = r'''
global.fetch = async (url) => {
  if (!String(url).includes("/tv/46260")) throw new Error("anime hint must resolve in TMDB tv namespace");
  return {
    ok: true,
    text: async () => "<html><a href='/genre/16-animation'>Animation</a><div>Original Language Japanese</div><a href='/keyword/anime'>anime</a></html>"
  };
};
const provider = require(process.argv[2]);
(async () => {
  const value = await provider.getStreams({
    tmdbId: "46260",
    mediaType: "series",
    category: "anime",
    season: 1,
    episode: 1
  });
  if (value[0].mediaType !== "anime") throw new Error("TMDB-verified anime category was lost");
  if (value[0].nuvioInputMediaType !== "series") throw new Error("input alias evidence was lost");
  if (value[0].tmdbNamespace !== "tv") throw new Error("anime series did not preserve TMDB tv namespace");
  if (value[0].tmdbIdentity !== "tv:46260") throw new Error("composite TMDB identity missing");
})().catch((error) => { console.error(error); process.exit(1); });
'''
    test.write_text(object_runner, encoding="utf-8")
    subprocess.run(["node", str(test), str(object_provider)], check=True)

anime_only = mod.apply(base, options={"semantic_types": ["anime"]})
with tempfile.TemporaryDirectory() as tmp:
    tmp_path = Path(tmp)
    provider = tmp_path / "anime-only.js"
    test = tmp_path / "anime-only-test.js"
    provider.write_text(anime_only, encoding="utf-8")
    test.write_text(r'''
let fetches = 0;
global.fetch = async (url) => {
  fetches += 1;
  if (String(url).includes("/tv/280049")) {
    return {
      ok: true,
      text: async () => "<html><a href='/genre/16-animation'>Animation</a><div>Original Language Japanese</div><a href='/keyword/anime'>anime</a></html>"
    };
  }
  return {
    ok: true,
    text: async () => "<html><a href='/genre/18-drama'>Drama</a><div>Original Language English</div></html>"
  };
};
const provider = require(process.argv[2]);
(async () => {
  const hellMode = await provider.getStreams("280049", "series", 1, 11);
  if (hellMode[0].mediaType !== "anime") throw new Error("Hell Mode was not classified anime before provider execution");
  const hellModeAgain = await provider.getStreams("280049", "series", 1, 12);
  if (hellModeAgain[0].mediaType !== "anime") throw new Error("cached anime classification was lost");
  if (fetches !== 1) throw new Error("TMDB classification was not cached inside provider runtime");

  const ordinaryTv = await provider.getStreams("1396", "series", 1, 1);
  if (!Array.isArray(ordinaryTv) || ordinaryTv.length !== 0) throw new Error("anime provider did not exit for ordinary TV");
})().catch((error) => { console.error(error); process.exit(1); });
''', encoding="utf-8")
    subprocess.run(["node", str(test), str(provider)], check=True)

public_mixed = mod.apply(base, options={"semantic_types": ["tv", "anime"]})
with tempfile.TemporaryDirectory() as tmp:
    tmp_path = Path(tmp)
    provider = tmp_path / "mixed-public.js"
    test = tmp_path / "mixed-public-test.js"
    provider.write_text(public_mixed, encoding="utf-8")
    test.write_text(r'''
global.fetch = async () => ({
  ok: true,
  text: async () => "<html><a href='/genre/16-animation'>Animation</a><div>Original Language Japanese</div><a href='/keyword/anime'>anime</a></html>"
});
const provider = require(process.argv[2]);
(async () => {
  const value = await provider.getStreams("280049", "series", 1, 11);
  if (value[0].mediaType !== "anime") throw new Error("public TMDB fallback did not refine series to anime");
})().catch((error) => { console.error(error); process.exit(1); });
''', encoding="utf-8")
    subprocess.run(["node", str(test), str(provider)], check=True)

print("global media-type resolver tests passed: transport series=>tv, semantic/TMDB anime=>anime without CI-only secret")

# Inverse regression: TV-only provider must not run for an anime surfaced as series/tv.
tv_only = mod.apply(base, options={"semantic_types": ["tv"]})
with tempfile.TemporaryDirectory() as tmp:
    tmp_path = Path(tmp)
    provider = tmp_path / "tv-only.js"
    test = tmp_path / "tv-only-test.js"
    provider.write_text(tv_only, encoding="utf-8")
    test.write_text(r'''
global.fetch = async () => ({
  ok: true,
  text: async () => "<html><a href='/genre/16-animation'>Animation</a><div>Original Language Japanese</div><a href='/keyword/anime'>anime</a></html>"
});
const provider = require(process.argv[2]);
(async () => {
  const mobPsycho = await provider.getStreams("30984", "series", 1, 7);
  if (!Array.isArray(mobPsycho) || mobPsycho.length !== 0) throw new Error("TV-only provider processed anime instead of exiting at TMDB entity gate");
})().catch((error) => { console.error(error); process.exit(1); });
''', encoding="utf-8")
    subprocess.run(["node", str(test), str(provider)], check=True)

# Ambiguous tv/anime classification failure is fail-closed.
fail_closed = mod.apply(base, options={"semantic_types": ["tv"]})
with tempfile.TemporaryDirectory() as tmp:
    tmp_path = Path(tmp)
    provider = tmp_path / "fail-closed.js"
    test = tmp_path / "fail-closed-test.js"
    provider.write_text(fail_closed, encoding="utf-8")
    test.write_text(r'''
global.fetch = async () => { throw new Error("metadata unavailable"); };
const provider = require(process.argv[2]);
(async () => {
  const value = await provider.getStreams("30984", "series", 1, 7);
  if (!Array.isArray(value) || value.length !== 0) throw new Error("ambiguous media classification must fail closed");
})().catch((error) => { console.error(error); process.exit(1); });
''', encoding="utf-8")
    subprocess.run(["node", str(test), str(provider)], check=True)

# TMDB IDs are namespaced: the same numeric id may exist in movie and tv.
mixed_all = mod.apply(base, options={"semantic_types": ["movie", "tv", "anime"]})
with tempfile.TemporaryDirectory() as tmp:
    tmp_path = Path(tmp)
    provider = tmp_path / "mixed-all.js"
    test = tmp_path / "mixed-all-test.js"
    provider.write_text(mixed_all, encoding="utf-8")
    test.write_text(r'''
const seen = [];
global.fetch = async (url) => {
  seen.push(String(url));
  const u = String(url);
  if (u.includes("/movie/4242")) return {
    ok: true,
    text: async () => "<html><a href='/genre/28-action'>Action</a><div>Original Language English</div></html>"
  };
  if (u.includes("/tv/4242")) return {
    ok: true,
    text: async () => "<html><a href='/genre/16-animation'>Animation</a><div>Original Language Japanese</div><a href='/keyword/anime'>anime</a></html>"
  };
  throw new Error("unexpected URL "+u);
};
const provider = require(process.argv[2]);
(async () => {
  const movie = await provider.getStreams("4242", "movie", null, null);
  if (movie[0].mediaType !== "movie") throw new Error("movie namespace was not preserved");
  const tvAnime = await provider.getStreams("4242", "series", 1, 1);
  if (tvAnime[0].mediaType !== "anime") throw new Error("tv namespace anime classification failed");
  if (!seen.some((u) => u.includes("/movie/4242"))) throw new Error("movie namespace lookup missing");
  if (!seen.some((u) => u.includes("/tv/4242"))) throw new Error("tv namespace lookup missing");
})().catch((error) => { console.error(error); process.exit(1); });
''', encoding="utf-8")
    subprocess.run(["node", str(test), str(provider)], check=True)

# Semantic anime must preserve the original TMDB namespace for downstream route adaptation.
context_base = r'''
"use strict";
async function getStreams(tmdbId, mediaType) {
  const ctx = globalThis.__nuvioMediaContext || {};
  return [{tmdbId,mediaType,namespace:ctx.tmdbNamespace,identity:ctx.tmdbIdentity,canonical:ctx.canonicalMediaType}];
}
module.exports = {getStreams};
'''
context_provider = mod.apply(context_base, options={"semantic_types":["movie","tv","anime"]})
with tempfile.TemporaryDirectory() as tmp:
    tmp_path=Path(tmp)
    provider=tmp_path/"context.js"
    runner=tmp_path/"context-test.js"
    provider.write_text(context_provider,encoding="utf-8")
    runner.write_text(r'''
global.fetch=async (url)=>({
  ok:true,
  text:async()=>"<html><a href='/genre/16-animation'>Animation</a><div>Original Language Japanese</div><a href='/keyword/anime'>anime</a></html>"
});
const provider=require(process.argv[2]);
(async()=>{
  const series=await provider.getStreams("280049","series",1,11);
  if(series[0].mediaType!=="anime"||series[0].namespace!=="tv"||series[0].identity!=="tv:280049") throw new Error("anime series lost tv namespace context");
  const movie=await provider.getStreams("4242","movie",null,null);
  if(movie[0].mediaType!=="anime"||movie[0].namespace!=="movie"||movie[0].identity!=="movie:4242") throw new Error("anime movie lost movie namespace context");
})().catch(e=>{console.error(e);process.exit(1)});
''',encoding="utf-8")
    subprocess.run(["node",str(runner),str(provider)],check=True)

# explicit anime without episode resolves namespace from TMDB instead of assuming TV.
anime_ambiguous = mod.apply(object_base, options={"semantic_types": ["anime"]})
with tempfile.TemporaryDirectory() as tmp:
    tmp_path = Path(tmp)
    provider = tmp_path / "anime-ambiguous.js"
    test = tmp_path / "anime-ambiguous-test.js"
    provider.write_text(anime_ambiguous, encoding="utf-8")
    test.write_text(r'''
const seen=[];
global.fetch=async(url)=>{
  const u=String(url);seen.push(u);
  if(u.includes("/tv/4242"))return{ok:true,text:async()=>"<html><a href='/genre/18-drama'>Drama</a><div>Original Language English</div></html>"};
  if(u.includes("/movie/4242"))return{ok:true,text:async()=>"<html><a href='/genre/16-animation'>Animation</a><div>Original Language Japanese</div><a href='/keyword/anime'>anime</a></html>"};
  throw new Error("unexpected "+u);
};
const provider=require(process.argv[2]);
(async()=>{
 const value=await provider.getStreams({tmdbId:"4242",mediaType:"anime"});
 if(!value.length||value[0].mediaType!=="anime")throw new Error("explicit anime unresolved");
 if(value[0].tmdbNamespace!=="movie"||value[0].tmdbIdentity!=="movie:4242")throw new Error("wrong anime namespace");
 if(!seen.some(u=>u.includes("/tv/4242"))||!seen.some(u=>u.includes("/movie/4242")))throw new Error("both namespaces not checked");
})().catch(e=>{console.error(e);process.exit(1);});
''', encoding="utf-8")
    subprocess.run(["node", str(test), str(provider)], check=True)

# Episodic anime is deterministically TV.
anime_episode = mod.apply(object_base, options={"semantic_types": ["anime"]})
with tempfile.TemporaryDirectory() as tmp:
    tmp_path = Path(tmp)
    provider = tmp_path / "anime-episode.js"
    test = tmp_path / "anime-episode-test.js"
    provider.write_text(anime_episode, encoding="utf-8")
    test.write_text(r'''
const seen=[];
global.fetch=async(url)=>{
 const u=String(url);seen.push(u);
 if(!u.includes("/tv/280049"))throw new Error("episodic anime left TV namespace");
 return{ok:true,text:async()=>"<html><a href='/keyword/anime'>anime</a><a href='/genre/16-animation'>Animation</a><div>Original Language Japanese</div></html>"};
};
const provider=require(process.argv[2]);
(async()=>{
 const value=await provider.getStreams({tmdbId:"280049",mediaType:"anime",season:1,episode:11});
 if(!value.length||value[0].tmdbNamespace!=="tv")throw new Error("episodic anime not TV");
 if(seen.some(u=>u.includes("/movie/")))throw new Error("unnecessary movie namespace probe");
})().catch(e=>{console.error(e);process.exit(1);});
''', encoding="utf-8")
    subprocess.run(["node", str(test), str(provider)], check=True)

# A TV-only provider can still reject movie at zero cost; anime capability is the exception.
tv_only_no_movie_or_anime = mod.apply(base, options={"semantic_types": ["tv"]})
with tempfile.TemporaryDirectory() as tmp:
    tmp_path = Path(tmp)
    provider = tmp_path / "tv-only-no-movie.js"
    test = tmp_path / "tv-only-no-movie-test.js"
    provider.write_text(tv_only_no_movie_or_anime, encoding="utf-8")
    test.write_text(r'''
let fetches=0;
global.fetch=async()=>{fetches+=1;throw new Error("TV-only movie request must exit before TMDB");};
const provider=require(process.argv[2]);
(async()=>{
 const value=await provider.getStreams("157336","movie",null,null);
 if(!Array.isArray(value)||value.length!==0)throw new Error("TV-only provider processed movie request");
 if(fetches!==0)throw new Error("TV-only provider performed unnecessary TMDB lookup");
})().catch(e=>{console.error(e);process.exit(1);});
''', encoding="utf-8")
    subprocess.run(["node", str(test), str(provider)], check=True)

# Anime semantic capability is sufficient to admit movie transport to the TMDB gate.
anime_movie_via_transport_alias = mod.apply(base, options={"semantic_types": ["anime"]})
with tempfile.TemporaryDirectory() as tmp:
    tmp_path = Path(tmp)
    provider = tmp_path / "anime-movie-transport-alias.js"
    test = tmp_path / "anime-movie-transport-alias-test.js"
    provider.write_text(anime_movie_via_transport_alias, encoding="utf-8")
    test.write_text(r'''
let seen=[];
global.fetch=async(url)=>{
 const u=String(url);seen.push(u);
 if(!u.includes("/movie/4242"))throw new Error("anime movie used wrong TMDB namespace");
 return{ok:true,text:async()=>"<html><a href='/genre/16-animation'>Animation</a><div>Original Language Japanese</div><a href='/keyword/anime'>anime</a></html>"};
};
const provider=require(process.argv[2]);
(async()=>{
 const value=await provider.getStreams("4242","movie",null,null);
 if(!value.length||value[0].mediaType!=="anime")throw new Error("anime-only provider lost anime movie transported as movie");
 if(seen.length!==1)throw new Error("anime movie classification should need one TMDB lookup");
})().catch(e=>{console.error(e);process.exit(1);});
''', encoding="utf-8")
    subprocess.run(["node", str(test), str(provider)], check=True)

# The same anime-only provider must reject an ordinary movie after TMDB.
anime_only_regular_movie = mod.apply(base, options={"semantic_types": ["anime"]})
with tempfile.TemporaryDirectory() as tmp:
    tmp_path = Path(tmp)
    provider = tmp_path / "anime-only-regular-movie.js"
    test = tmp_path / "anime-only-regular-movie-test.js"
    provider.write_text(anime_only_regular_movie, encoding="utf-8")
    test.write_text(r'''
const seen=[];
global.fetch=async(url)=>{
 const u=String(url);seen.push(u);
 if(!u.includes("/movie/4242"))throw new Error("ordinary movie used wrong TMDB namespace");
 return{ok:true,text:async()=>"<html><a href='/genre/18-drama'>Drama</a><div>Original Language English</div></html>"};
};
const provider=require(process.argv[2]);
(async()=>{
 const value=await provider.getStreams("4242","movie",null,null);
 if(!Array.isArray(value)||value.length!==0)throw new Error("anime-only provider processed an ordinary movie");
 if(seen.length!==1)throw new Error("ordinary movie should be rejected after one TMDB lookup");
})().catch(e=>{console.error(e);process.exit(1);});
''', encoding="utf-8")
    subprocess.run(["node", str(test), str(provider)], check=True)
