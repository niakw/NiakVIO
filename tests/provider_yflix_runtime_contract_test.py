#!/usr/bin/env python3
from pathlib import Path
import json
import subprocess

ROOT=Path(__file__).resolve().parents[1]
src=(ROOT/"scripts/provider_patches/yflix_runtime_v1.py").read_text(encoding="utf-8")
ov=json.loads((ROOT/"provider-overrides.json").read_text(encoding="utf-8"))["provider_patches"]["yflix"]
lego="scripts/provider_patches/yflix_runtime_v1.py"

for token in (
    "NIAKVIO_YFLIX_RUNTIME_V1",
    "/find?tmdb_id=",
    "/enc-movies-flix?text=",
    "/episodes/list?id=",
    "/links/list?eid=",
    "/links/view?id=",
    "/dec-movies-flix",
    "/dec-rapid",
    "rapidshare.cc",
    '__niakvioProviderRuntimeResolverV1={provider:"yflix",resolve:resolve}',
):
    assert token in src, token
assert ov["provider_lego_scripts"]==[lego]
assert "api_recipe" not in ov and "candidate_api_recipe" not in ov
opts=ov["provider_lego_options"][lego]
assert opts["db"]=="https://enc-dec.app/db/flix"
assert opts["api"]=="https://enc-dec.app/api"
assert opts["ajaxBases"][0]=="https://yflix.to/ajax"
assert "https://1moviesz.to/ajax" in opts["ajaxBases"]
assert "https://1movies.bz/ajax" in opts["ajaxBases"]
assert ov["published_types"]==["movie","tv"]

wrapper=src.split("WRAPPER = r'''",1)[1].split("'''",1)[0]
cfg=json.dumps(opts,separators=(",",":"))
compiled=wrapper.replace("CONFIG_PLACEHOLDER",cfg)

harness=r'''
const calls=[];
global.fetch=async function(url,opt){
  url=String(url); opt=opt||{}; calls.push([url,String(opt.method||"GET").toUpperCase(),String(opt.body||"")]);
  function R(status,obj){return {ok:status>=200&&status<300,status,headers:{get(){return "application/json"}},async json(){return obj},async text(){return JSON.stringify(obj)}}}
  if(url.includes("/db/flix/find?tmdb_id=157336")) return R(200,[{info:{flix_id:"c1",title_en:"Interstellar"},episodes:{"1":{"1":{eid:"e1"}}}}]);
  if(url.includes("/api/enc-movies-flix?text=e1")) return R(200,{result:"enc-e1"});
  if(url.includes("/ajax/links/list?eid=e1")) return R(200,{result:"SERVERS_HTML"});
  if(url.endsWith("/api/parse-html") && String(opt.body).includes("SERVERS_HTML")) return R(200,{result:{rapid:{main:{lid:"l1"}}}});
  if(url.includes("/api/enc-movies-flix?text=l1")) return R(200,{result:"enc-l1"});
  if(url.includes("/ajax/links/view?id=l1")) return R(200,{result:"cipher1"});
  if(url.endsWith("/api/dec-movies-flix")) return R(200,{result:{url:"https://rapidshare.cc/e/abc"}});
  if(url==="https://rapidshare.cc/media/abc") return R(200,{result:"rapid-cipher"});
  if(url.endsWith("/api/dec-rapid")) return R(200,{result:{sources:[{file:"https://cdn.example/master.m3u8"}],tracks:[]}});
  return R(404,{});
};
''' + compiled + r'''
(async()=>{
 const hook=globalThis.__niakvioProviderRuntimeResolverV1;
 if(!hook||hook.provider!=="yflix") throw new Error("hook missing");
 const out=await hook.resolve(["157336","movie",null,null]);
 if(!Array.isArray(out)||out.length!==1) throw new Error("expected one stream: "+JSON.stringify(out));
 if(out[0].url!=="https://cdn.example/master.m3u8") throw new Error("terminal mismatch");
 const flat=calls.map(x=>x[0]).join("\n");
 for(const token of ["/db/flix/find?tmdb_id=157336","/ajax/links/list?eid=e1","/ajax/links/view?id=l1","/api/dec-movies-flix","rapidshare.cc/media/abc","/api/dec-rapid"]){
   if(!flat.includes(token)) throw new Error("missing call "+token+"\n"+flat);
 }
 console.log("YFLIX_RUNTIME_BEHAVIOR_OK");
})().catch(e=>{console.error(e);process.exit(1)});
'''
subprocess.run(["node","-e",harness],check=True)
print("YFlix current encrypted AJAX runtime contract passed")
