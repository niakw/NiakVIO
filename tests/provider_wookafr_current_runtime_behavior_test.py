#!/usr/bin/env python3
from pathlib import Path
import json
import subprocess

ROOT=Path(__file__).resolve().parents[1]
src=(ROOT/"scripts/provider_patches/wookafr_current_runtime_v2.py").read_text(encoding="utf-8")
ov=json.loads((ROOT/"provider-overrides.json").read_text(encoding="utf-8"))["provider_patches"]["wookafr"]
opts=ov["provider_lego_options"]["scripts/provider_patches/wookafr_current_runtime_v2.py"]
wrapper=src.split("WRAPPER = r'''",1)[1].split("'''",1)[0]
compiled=wrapper.replace("CONFIG_PLACEHOLDER",json.dumps(opts,separators=(",",":")))

harness=r'''
const calls=[];
global.__nuvioCoreGetTmdbDataV1=async function(q){
  if(q.mediaType==="tv") return {state:"ok",metadata:{name:"Breaking Bad",first_air_date:"2008-01-20"}};
  return {state:"ok",metadata:{title:"Inception",release_date:"2010-07-16"}};
};
function R(status,body,url){return{ok:status>=200&&status<300,status,url:url||"",async text(){return String(body||"")},async json(){return JSON.parse(String(body||"{}"))}}}
global.fetch=async function(url,opt){
  url=String(url);calls.push(url);
  if(url==="https://wookafr.boston/?s=Inception") return R(200,'<a href="/streaming/aventure/inception/">Inception 2010</a>',url);
  if(url==="https://wookafr.boston/streaming/aventure/inception/") return R(200,'<iframe src="https://lecteurvideo.com/embed.php?id=dead"></iframe><iframe data-src="https://vidmoly.example/e/live"></iframe>',url);
  if(url==="https://wookafr.boston/?s=Breaking%20Bad") return R(200,'<a href="/streaming/series/breaking-bad/">Breaking Bad 2008 série</a>',url);
  if(url==="https://wookafr.boston/streaming/series/breaking-bad/") return R(200,'<a href="/streaming/episodes/breaking-bad-saison-1-episode-1/">Saison 1 Episode 1</a>',url);
  if(url==="https://wookafr.boston/streaming/episodes/breaking-bad-saison-1-episode-1/") return R(200,'<iframe src="https://vidzy.live/e/bb1"></iframe>',url);
  return R(404,"",url);
};
global._crawlDirectMedia=async function(urls,ref,depth){
  const u=String(urls[0]||"");calls.push("crawl:"+u);
  if(u.startsWith("https://lecteurvideo.com/")) return [];
  if(u==="https://vidmoly.example/e/live") return [{url:"https://cdn.example/inception/master.m3u8",quality:"1080p"}];
  if(u==="https://vidzy.live/e/bb1") return [{url:"https://cdn.example/breakingbad/s1e1.m3u8",quality:"720p"}];
  return [];
};
module={exports:{getStreams:async()=>[]}};
''' + compiled + r'''
(async()=>{
  const hook=globalThis.__niakvioProviderRuntimeResolverV1;
  if(!hook||hook.provider!=="wookafr") throw new Error("Wooka hook missing");
  let out=await hook.resolve([{tmdbId:"27205",canonicalMediaType:"movie"}]);
  if(!Array.isArray(out)||out.length!==1||out[0].url!=="https://cdn.example/inception/master.m3u8") throw new Error("movie fallback failed "+JSON.stringify(out));
  let flat=calls.join("\n");
  if(!flat.includes("crawl:https://lecteurvideo.com/embed.php?id=dead")) throw new Error("lecteurvideo was not attempted");
  if(!flat.includes("crawl:https://vidmoly.example/e/live")) throw new Error("later player starved after lecteurvideo failure");
  calls.length=0;
  out=await hook.resolve([{tmdbId:"1396",canonicalMediaType:"tv",season:1,episode:1}]);
  if(!Array.isArray(out)||out.length!==1||out[0].url!=="https://cdn.example/breakingbad/s1e1.m3u8") throw new Error("tv episode chain failed "+JSON.stringify(out));
  flat=calls.join("\n");
  for(const token of ["/streaming/series/breaking-bad/","/streaming/episodes/breaking-bad-saison-1-episode-1/","crawl:https://vidzy.live/e/bb1"]) if(!flat.includes(token)) throw new Error("missing "+token+"\n"+flat);
  console.log("WOOKAFR_CURRENT_MULTIPLAYER_OK");
})().catch(e=>{console.error(e);process.exit(1)});
'''
subprocess.run(["node","-e",harness],check=True)
print("Wooka current multi-player runtime behavior passed")
