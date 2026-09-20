#!/usr/bin/env python3
from pathlib import Path
import json
import subprocess

ROOT=Path(__file__).resolve().parents[1]
src=(ROOT/"scripts/provider_patches/mallumv_runtime_v1.py").read_text(encoding="utf-8")
ov=json.loads((ROOT/"provider-overrides.json").read_text(encoding="utf-8"))["provider_patches"]["mallumv"]
opts=ov["provider_lego_options"]["scripts/provider_patches/mallumv_runtime_v1.py"]
wrapper=src.split("WRAPPER = r'''",1)[1].split("'''",1)[0]
compiled=wrapper.replace("CONFIG_PLACEHOLDER",json.dumps(opts,separators=(",",":")))

harness=r'''
const calls=[];
global.__nuvioCoreGetTmdbDataV1=async()=>({state:"ok",metadata:{title:"Interstellar",release_date:"2014-11-05"}});
function R(status,body,url){return{ok:status>=200&&status<300,status,url:url||"",async text(){return String(body||"")},async json(){return JSON.parse(String(body||"{}"))}}}
global.fetch=async function(url,opt){
  url=String(url); calls.push(url);
  if(url==="https://mallumv.space/search.php?q=Interstellar") return R(200,'<a href="/movie/1755/Interstellar_2014_English.xhtml"><b>Interstellar 2014 English</b></a>',url);
  if(url==="https://mallumv.space/movie/1755/Interstellar_2014_English.xhtml") return R(200,'<a href="/confirm/1755/998/Interstellar_2014_English.xhtml">Download 1080p</a>',url);
  if(url==="https://mallumv.space/confirm/1755/998/Interstellar_2014_English.xhtml") return R(200,'<a class="touch" href="/internal/1755/998/Interstellar_2014_English.xhtml">Confirm Download</a>',url);
  if(url==="https://mallumv.space/internal/1755/998/Interstellar_2014_English.xhtml") return R(200,'<a href="https://hubcloud.example/video/abc123">HubCloud</a>',url);
  return R(404,"",url);
};
global._crawlDirectMedia=async function(urls,ref,depth){
  calls.push("crawl:"+urls[0]);
  if(urls[0]==="https://hubcloud.example/video/abc123") return [{url:"https://cdn.example/interstellar/master.m3u8",quality:"1080p"}];
  return [];
};
module={exports:{getStreams:async()=>[]}};
''' + compiled + r'''
(async()=>{
  const hook=globalThis.__niakvioProviderRuntimeResolverV1;
  if(!hook||hook.provider!=="mallumv")throw new Error("MalluMV hook missing");
  const out=await hook.resolve([{tmdbId:"157336",canonicalMediaType:"movie"}]);
  if(!Array.isArray(out)||out.length!==1)throw new Error("expected one stream "+JSON.stringify(out));
  if(out[0].url!=="https://cdn.example/interstellar/master.m3u8")throw new Error("wrong terminal "+JSON.stringify(out[0]));
  const flat=calls.join("\n");
  for(const token of [
    "https://mallumv.space/search.php?q=Interstellar",
    "/movie/1755/Interstellar_2014_English.xhtml",
    "/confirm/1755/998/Interstellar_2014_English.xhtml",
    "/internal/1755/998/Interstellar_2014_English.xhtml",
    "crawl:https://hubcloud.example/video/abc123"
  ]) if(!flat.includes(token)) throw new Error("missing "+token+"\n"+flat);
  console.log("MALLUMV_CURRENT_RUNTIME_OK");
})().catch(e=>{console.error(e);process.exit(1)});
'''
subprocess.run(["node","-e",harness],check=True)
print("MalluMV current catalogue -> terminal runtime behavior passed")
