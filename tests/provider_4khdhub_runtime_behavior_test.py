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
const scenario=process.argv[2]||"normal";
globalThis.__nuvioCoreGetTmdbDataV1=async({mediaType})=>({metadata:mediaType==="tv"
  ? {name:"Breaking Bad",first_air_date:"2008-01-20"}
  : {title:"The Colony",release_date:"2021-08-27"}});
function response(url,text){return {ok:true,status:200,url,async text(){return text}}}
globalThis.fetch=async function(url){
  url=String(url);
  const query=new URL(url).searchParams.get("s");
  if(query==="The Colony 2021"||query==="The Colony") {
    if(scenario==="title_only"&&query!=="The Colony")return response(url,'<main>No results</main>');
    const format=scenario==="wrong_movie_type"?"Series":"Movies",year=scenario==="wrong_year"?"2001":"2021";
    return response(url,'<a class="movie-card" href="/the-colony-movie-7978/"><div class="movie-card-content"><span class="movie-card-title">The Colony</span><span class="movie-card-format">'+format+'</span><span class="movie-card-meta">'+year+'</span></div></a>');
  }
  if(url.endsWith("/the-colony-movie-7978/")) return response(url,
    '<div class="download-item"><span class="file-title">The Colony 2021 2160p [12 GB]</span><a href="https://hubcloud.test/f/abc">HubCloud</a></div>');
  if(url==="https://hubcloud.test/f/abc") return response(url,
    '<a id="download" href="https://hubcloud.test/v/abc">Download</a>');
  if(url==="https://hubcloud.test/v/abc") return response(url,
    '<div class="card-header">The Colony 2021 2160p 12 GB</div><a href="https://media.workers.dev/colony.mkv">Direct</a>');

  if(query==="Breaking Bad Season 1"||query==="Breaking Bad 2008"||query==="Breaking Bad") {
    if(scenario==="title_only"&&query!=="Breaking Bad")return response(url,'<main>No results</main>');
    const format=scenario==="wrong_tv_type"?"Movies":"Series";
    return response(url,'<a class="movie-card" href="/breaking-bad-series-1385/"><div class="movie-card-content"><span class="movie-card-title">Breaking Bad Season 1</span><span class="movie-card-format">'+format+'</span><span class="movie-card-meta">2008</span></div></a>');
  }
  if(url.endsWith("/breaking-bad-series-1385/")) return response(url,
    '<div id="episodes"><div class="episode-download-item"><span class="episode-file-title">Breaking Bad S01E01 1080p 2 GB</span><a href="https://hubcloud.test/f/bb">HubCloud</a></div></div>');
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
  const wrongEpisode=await hook.resolve(["1396","tv",1,2]);
  console.log(JSON.stringify({movie,tv,wrongEpisode}));
})().catch(e=>{console.error(e.stack||e);process.exit(1)});
'''
def execute(program,scenario="normal"):
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/"probe.cjs"
        path.write_text(program,encoding="utf-8")
        proc=subprocess.run(["node",str(path),scenario],cwd=ROOT,capture_output=True,text=True,check=True)
    return json.loads(proc.stdout.strip().splitlines()[-1])

result=execute(js)
movie=result["movie"]
tv=result["tv"]
assert len(movie)==1,movie
assert movie[0]["url"]=="https://media.workers.dev/colony.mkv",movie
assert movie[0]["quality"]=="2160p",movie
assert "The Colony" in movie[0]["title"],movie
assert len(tv)==1,tv
assert tv[0]["url"]=="https://media.workers.dev/bb-s01e01.mkv",tv
assert "S01E01" in tv[0]["title"],tv
assert result["wrongEpisode"] == [],result["wrongEpisode"]
fallback=execute(js,"title_only")
assert len(fallback["movie"])==len(fallback["tv"])==1,fallback
assert fallback["wrongEpisode"]==[],fallback
assert execute(js,"wrong_year")["movie"]==[]
assert execute(js,"wrong_movie_type")["movie"]==[]
assert execute(js,"wrong_tv_type")["tv"]==[]

# Run the same controls on the exact materialized owned runtime, catching
# publication/minification changes without treating synthetic URLs as media proof.
from provider_patch_blocks import owned_span
manifest=json.loads((ROOT/"manifest.json").read_text())
published=next(row for row in manifest["scrapers"] if row["id"].casefold()=="4khdhub")
bundle=(ROOT/published["filename"]).read_text()
start,end=owned_span(bundle,"PROVIDER.4KHDHUB.RUNTIME.V1")
assert js.count(wrapper)==1
published_js=js.replace(wrapper,bundle[start:end],1)
def semantic(rows):
    return {key:[{field:row.get(field) for field in ("url","title","quality","provider")}
                 for row in value] for key,value in rows.items()}
for scenario in ("normal","title_only","wrong_year","wrong_movie_type","wrong_tv_type"):
    assert semantic(execute(published_js,scenario))==semantic(execute(js,scenario)),scenario
src=PATCH.read_text(encoding="utf-8")
assert 'classBlocks(html,"episode-download-item")' in src
assert 'green(?:mount)?motors' in src
assert '_crawlDirectMedia([url],url,3)' in src
assert "hdhub4u" not in mod.WRAPPER.lower()
print("4KHDHub runtime behavior contract passed")
