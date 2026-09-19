#!/usr/bin/env python3
from pathlib import Path
import json
import subprocess
ROOT=Path(__file__).resolve().parents[1]
src=(ROOT/"scripts/provider_patches/vidfast_runtime_v1.py").read_text(encoding="utf-8")
over=json.loads((ROOT/"provider-overrides.json").read_text(encoding="utf-8"))
opts=over["provider_patches"]["vidfast"]["provider_lego_options"]["scripts/provider_patches/vidfast_runtime_v1.py"]
wrapper=src.split("WRAPPER = r'''",1)[1].split("'''",1)[0]
compiled=wrapper.replace("CONFIG_PLACEHOLDER",json.dumps(opts,separators=(",",":")))
harness=r'''
const calls=[];
function R(status,body,url){return{ok:status>=200&&status<300,status,url:url||"",async text(){return typeof body==="string"?body:JSON.stringify(body)},async json(){return typeof body==="string"?JSON.parse(body):body}}}
global.fetch=async function(url,opt){
 url=String(url);opt=opt||{};calls.push([url,String(opt.method||"GET").toUpperCase(),String(opt.body||"")]);
 if(url==="https://vidfast.to/embed/movie/157336")return R(200,"<html><body>embed shell without legacy token</body></html>",url);
 if(url==="https://vidfast.vc/movie/157336/")return R(200,'<script>window.__x={"en":"tok-vc"}</script>',url);
 if(url.includes("/enc-vidfast?text=tok-vc"))return R(200,{result:{servers:"https://vidfast.vc/api/server",stream:"https://vidfast.vc/api/stream",csrf:"csrf1"}},url);
 if(url==="https://vidfast.vc/api/stream")return R(200,"encrypted-servers",url);
 if(url.endsWith("/dec-vidfast")){const b=JSON.parse(String(opt.body||"{}"));if(b.text==="encrypted-servers")return R(200,{result:[{data:"srv1",name:"Main",description:"1080p"}]},url);if(b.text==="encrypted-stream")return R(200,{result:{url:"https://cdn.example/master.m3u8"}},url)}
 if(url==="https://vidfast.vc/api/server/srv1")return R(200,"encrypted-stream",url);
 return R(404,"",url);
};
'''+compiled+r'''
(async()=>{const hook=globalThis.__niakvioProviderRuntimeResolverV1;if(!hook||hook.provider!=="vidfast")throw new Error("hook missing");const out=await hook.resolve(["157336","movie",null,null]);if(!Array.isArray(out)||out.length!==1)throw new Error("expected one stream "+JSON.stringify(out));if(out[0].url!=="https://cdn.example/master.m3u8")throw new Error("wrong terminal");const urls=calls.map(x=>x[0]);if(urls[0]!=="https://vidfast.to/embed/movie/157336")throw new Error("current docs base not first");if(!urls.includes("https://vidfast.vc/movie/157336/"))throw new Error("vc fallback missing");if(!urls.some(u=>u.includes("/enc-vidfast?text=tok-vc")))throw new Error("enc-dec stage missing");console.log("VIDFAST_MULTIBASE_RUNTIME_OK")})().catch(e=>{console.error(e);process.exit(1)});
'''
subprocess.run(["node","-e",harness],check=True)
print("VidFast current-docs + upstream fallback runtime contract passed")
