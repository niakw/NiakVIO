#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
script = ROOT / "scripts" / "provider_patches" / "adaptive_runtime_recovery_v5.py"
spec = importlib.util.spec_from_file_location("adaptive_request_recipe_v5", script)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)

options = {
    "provider_name": "Recipe Demo",
    "base_url": "https://demo.example",
    "types": ["movie"],
    "request_recipes": [{
        "route": "/engine/ajax/search.php",
        "origin": "https://demo.example",
        "role": "search",
        "method": "POST",
        "bodyKind": "form",
        "body": {"query": "{query}", "page": "1"},
        "headerNames": ["accept", "accept-language", "content-type", "referer", "origin", "user-agent"],
        "response": "html-or-text",
        "semanticType": "movie",
        "streamProof": True,
        "executable": True,
        "source": "provider-experience",
    }],
    "search_paths": [],
    "direct_paths": [],
    "max_pages": 8,
    "max_embeds": 8,
    "max_depth": 4,
    "user_agent": "NiakVIO-Recipe-Test/1.0",
}
source = module.apply(
    'module.exports={getStreams:async function(){return []}};\n',
    options=options,
)
assert "NUVIO_VERIFIED_MEDIA_RUNTIME_RECOVERY_V5" in source
assert "function requestRecipe(" in source
assert '"method":"POST"' in source
assert '"bodyKind":"form"' in source

runner = r"""
const vm=require('vm');
const src=process.argv[2],calls=[];
function H(type){return {get:(key)=>{key=String(key).toLowerCase();if(key==='content-type')return type;if(key==='content-disposition')return null;if(key==='set-cookie')return null;return null},getSetCookie:()=>[]}}
function R(url,type,body){return {ok:true,status:200,url,headers:H(type),text:async()=>String(body||''),json:async()=>JSON.parse(String(body||'{}'))}}
const sandbox={
  module:{exports:{}},exports:{},URL,AbortController,setTimeout,clearTimeout,Uint8Array,
  fetch:async(input,init={})=>{
    const url=String(input),method=String(init.method||'GET').toUpperCase(),body=String(init.body||'');
    calls.push({url,method,body,headers:init.headers||{}});
    if(url==='https://demo.example/engine/ajax/search.php'){
      if(method!=='POST') throw new Error('search was not POST');
      if(body!=='query=Fixture%20Movie&page=1') throw new Error('unexpected form body '+body);
      return R(url,'text/html; charset=utf-8','<a href="/player/42">Fixture Movie 2020</a>');
    }
    if(url==='https://demo.example/player/42'){
      return R(url,'text/html; charset=utf-8','<script>var player={file:"https://cdn.example/master.m3u8"};</script>');
    }
    if(url==='https://cdn.example/master.m3u8'){
      return R(url,'application/vnd.apple.mpegurl','#EXTM3U\n#EXT-X-TARGETDURATION:6\n#EXTINF:6,\nseg.ts\n#EXT-X-ENDLIST\n');
    }
    throw new Error('unexpected '+method+' '+url);
  }
};
sandbox.globalThis=sandbox;
vm.runInNewContext(src,sandbox,{timeout:5000});
sandbox.module.exports.getStreams({
  tmdbId:'1',mediaType:'movie',title:'Fixture Movie',year:2020
}).then(rows=>console.log(JSON.stringify({rows,calls}))).catch(err=>{console.error(err);process.exit(1)});
"""

with tempfile.TemporaryDirectory() as directory:
    runner_path = Path(directory) / "request-recipe.cjs"
    runner_path.write_text(runner, encoding="utf-8")
    result = subprocess.run(
        ["node", str(runner_path), source],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=25,
    )
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout.strip())

assert len(data["rows"]) == 1, data
assert data["rows"][0]["url"] == "https://cdn.example/master.m3u8", data
assert data["rows"][0]["isDirect"] is True, data

search_calls = [row for row in data["calls"] if row["url"] == "https://demo.example/engine/ajax/search.php"]
assert len(search_calls) == 1, data
assert search_calls[0]["method"] == "POST", data
assert search_calls[0]["body"] == "query=Fixture%20Movie&page=1", data
assert search_calls[0]["headers"]["Content-Type"] == "application/x-www-form-urlencoded", data
assert search_calls[0]["headers"]["User-Agent"] == "NiakVIO-Recipe-Test/1.0", data
assert any(row["url"] == "https://demo.example/player/42" for row in data["calls"]), data
assert any(row["url"] == "https://cdn.example/master.m3u8" for row in data["calls"]), data

print("adaptive request recipe behavior test passed")
