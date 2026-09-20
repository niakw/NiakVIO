#!/usr/bin/env python3
from pathlib import Path
import json
import subprocess

ROOT=Path(__file__).resolve().parents[1]
src=(ROOT/"scripts/provider_patches/moviebox_vidsrcme_runtime_v1.py").read_text(encoding="utf-8")
ov=json.loads((ROOT/"provider-overrides.json").read_text(encoding="utf-8"))["provider_patches"]["moviebox"]
opts=ov["provider_lego_options"]["scripts/provider_patches/moviebox_vidsrcme_runtime_v1.py"]
wrapper=src.split("WRAPPER = r'''",1)[1].split("'''",1)[0]
compiled=wrapper.replace("CONFIG_PLACEHOLDER",json.dumps(opts,separators=(",",":")))

harness=r'''
const calls=[];
let mode="primary";
global.__nuvioCoreGetTmdbDataV1=async()=>({state:"ok",metadata:{external_ids:{imdb_id:"tt0816692"}}});
function R(status,body,url){return{ok:status>=200&&status<300,status,url:url||"",async json(){return typeof body==="string"?JSON.parse(body):body},async text(){return typeof body==="string"?body:JSON.stringify(body)}}}
global.fetch=async function(url,opt){
 url=String(url);calls.push(url);
 const isStream=url.includes("/stream/movie/tt0816692.json");
 const isAlt=url.startsWith("https://moviebox-cfa7.onrender.com/");
 const isPrimary=url.startsWith("https://pengu.uk/");
 if(isStream&&isPrimary){
   if(mode==="primary")return R(200,{streams:[{url:"https://cdn.primary/master.m3u8",title:"1080p English"}]},url);
   if(mode==="alternate")return R(429,{},url);
   return R(404,{},url);
 }
 if(isStream&&isAlt){
   if(mode==="alternate")return R(200,{streams:[{url:"https://cdn.alternate/master.m3u8",title:"1080p Hindi"}]},url);
   return R(404,{},url);
 }
 if(url.startsWith("https://vidsrcme.ru/vs_src.php"))return R(200,{src:"https://cdn.legacy/master.m3u8"},url);
 return R(404,{},url);
};
module={exports:{getStreams:async()=>[]}};
'''+compiled+r'''
(async()=>{
 const hook=globalThis.__niakvioProviderRuntimeResolverV1;
 if(!hook)throw new Error("runtime hook missing");
 let out=await hook.resolve(["157336","movie",null,null]);
 if(out.length!==1||out[0].url!=="https://cdn.primary/master.m3u8")throw new Error("primary current path failed "+JSON.stringify(out));
 if(calls.some(u=>u.startsWith("https://moviebox-cfa7.onrender.com/")))throw new Error("alternate called despite primary success");
 if(calls.some(u=>u.startsWith("https://vidsrcme.ru/")))throw new Error("legacy called despite primary success");
 mode="alternate";calls.length=0;
 out=await hook.resolve(["157336","movie",null,null]);
 if(out.length!==1||out[0].url!=="https://cdn.alternate/master.m3u8")throw new Error("alternate current path failed "+JSON.stringify(out));
 if(!calls.some(u=>u.startsWith("https://pengu.uk/")))throw new Error("primary current base not attempted before alternate");
 if(!calls.some(u=>u.startsWith("https://moviebox-cfa7.onrender.com/")))throw new Error("alternate current base not attempted");
 if(calls.some(u=>u.startsWith("https://vidsrcme.ru/")))throw new Error("legacy called despite alternate current success");
 mode="legacy";calls.length=0;
 out=await hook.resolve(["157336","movie",null,null]);
 if(out.length!==1||out[0].url!=="https://cdn.legacy/master.m3u8")throw new Error("legacy fallback failed "+JSON.stringify(out));
 if(!calls.some(u=>u.startsWith("https://pengu.uk/")))throw new Error("primary current base not attempted before legacy");
 if(!calls.some(u=>u.startsWith("https://moviebox-cfa7.onrender.com/")))throw new Error("alternate current base not attempted before legacy");
 if(!calls.some(u=>u.startsWith("https://vidsrcme.ru/vs_src.php")))throw new Error("legacy fallback not attempted");
 console.log("MOVIEBOX_MULTIBASE_CURRENT_FALLBACK_OK");
})().catch(e=>{console.error(e);process.exit(1)});
'''
subprocess.run(["node","-e",harness],check=True)
print("MovieBox current + fallback runtime behavior passed")
