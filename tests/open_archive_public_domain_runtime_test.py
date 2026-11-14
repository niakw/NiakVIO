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
sys.path.insert(0,str(ROOT/"scripts"/"provider_patches"))
path=ROOT/"scripts/provider_patches/internet_archive_public_domain_runtime_v1.py"
spec=importlib.util.spec_from_file_location("internet_archive_public_domain_runtime_v1",path)
assert spec and spec.loader
mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)

source=mod.apply(
    "module.exports={getStreams:async()=>[]};\n",
    options={"base":"https://archive.org","provider":"internet-archive","name":"Internet Archive — Public Domain","max_streams":3},
)
assert mod.MARKER in source
assert source==mod.apply(source,options={"base":"https://archive.org","provider":"internet-archive","name":"Internet Archive — Public Domain","max_streams":3})
try:
    mod.apply("module.exports={};",options={"base":"https://example.invalid"})
except ValueError:
    pass
else:
    raise AssertionError("non-archive origin accepted")

node=r'''
let metadataPublic=true;
const calls=[];
globalThis.fetch=async function(url){
  calls.push(String(url));
  if(!String(url).startsWith("https://archive.org/")) throw new Error("unexpected origin");
  if(String(url).includes("/advancedsearch.php")){
    return {ok:true,json:async()=>({response:{docs:[{
      identifier:"plan-9-from-outer-space",title:"Plan 9 from Outer Space",date:"1959",
      licenseurl:"https://creativecommons.org/publicdomain/mark/1.0/"
    }]}})};
  }
  if(String(url).includes("/metadata/")){
    return {ok:true,json:async()=>({
      metadata:{title:"Plan 9 from Outer Space",date:"1959",
        licenseurl:metadataPublic?"https://creativecommons.org/publicdomain/mark/1.0/":"https://creativecommons.org/licenses/by/4.0/"},
      files:[
        {name:"Plan9_1080.mp4",format:"MPEG4",height:1080,size:"900000000"},
        {name:"Plan9_512kb.mp4",format:"MPEG4",height:480,size:"150000000"},
        {name:"Plan9.srt",format:"SubRip",size:"1000"}
      ]
    })};
  }
  throw new Error("unexpected URL "+url);
};
'''+source+r'''
(async()=>{
  const hook=globalThis.__niakvioProviderRuntimeResolverV1;
  if(!hook||hook.provider!=="internet-archive")throw new Error("resolver not registered");
  const good=await hook.resolve([{tmdbId:"10513",canonicalMediaType:"movie",title:"Plan 9 from Outer Space",year:1957}]);
  if(!Array.isArray(good)||good.length!==2)throw new Error("expected two direct public-domain rows: "+JSON.stringify(good));
  if(good[0].quality!=="1080p"||good[0].sourceTitle!=="Plan 9 from Outer Space")throw new Error(JSON.stringify(good[0]));
  if(!good.every(x=>x.url.startsWith("https://archive.org/download/plan-9-from-outer-space/")))throw new Error(JSON.stringify(good));
  const wrong=await hook.resolve([{tmdbId:"10513",canonicalMediaType:"movie",title:"Different Movie",year:1957}]);
  if(wrong.length!==0)throw new Error("wrong title accepted");
  metadataPublic=false;
  const denied=await hook.resolve([{tmdbId:"10513",canonicalMediaType:"movie",title:"Plan 9 from Outer Space",year:1957}]);
  if(denied.length!==0)throw new Error("non-public-domain metadata accepted");
  const tv=await hook.resolve([{tmdbId:"1",canonicalMediaType:"tv",title:"Example",year:1957}]);
  if(tv.length!==0)throw new Error("TV lane accepted");
  if(calls.some(x=>!x.startsWith("https://archive.org/")))throw new Error("origin escape");
  console.log("OPEN_ARCHIVE_PUBLIC_DOMAIN_RUNTIME_OK calls="+calls.length);
})().catch(e=>{console.error(e);process.exit(1)});
'''
with tempfile.NamedTemporaryFile("w",suffix=".js",delete=False,encoding="utf-8") as fh:
    fh.write(node); temp=Path(fh.name)
try:
    subprocess.run(["node",str(temp)],cwd=ROOT,check=True)
finally:
    temp.unlink(missing_ok=True)

print("Open archive public-domain runtime contract passed")
