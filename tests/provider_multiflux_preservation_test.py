#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_node(bundle: str, body: str) -> dict:
    with tempfile.TemporaryDirectory(prefix="niakvio-multiflux-") as tmp:
        tmp_path = Path(tmp)
        provider = tmp_path / "provider.cjs"
        runner = tmp_path / "runner.cjs"
        provider.write_text(bundle, encoding="utf-8")
        runner.write_text(body, encoding="utf-8")
        result = subprocess.run(
            ["node", str(runner), str(provider)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        return json.loads(result.stdout.strip().splitlines()[-1])


streamzo = load_module("streamzo_runtime_multiflux", ROOT / "scripts/provider_patches/streamzo_runtime_v1.py")
streamzo_bundle = streamzo.apply("module.exports={};\n", options={"base": "https://streamzo.test"})

streamzo_runner = r"""
const fs=require("fs"),vm=require("vm");
global.module={exports:{}};global.exports=global.module.exports;
const source=fs.readFileSync(process.argv[2],"utf8");
global.__nuvioCoreGetTmdbDataV1=async()=>({metadata:{name:"Example Show",first_air_date:"2026-01-01"}});
global._crawlDirectMedia=async function(urls){return (urls||[]).map(url=>({url}));};
function response(url,value,json=false){return{ok:true,status:200,url,headers:{get:()=>json?"application/json":"text/html"},json:async()=>value,text:async()=>json?JSON.stringify(value):String(value)}}
global.fetch=async function(url){
 url=String(url);
 if(url.includes("/api/web/suggest"))return response(url,{suggestions:[{href:"/example-show",titre:"Example Show",content_type:"series",year:2026,resolution:"1080p"}]},true);
 if(url==="https://streamzo.test/example-show")return response(url,
   '<button class="sd-ep" data-season="1" data-ep="1" data-lang="vf" data-src="/embed/a" data-player="Lecteur 1">'+
   '<button class="sd-ep" data-season="1" data-ep="1" data-lang="vf" data-src="/embed/b" data-player="Lecteur 2">'+
   '<button class="sd-ep" data-season="1" data-ep="1" data-lang="vf" data-src="/embed/c" data-player="Lecteur 3">');
 if(url.endsWith("/embed/a"))return response(url,'https://cdn.example/a/master.m3u8');
 if(url.endsWith("/embed/b"))return response(url,'https://cdn.example/b/master.m3u8');
 if(url.endsWith("/embed/c"))return response(url,'https://cdn.example/c/master.m3u8');
 throw new Error("unexpected "+url);
};
vm.runInThisContext(source,{filename:"streamzo.cjs"});
(async()=>{
 const resolver=global.__niakvioProviderRuntimeResolverV1;
 if(!resolver||resolver.provider!=="streamzo")throw new Error("streamzo resolver missing");
 const rows=await resolver.resolve([{tmdbId:"123",mediaType:"tv",season:1,episode:1}],{});
 console.log(JSON.stringify({count:rows.length,urls:rows.map(r=>r.url),players:rows.map(r=>r.player),languages:rows.map(r=>r.language)}));
})().catch(e=>{console.error(e);process.exit(1)});
"""
streamzo_result = run_node(streamzo_bundle, streamzo_runner)
assert streamzo_result["count"] == 3, streamzo_result
assert len(set(streamzo_result["urls"])) == 3, streamzo_result
assert streamzo_result["players"] == ["Lecteur 1", "Lecteur 2", "Lecteur 3"], streamzo_result
assert streamzo_result["languages"] == ["VF", "VF", "VF"], streamzo_result

papadustream = load_module("papadustream_runtime_multiflux", ROOT / "scripts/provider_patches/papadustream_site_runtime_v1.py")
papa_bundle = papadustream.apply("module.exports={};\n", options={"base": "https://papa.test"})
papa_runner = r"""
const fs=require("fs"),vm=require("vm");
global.module={exports:{}};global.exports=global.module.exports;
const source=fs.readFileSync(process.argv[2],"utf8");
global.__nuvioCoreGetTmdbDataV1=async()=>({metadata:{title:"Example Movie"}});
global._crawlDirectMedia=async function(urls){
 return (urls||[]).map((url,i)=>({url:"https://cdn.example/"+encodeURIComponent(new URL(url).hostname)+"/"+i+".m3u8"}));
};
function response(url,body){return{ok:true,status:200,url,headers:{get:()=>"text/html"},text:async()=>body}}
global.fetch=async function(url){
 url=String(url);
 if(url.includes("/search/Example%20Movie/"))return response(url,'<a href="/movie/example-movie">Example Movie</a>');
 if(url.includes("/movie/example-movie"))return response(url,
   '<h1>Example Movie</h1> "link":"https://filemoon.test/e/1" "link":"https://vidzy.test/e/2" "link":"https://uqload.test/e/3" '+
   '"link":"https://doply.test/e/4" "link":"https://sandratableother.test/e/5" "link":"https://multiup.test/e/6"');
 throw new Error("unexpected "+url);
};
vm.runInThisContext(source,{filename:"papa.cjs"});
(async()=>{
 const resolver=global.__niakvioProviderRuntimeResolverV1;
 if(!resolver||resolver.provider!=="papadustream")throw new Error("papa resolver missing");
 const rows=await resolver.resolve([{tmdbId:"456",mediaType:"movie"}],{});
 console.log(JSON.stringify({count:rows.length,urls:rows.map(r=>r.url),players:rows.map(r=>r.player)}));
})().catch(e=>{console.error(e);process.exit(1)});
"""
papa_result = run_node(papa_bundle, papa_runner)
assert papa_result["count"] == 6, papa_result
assert len(set(papa_result["urls"])) == 6, papa_result
assert all(papa_result["players"]), papa_result

print("provider multiflux preservation passed: StreamZo same-language fanout + PapaDuStream multi-player fanout")
