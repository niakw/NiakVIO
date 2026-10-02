#!/usr/bin/env python3
from __future__ import annotations
import importlib.util
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

runtime = load(ROOT / "scripts" / "adaptive_runtime" / "runtime_repair.py", "contract_probe_runtime")
generator = load(ROOT / "scripts" / "adaptive_runtime" / "runtime_recovery_generator.py", "contract_probe_generator")
options = {
    "provider_name": "Demo",
    "base_url": "https://demo.example",
    "types": ["movie"],
    "search_paths": [],
    "direct_paths": ["/film/{slug}"],
    "request_recipes": [],
    "contract_probes": [{
        "origin": "https://demo.example",
        "route": "/wp-json/demo/v1/resolve",
        "role": "player-resolver",
        "requestKeys": ["tmdb", "type", "year", "pid"],
        "methodCandidates": ["POST", "GET"],
        "bodyKindCandidates": ["form", "json"],
        "proofAuthority": False,
        "executionAuthority": False,
        "executable": False,
        "source": "current-structure-observation",
    }],
    "max_pages": 8, "max_embeds": 20, "max_depth": 4,
    "max_recipe_passes": 3, "timeout_ms": 5000,
}
source = generator.apply('module.exports={getStreams:async function(){return []}};\n', options=options)
assert "987" not in source
assert '"contractProbes"' in source
assert '"executable":false' in source

runner = r"""
const vm=require('vm');const src=process.argv[2],calls=[];
function H(type){return {get:(key)=>{key=String(key).toLowerCase();if(key==='content-type')return type;if(key==='content-length'||key==='content-disposition'||key==='set-cookie')return null;return null},getSetCookie:()=>[]}}
function R(url,type,body,status=200){return {ok:status>=200&&status<300,status,url,headers:H(type),clone(){return R(url,type,body,status)},text:async()=>String(body||''),json:async()=>JSON.parse(String(body||'{}'))}}
const detail='<div data-player="{&quot;rest&quot;:&quot;https:\\/\\/demo.example\\/wp-json\\/demo\\/v1\\/resolve&quot;,&quot;params&quot;:{&quot;tmdb&quot;:101,&quot;type&quot;:&quot;movie&quot;,&quot;year&quot;:&quot;2020&quot;,&quot;pid&quot;:987}}"></div>';
const sandbox={module:{exports:{}},exports:{},URL,URLSearchParams,AbortController,setTimeout,clearTimeout,Uint8Array,TMDB_API_KEY:'fixture',
fetch:async(input,init={})=>{const url=String(input),method=String(init.method||'GET').toUpperCase(),body=String(init.body||'');calls.push({url,method,body});
if(url.startsWith('https://api.themoviedb.org/3/movie/101'))return R(url,'application/json',JSON.stringify({id:101,title:'Fixture Movie',original_title:'Fixture Movie',release_date:'2020-01-01',alternative_titles:{titles:[]},external_ids:{}}));
if(url==='https://demo.example/film/fixture-movie')return R(url,'text/html',detail);
if(url.startsWith('https://demo.example/wp-json/demo/v1/resolve')){if(method==='POST'&&body==='tmdb=101&type=movie&year=2020&pid=987')return R(url,'application/json',JSON.stringify({sources:[{url:'https://cdn.example/master.m3u8'}]}));return R(url,'application/json',JSON.stringify({error:'wrong'}),405)}
if(url==='https://cdn.example/master.m3u8')return R(url,'application/vnd.apple.mpegurl','#EXTM3U\n#EXT-X-TARGETDURATION:6\n#EXTINF:6,\nseg.ts\n#EXT-X-ENDLIST\n');
throw new Error('unexpected '+method+' '+url);}};
sandbox.globalThis=sandbox;vm.runInNewContext(src,sandbox,{timeout:5000});
sandbox.module.exports.getStreams({tmdbId:'101',mediaType:'movie',title:'Fixture Movie',year:2020}).then(rows=>console.log(JSON.stringify({rows,calls}))).catch(err=>{console.error(err);process.exit(1)});
"""
with tempfile.TemporaryDirectory() as directory:
    path = Path(directory) / "contract-probe.cjs"
    path.write_text(runner, encoding="utf-8")
    completed = subprocess.run(["node", str(path), source], cwd=ROOT, capture_output=True, text=True, timeout=30)
    assert completed.returncode == 0, completed.stderr
    execution = json.loads(completed.stdout.strip())
assert execution["rows"], execution
assert execution["rows"][0]["url"] == "https://cdn.example/master.m3u8", execution
post_calls=[row for row in execution["calls"] if row["url"].startswith("https://demo.example/wp-json/demo/v1/resolve") and row["method"]=="POST"]
assert post_calls and post_calls[0]["body"]=="tmdb=101&type=movie&year=2020&pid=987", execution

candidate={"canonical_id":"demo","metadata":{"name":"Demo","supportedTypes":["movie"]}}
result={"tests":[{"fixture":{"title":"Fixture Movie","tmdbId":"101","mediaType":"movie","year":2020},"network_observations":[
{"stage":"content_lookup","host":"demo.example","method":"GET","proof_url":"https://demo.example/film/fixture-movie","path_pattern":"/film/{value}","status":200,"ok":True,"infrastructure":False,"content_type":"text/html","response_value_hints":[{"key":"pid","value":"987"}]},
{"stage":"player","host":"demo.example","method":"POST","proof_url":"https://demo.example/wp-json/demo/v1/resolve","path_pattern":"/wp-json/demo/v1/resolve","proof_body_kind":"form","proof_body_fields":["tmdb","type","year","pid"],"proof_body_values":{"tmdb":"101","type":"movie","year":"2020","pid":"987"},"proof_headers":{"content-type":"application/x-www-form-urlencoded","accept":"application/json"},"status":200,"ok":True,"infrastructure":False,"content_type":"application/json"}
]}]}
recipes=runtime.observed_request_recipes(candidate,result)
assert len(recipes)==2,recipes
assert recipes[0]["route"]=="/film/{slug}",recipes
resolver=recipes[1]
assert resolver["route"]=="/wp-json/demo/v1/resolve",resolver
assert resolver["method"]=="POST" and resolver["bodyKind"]=="form" and resolver["role"]=="player",resolver
assert resolver["body"]=={"tmdb":"{tmdbId}","type":"{mediaType}","year":"{year}","pid":"{binding:pid}"},resolver
assert resolver["requiredBindings"]==["pid"],resolver
assert resolver["source"]=="current-observation",resolver
assert "987" not in json.dumps(recipes,sort_keys=True)
print("Brain current-structure contract-probe execution contract passed")
