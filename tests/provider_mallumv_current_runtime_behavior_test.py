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
const calls=[]; let mode="confirm";
global.__nuvioCoreGetTmdbDataV1=async()=>({state:"ok",metadata:{title:"Interstellar",release_date:"2014-11-05"}});
function R(status,body,url,headers){const map=Object.fromEntries(Object.entries(headers||{}).map(([k,v])=>[String(k).toLowerCase(),String(v)]));return{ok:status>=200&&status<300,status,url:url||"",headers:{get(k){return map[String(k).toLowerCase()]||null}},async text(){return String(body||"")},async json(){return JSON.parse(String(body||"{}"))}}}
global.fetch=async function(url,opt){
  url=String(url); calls.push(url);
  if(url==="https://mallumv.space/search.php?q=Interstellar") return R(200,'<a href="/movie/1755/Interstellar_2014_English.xhtml"><b>Interstellar 2014 English</b></a>',url);
  if(url==="https://mallumv.space/movie/1755/Interstellar_2014_English.xhtml") {
    if(mode==="confirm") return R(200,'<script>window.__download="confirm\\/1755\\/998\\/Interstellar_2014_English.xhtml";</script>',url);
    if(mode==="viking"||mode==="viking-header") return R(200,'<a href="/internal/6705/1755/Interstellar_2014_English.xhtml">1080p</a>',url);
    return R(200,'<a href="https://hubcloud.example/drive/abc123">Download 1080p</a>',url);
  }
  if(url==="https://mallumv.space/confirm/1755/998/Interstellar_2014_English.xhtml") return R(200,'<a class="touch" href="/internal/1755/998/Interstellar_2014_English.xhtml">Confirm Download</a>',url);
  if(url==="https://mallumv.space/internal/1755/998/Interstellar_2014_English.xhtml") return R(200,'<a href="https://hubcloud.example/drive/abc123">HubCloud</a>',url);
  if(url==="https://mallumv.space/internal/6705/1755/Interstellar_2014_English.xhtml") return R(200,'<a href="https://vik1ngfile.site/f/tMAohzba53">Download 1080p</a>',url);
  if(url==="https://vik1ngfile.site/f/tMAohzba53") return R(200,'<script>var canonical="https://vikingfile.com/f/tMAohzba53&quot;";</script><a href="https://vikingfile.com/fast-download/interstellar">Fast Download</a>',url);
  if(url==="https://vikingfile.com/f/tMAohzba53") return R(200,'<video controls><source src="/stream/interstellar.mkv" type="video/x-matroska"></video>',url,{"content-type":"text/html; charset=UTF-8"});
  if(url==="https://vikingfile.com/fast-download/interstellar") return mode==="viking-header"
    ? R(200,"BINARY",url,{"content-type":"application/octet-stream","content-disposition":'attachment; filename="Interstellar.2014.1080p.mkv"'})
    : R(200,'<html><body>regular landing page</body></html>',url,{"content-type":"text/html; charset=UTF-8"});
  if(url==="https://vikingfile.com/stream/interstellar.mkv") return R(200,"BINARY",url,{"content-type":"video/x-matroska"});
  if(url==="https://hubcloud.example/drive/abc123") return R(200,'<a href="/video/abc123">Continue</a>',url);
  if(url==="https://hubcloud.example/video/abc123") return R(200,'<a href="https://cdn.example/interstellar/master.mp4">Download</a>',url);
  return R(404,"",url);
};
global._crawlDirectMedia=async function(urls,ref,depth){
  calls.push("crawl:"+urls[0]);
  return [];
};
module={exports:{getStreams:async()=>[]}};
''' + compiled + r'''
(async()=>{
  const hook=globalThis.__niakvioProviderRuntimeResolverV1;
  if(!hook||hook.provider!=="mallumv")throw new Error("MalluMV hook missing");
  const out=await hook.resolve([{tmdbId:"157336",canonicalMediaType:"movie"}]);
  if(!Array.isArray(out)||out.length!==1)throw new Error("expected one stream "+JSON.stringify(out));
  if(out[0].url!=="https://cdn.example/interstellar/master.mp4")throw new Error("wrong terminal "+JSON.stringify(out[0]));
  const flat=calls.join("\n");
  for(const token of [
    "https://mallumv.space/search.php?q=Interstellar",
    "/movie/1755/Interstellar_2014_English.xhtml",
    "/confirm/1755/998/Interstellar_2014_English.xhtml",
    "/internal/1755/998/Interstellar_2014_English.xhtml",
    "https://hubcloud.example/drive/abc123",
    "https://hubcloud.example/video/abc123",
    "crawl:https://hubcloud.example/drive/abc123"
  ]) if(!flat.includes(token)) throw new Error("missing "+token+"\n"+flat);

  calls.length=0; mode="direct";
  const directOut=await hook.resolve([{tmdbId:"157336",canonicalMediaType:"movie"}]);
  if(!Array.isArray(directOut)||directOut.length!==1||directOut[0].url!=="https://cdn.example/interstellar/master.mp4")throw new Error("detail-terminal fallback failed "+JSON.stringify(directOut));
  const directFlat=calls.join("\n");
  for(const token of ["https://mallumv.space/movie/1755/Interstellar_2014_English.xhtml","https://hubcloud.example/drive/abc123","https://hubcloud.example/video/abc123"]) if(!directFlat.includes(token)) throw new Error("missing direct-detail "+token+"\n"+directFlat);
  if(directFlat.includes("/confirm/")||directFlat.includes("/internal/"))throw new Error("direct detail fallback unexpectedly required confirm/internal\n"+directFlat);

  calls.length=0; mode="viking";
  const vikingOut=await hook.resolve([{tmdbId:"157336",canonicalMediaType:"movie"}]);
  if(!Array.isArray(vikingOut)||vikingOut.length!==1)throw new Error("expected VikingFile terminal "+JSON.stringify(vikingOut));
  if(vikingOut[0].url!=="https://vikingfile.com/stream/interstellar.mkv"||vikingOut[0].isDirect!==true)throw new Error("wrong VikingFile terminal "+JSON.stringify(vikingOut[0]));
  const vikingFlat=calls.join("\n");
  for(const token of ["/internal/6705/1755/Interstellar_2014_English.xhtml","https://vik1ngfile.site/f/tMAohzba53","https://vikingfile.com/f/tMAohzba53"]) if(!vikingFlat.includes(token)) throw new Error("missing viking "+token+"\n"+vikingFlat);
  if(vikingFlat.includes("https://vikingfile.com/fast-download/interstellar"))throw new Error("canonical VikingFile route must outrank dead fast-download landing\n"+vikingFlat);
  if(vikingFlat.includes("https://vikingfile.com/stream/interstellar.mkv"))throw new Error("direct discovered VikingFile media should not be refetched by provider runtime\n"+vikingFlat);
  if(vikingFlat.includes("&quot;"))throw new Error("HTML entity leaked into VikingFile request\n"+vikingFlat);
  if(vikingFlat.includes("/confirm/"))throw new Error("VikingFile live-shape unexpectedly required confirm\n"+vikingFlat);

  calls.length=0; mode="viking-header";
  const headerOut=await hook.resolve([{tmdbId:"157336",canonicalMediaType:"movie"}]);
  if(!Array.isArray(headerOut)||headerOut.length!==1||headerOut[0].url!=="https://vikingfile.com/fast-download/interstellar"||headerOut[0].isDirect!==true)throw new Error("VikingFile response-header terminal failed "+JSON.stringify(headerOut));

  console.log("MALLUMV_CURRENT_RUNTIME_OK");
})().catch(e=>{console.error(e);process.exit(1)});
'''
subprocess.run(["node","-e",harness],check=True)
print("MalluMV current catalogue -> terminal runtime behavior passed")
