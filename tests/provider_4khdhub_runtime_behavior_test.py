#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0,str(ROOT/"scripts"))
PATCH=ROOT/"scripts/provider_patches/4khdhub_runtime_v1.py"
spec=importlib.util.spec_from_file_location("niakvio_4khdhub_runtime_test",PATCH)
assert spec and spec.loader
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

cfg={"base":"https://4khdhub.one","maxStreams":8,"ua":"NiakVIO-Test"}
wrapper=mod.WRAPPER.replace("CONFIG_PLACEHOLDER",json.dumps(cfg,separators=(",",":")))
js=r'''
"use strict";
const NIAKVIO_PROVIDER_MODEL={officialSite:"https://4khdhub.one",knownSite:"https://4khdhub.one"};
globalThis.__nuvioCoreGetTmdbDataV1=async({mediaType})=>({metadata:mediaType==="tv"
  ? {name:"Breaking Bad",first_air_date:"2008-01-20"}
  : {title:"The Colony",release_date:"2021-08-27"}});
function response(url,text){return {ok:true,status:200,url,async text(){return text}}}
globalThis.fetch=async function(url){
  url=String(url);
  if(url.includes("/?s=The%20Colony%202021")) return response(url,
    '<a class="movie-card" href="/the-colony-movie-7978/"><span class="movie-card-title">The Colony</span><span class="movie-card-format">Movies</span><span class="movie-card-meta">2021</span></a>');
  if(url.endsWith("/the-colony-movie-7978/")) return response(url,
    '<div class="download-item"><span class="file-title">The Colony 2021 2160p [12 GB]</span><a href="https://hubcloud.test/f/abc">HubCloud</a></div>');
  if(url==="https://hubcloud.test/f/abc") return response(url,
    '<a id="download" href="https://hubcloud.test/v/abc">Download</a>');
  if(url==="https://hubcloud.test/v/abc") return response(url,
    '<div class="card-header">The Colony 2021 2160p 12 GB</div><a href="https://media.workers.dev/colony.mkv">Direct</a>');

  if(url.includes("/?s=Breaking%20Bad%20Season%201")) return response(url,
    '<a class="movie-card" href="/breaking-bad-series-1385/"><span class="movie-card-title">Breaking Bad Season 1</span><span class="movie-card-format">Series</span><span class="movie-card-meta">2008</span></a>');
  if(url.endsWith("/breaking-bad-series-1385/")) return response(url,
    '<div class="episode-item"><span class="episode-title">S01</span><div class="episode-download-item"><span class="episode-file-title">Episode-01 Breaking Bad 1080p 2 GB</span><a href="https://hubcloud.test/f/bb">HubCloud</a></div></div>');
  if(url==="https://hubcloud.test/f/bb") return response(url,
    '<a id="download" href="https://hubcloud.test/v/bb">Download</a>');
  if(url==="https://hubcloud.test/v/bb") return response(url,
    '<div class="card-header">Breaking Bad S01E01 1080p 2 GB</div><a href="https://media.workers.dev/bb-s01e01.mkv">Direct</a>');
  throw new Error("unexpected fetch "+url);
};
''' + wrapper + r'''
(async()=>{
  const hook=globalThis.__niakvioProviderRuntimeResolverV1;
  if(!hook||hook.provider!=="4khdhub") throw new Error("hook missing");
  const movie=await hook.resolve(["760873","movie",null,null]);
  const tv=await hook.resolve(["1396","tv",1,1]);
  console.log(JSON.stringify({movie,tv}));
})().catch(e=>{console.error(e.stack||e);process.exit(1)});
'''
with tempfile.TemporaryDirectory() as td:
    path=Path(td)/"probe.cjs"
    path.write_text(js,encoding="utf-8")
    proc=subprocess.run(["node",str(path)],cwd=ROOT,capture_output=True,text=True,check=True)
result=json.loads(proc.stdout.strip().splitlines()[-1])
movie=result["movie"]
tv=result["tv"]
assert len(movie)==1,movie
assert movie[0]["url"]=="https://media.workers.dev/colony.mkv",movie
assert movie[0]["quality"]=="2160p",movie
assert "The Colony" in movie[0]["title"],movie
assert len(tv)==1,tv
assert tv[0]["url"]=="https://media.workers.dev/bb-s01e01.mkv",tv
assert "S01E01" in tv[0]["title"],tv
print("4KHDHub runtime behavior contract passed")
