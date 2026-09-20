#!/usr/bin/env python3
from pathlib import Path
import json
import subprocess

ROOT=Path(__file__).resolve().parents[1]
src=(ROOT/"scripts/provider_patches/uhdmovies_runtime_v1.py").read_text(encoding="utf-8")
ov=json.loads((ROOT/"provider-overrides.json").read_text(encoding="utf-8"))["provider_patches"]["uhdmovies"]
opts=ov["provider_lego_options"]["scripts/provider_patches/uhdmovies_runtime_v1.py"]
wrapper=src.split("WRAPPER = r'''",1)[1].split("'''",1)[0]
compiled=wrapper.replace("CONFIG_PLACEHOLDER",json.dumps(opts,separators=(",",":")))

harness=r'''
const calls=[];
const NIAKVIO_PROVIDER_MODEL={officialSite:"https://uhdmovies.my"};
global.__nuvioCoreGetTmdbDataV1=async()=>({metadata:{title:"Interstellar",release_date:"2014-11-05"}});
function H(map){return{get(k){return map[String(k).toLowerCase()]||""}}}
function R(status,body,url,headers){
  return{ok:status>=200&&status<300,status,url:url||"",headers:H(headers||{"content-type":"text/html"}),async text(){return String(body||"")}}
}
global.fetch=async function(url,opt){
  url=String(url);opt=opt||{};calls.push([url,String(opt.method||"GET").toUpperCase(),String(opt.body||"")]);
  if(url==="https://uhdmovies.my/?s=Interstellar") return R(200,'<article><a title="Interstellar 2014" href="https://uhdmovies.my/download-interstellar-2014/">Interstellar 2014</a></article>',url);
  if(url==="https://uhdmovies.my/download-interstellar-2014/") return R(200,'<p>Interstellar 1080p [ 2 GB ] <a href="https://cloud.unblockedgames.world/?sid=test">Cloud</a></p>',url);
  if(url==="https://cloud.unblockedgames.world/?sid=test" && String(opt.method||"GET").toUpperCase()==="GET") return R(200,'<form id="landing" action="/step1"><input name="_wp_http" value="one"></form>',url);
  if(url==="https://cloud.unblockedgames.world/step1" && String(opt.method||"GET").toUpperCase()==="POST") return R(200,'<form id="landing" action="/step2"><input name="_wp_http2" value="two"><input name="token" value="tok"></form>',url);
  if(url==="https://cloud.unblockedgames.world/step2" && String(opt.method||"GET").toUpperCase()==="POST") return R(200,'<a href="?go=gate">continue</a>',url);
  if(url==="https://cloud.unblockedgames.world/?go=gate") return R(200,'<meta http-equiv="refresh" content="0;url=https://driveseed.org/file/abc">',url);
  if(url==="https://driveseed.org/file/abc") return R(200,
    '<a href="https://cdn.video-gen.xyz/dead-token">Generic direct</a>'+
    '<a href="https://driveseed.org/resume/abc">Resume Cloud</a>',url);
  if(url==="https://driveseed.org/resume/abc") return R(200,
    '<a class="btn btn-success" href="https://healthy-worker.workers.dev/interstellar.mkv">Download</a>',url);
  return R(404,"",url);
};
''' + compiled + r'''
(async()=>{
  const hook=globalThis.__niakvioProviderRuntimeResolverV1;
  if(!hook||hook.provider!=="uhdmovies")throw new Error("UHDMovies hook missing");
  const out=await hook.resolve(["157336","movie",null,null]);
  if(!Array.isArray(out)||out.length<2)throw new Error("expected multiple terminal candidates "+JSON.stringify(out));
  if(out[0].url!=="https://healthy-worker.workers.dev/interstellar.mkv")throw new Error("explicit DriveSeed server was not prioritized "+JSON.stringify(out));
  if(!out.some(x=>x.url==="https://cdn.video-gen.xyz/dead-token"))throw new Error("generic fallback candidate should remain available to Core");
  const flat=calls.map(x=>x[0]).join("\n");
  for(const token of [
    "https://uhdmovies.my/?s=Interstellar",
    "https://cloud.unblockedgames.world/?go=gate",
    "https://driveseed.org/file/abc",
    "https://driveseed.org/resume/abc"
  ])if(!flat.includes(token))throw new Error("missing "+token+"\n"+flat);
  console.log("UHDMOVIES_BUTTON_FIRST_MULTITERMINAL_OK");
})().catch(e=>{console.error(e);process.exit(1)});
'''
subprocess.run(["node","-e",harness],check=True)
print("UHDMovies button-first multi-terminal behavior passed")
