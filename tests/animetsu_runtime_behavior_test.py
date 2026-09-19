#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
PATCH=ROOT/"scripts/provider_patches/animetsu_runtime_v1.py"
spec=importlib.util.spec_from_file_location("niakvio_animetsu_runtime_test",PATCH)
assert spec and spec.loader
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

cfg={
    "api":"https://animetsu.live/v2/api",
    "site":"https://animetsu.live",
    "proxy":"https://swiftstream.top/proxy",
    "servers":["kite","dio"],
    "sourceTypes":["sub","dub"],
    "maxStreams":8,
    "ua":"NiakVIO-Test",
}
wrapper=mod.WRAPPER.replace("CONFIG_PLACEHOLDER",json.dumps(cfg,separators=(",",":")))
js=r'''
"use strict";
let providerFetches=0;
globalThis.__nuvioCoreGetTmdbDataV1=async({tmdbId})=>{
  if(String(tmdbId)==="95479") return {metadata:{
    name:"Jujutsu Kaisen",
    original_name:"呪術廻戦",
    first_air_date:"2020-10-03",
    original_language:"ja",
    genres:[{id:16,name:"Animation"},{id:10765,name:"Sci-Fi & Fantasy"}],
    seasons:[{season_number:1,episode_count:24}]
  }};
  return {metadata:{
    name:"Breaking Bad",
    first_air_date:"2008-01-20",
    original_language:"en",
    genres:[{id:18,name:"Drama"}],
    seasons:[{season_number:1,episode_count:7}]
  }};
};
function response(url,obj){return {ok:true,status:200,url,async text(){return JSON.stringify(obj)}}}
globalThis.fetch=async function(url){
  url=String(url);
  if(url.includes("animetsu.live")) providerFetches++;
  if(url.includes("/anime/search/?query=Jujutsu%20Kaisen")) return response(url,{results:[
    {id:"jjk-2020",year:2020,title:{english:"Jujutsu Kaisen",romaji:"Jujutsu Kaisen"}},
    {id:"wrong",year:2010,title:{english:"Jujutsu Something",romaji:"Jujutsu Something"}}
  ]});
  if(url.includes("/anime/oppai/jjk-2020/1?server=kite&source_type=sub")) return response(url,{sources:[
    {url:"?url=https%3A%2F%2Ffetch.nexabloom.top%2Fjjk%2Fmaster.m3u8",quality:"1080p"}
  ]});
  if(url.includes("/anime/oppai/jjk-2020/1?server=kite&source_type=dub")) return response(url,{sources:[]});
  if(url.includes("/anime/oppai/jjk-2020/1?server=dio&source_type=sub")) return response(url,{sources:[]});
  if(url.includes("/anime/oppai/jjk-2020/1?server=dio&source_type=dub")) return response(url,{sources:[]});
  throw new Error("unexpected fetch "+url);
};
''' + wrapper + r'''
(async()=>{
  const hook=globalThis.__niakvioProviderRuntimeResolverV1;
  if(!hook||hook.provider!=="animetsu") throw new Error("hook missing");
  const anime=await hook.resolve([{tmdbId:"95479",canonicalMediaType:"anime",mediaType:"tv",season:1,episode:1}]);
  const before=providerFetches;
  const live=await hook.resolve([{tmdbId:"1396",canonicalMediaType:"tv",mediaType:"tv",season:1,episode:1}]);
  console.log(JSON.stringify({anime,live,before,after:providerFetches}));
})().catch(e=>{console.error(e.stack||e);process.exit(1)});
'''
with tempfile.TemporaryDirectory() as td:
    p=Path(td)/"probe.cjs"
    p.write_text(js,encoding="utf-8")
    proc=subprocess.run(["node",str(p)],cwd=ROOT,capture_output=True,text=True,check=True)
result=json.loads(proc.stdout.strip().splitlines()[-1])
anime=result["anime"]
assert len(anime)==1,anime
assert anime[0]["provider"]=="animetsu",anime
assert anime[0]["language"]=="VOSTA",anime
assert anime[0]["quality"]=="1080p",anime
assert anime[0]["url"].startswith("https://swiftstream.top/proxy?url="),anime
assert result["live"]==[],result
assert result["after"]==result["before"],"live-action reached provider network"

src=PATCH.read_text(encoding="utf-8")
for token in (
    "NIAKVIO_ANIMETSU_RUNTIME_V1",
    '"/anime/search/?query="',
    '"/anime/oppai/"',
    '"?server="',
    '"&source_type="',
    '"kite","dio"',
    '"sub","dub"',
    "https://swiftstream.top/proxy",
    '__niakvioProviderRuntimeResolverV1={provider:"animetsu",resolve:resolve}',
):
    assert token in src,token

ov=json.loads((ROOT/"provider-overrides.json").read_text(encoding="utf-8"))["provider_patches"]["animetsu"]
lego="scripts/provider_patches/animetsu_runtime_v1.py"
assert ov["provider_lego_scripts"]==[lego]
assert ov["provider_lego_options"][lego]["servers"]==["kite","dio"]
assert ov["provider_lego_options"][lego]["sourceTypes"]==["sub","dub"]
assert ov["repair_disposition"]["requiredLanes"]==["anime"]
print("Animetsu current API behavior contract passed")
