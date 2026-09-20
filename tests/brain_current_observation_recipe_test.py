#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
ADAPTIVE = SCRIPTS / "adaptive_runtime"
sys.path.insert(0, str(ADAPTIVE))
sys.path.insert(1, str(SCRIPTS))

spec = importlib.util.spec_from_file_location(
    "adaptive_runtime_repair_observed",
    ROOT / "scripts" / "adaptive_runtime" / "runtime_repair.py",
)
assert spec and spec.loader
runtime = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runtime)

candidate = {
    "canonical_id": "demo",
    "metadata": {
        "name": "Demo",
        "baseUrl": "https://demo.example",
        "supportedTypes": ["movie"],
    },
}
result = {
    "status": "no_streams",
    "evidence": {"streams_returned": 0, "streams_playable": 0},
    "tests": [{
        "fixture": {
            "label": "Fixture Movie",
            "title": "Fixture Movie",
            "tmdbId": "101",
            "mediaType": "movie",
            "year": 2020,
        },
        "failure_class": "content_lookup_completed_no_streams",
        "network_observations": [
            {
                "stage": "search",
                "host": "api.themoviedb.org",
                "method": "GET",
                "path_pattern": "/3/movie/{id}",
                "proof_url": "https://api.themoviedb.org/3/movie/101",
                "status": 200,
                "ok": True,
                "infrastructure": True,
            },
            {
                "stage": "search",
                "host": "demo.example",
                "method": "POST",
                "path_pattern": "/engine/ajax/search.php",
                "proof_url": "https://demo.example/engine/ajax/search.php",
                "proof_body_kind": "form",
                "proof_body_fields": ["query", "page"],
                "proof_body_values": {"query": "Fixture Movie", "page": "1"},
                "proof_headers": {
                    "content-type": "application/x-www-form-urlencoded",
                    "accept": "text/html",
                    "cookie": "must-not-be-used",
                },
                "content_type": "application/json",
                "response_value_hints": [{"key": "id", "value": "987"}],
                "status": 200,
                "ok": True,
                "infrastructure": False,
            },
            {
                "stage": "search",
                "host": "demo.example",
                "method": "GET",
                "path_pattern": "/api/search?q={value}",
                "proof_url": "https://demo.example/api/search?q=Fixture%20Movie",
                "content_type": "application/json",
                "status": 200,
                "ok": True,
                "infrastructure": False,
            },
            {
                # 987 is a provider-local ID, not the fixture TMDB id. Until
                # response->request binding exists this route must not execute.
                "stage": "player",
                "host": "demo.example",
                "method": "GET",
                "path_pattern": "/player/{id}",
                "proof_url": "https://demo.example/player/987",
                "content_type": "text/html",
                "status": 200,
                "ok": True,
                "infrastructure": False,
            },
            {
                "stage": "player",
                "host": "demo.example",
                "method": "GET",
                "path_pattern": "/player?token={value}",
                "proof_url": "https://demo.example/player?token=%3Credacted%3E",
                "status": 200,
                "ok": True,
                "infrastructure": False,
            },
            {
                "stage": "search",
                "host": "demo.example",
                "method": "GET",
                "path_pattern": "/failed?q={value}",
                "proof_url": "https://demo.example/failed?q=Fixture%20Movie",
                "status": 500,
                "ok": False,
                "infrastructure": False,
            },
        ],
    }],
}

recipes = runtime.observed_request_recipes(candidate, result)
assert len(recipes) == 3, recipes
assert [row["route"] for row in recipes] == [
    "/engine/ajax/search.php",
    "/api/search?q={query}",
    "/player/{binding:id}",
], recipes
post = recipes[0]
assert post["source"] == "current-observation", post
assert post["method"] == "POST", post
assert post["body"] == {"query": "{query}", "page": "1"}, post
assert post["headerNames"] == ["accept", "content-type"], post
assert post["origin"] == "https://demo.example", post
assert recipes[1]["response"] == "json", recipes[1]
bound = recipes[2]
assert bound["requiredBindings"] == ["id"], bound
assert "987" not in bound["route"], bound
assert all("token" not in row["route"].casefold() for row in recipes)

candidate["brain_observed_request_recipes"] = recipes
candidate["brain_repair_plan"] = {
    "failureClass": "route_proven_gap",
    "experimentVariant": 4,
    "experimentGeneration": 2,
}
config = {
    "provider_patches": {
        "demo": {"official_site": "https://demo.example", "capability": "html_scraper"},
    },
    "provider_capabilities": {
        "demo": {"strategy": "html_scraper", "catalogue_types": ["movie"]},
    },
}
options = runtime._adaptive_runtime_options(candidate, config)
assert options is not None
assert options["request_recipes"][:3] == recipes, options["request_recipes"]
assert options["route_prior_counts"]["currentObservationRequestRecipes"] == 3

# Planner transport must keep causal shape but not raw URL/body/header values.
spec2 = importlib.util.spec_from_file_location(
    "brain_runtime_observed",
    ROOT / "scripts" / "brain_repair_runtime.py",
)
assert spec2 and spec2.loader
brain = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(brain)
transport = brain._planner_result(result)
obs = transport["tests"][0]["network_observations"]
provider_obs = [row for row in obs if not row["infrastructure"]]
assert provider_obs[0]["stage"] == "search", provider_obs[0]
assert provider_obs[0]["method"] == "POST", provider_obs[0]
assert provider_obs[0]["path_pattern"] == "/engine/ajax/search.php", provider_obs[0]
assert provider_obs[0]["proof_body_kind"] == "form", provider_obs[0]
serialized = repr(transport)
assert "Fixture Movie" not in serialized, serialized
assert "proof_url" not in serialized, serialized
assert "proof_body_values" not in serialized, serialized
assert "cookie" not in serialized, serialized

runner = (ROOT / "scripts" / "run_adaptive_deep_repair.py").read_text(encoding="utf-8")
assert 'candidate["brain_observed_request_recipes"] = runtime_repair.observed_request_recipes(candidate, result)' in runner



# Execute the synthesized chain: search response -> unique id binding -> player -> media.
gen_spec = importlib.util.spec_from_file_location(
    "observed_recipe_generator",
    ROOT / "scripts" / "adaptive_runtime" / "runtime_recovery_generator.py",
)
assert gen_spec and gen_spec.loader
generator = importlib.util.module_from_spec(gen_spec)
gen_spec.loader.exec_module(generator)
source = generator.apply(
    'module.exports={getStreams:async function(){return []}};\n',
    options=options,
)
runner = r"""
const vm=require('vm');
const src=process.argv[2],calls=[];
function H(type){return {get:(key)=>{key=String(key).toLowerCase();if(key==='content-type')return type;if(key==='content-disposition')return null;if(key==='set-cookie')return null;return null},getSetCookie:()=>[]}}
function R(url,type,body,status=200){return {ok:status>=200&&status<300,status,url,headers:H(type),text:async()=>String(body||''),json:async()=>JSON.parse(String(body||'{}'))}}
const sandbox={
  module:{exports:{}},exports:{},URL,AbortController,setTimeout,clearTimeout,Uint8Array,
  fetch:async(input,init={})=>{
    const url=String(input),method=String(init.method||'GET').toUpperCase(),body=String(init.body||'');
    calls.push({url,method,body});
    if(url==='https://demo.example/engine/ajax/search.php'){
      if(method!=='POST'||body!=='query=Fixture%20Movie&page=1') throw new Error('bad observed search replay');
      return R(url,'application/json',JSON.stringify({id:'987',title:'Fixture Movie'}));
    }
    if(url==='https://demo.example/api/search?q=Fixture%20Movie'){
      return R(url,'application/json',JSON.stringify({message:'secondary search'}));
    }
    if(url==='https://demo.example/player/987'){
      return R(url,'text/html','<script>var p={file:"https://cdn.example/master.m3u8"};</script>');
    }
    if(url==='https://cdn.example/master.m3u8'){
      return R(url,'application/vnd.apple.mpegurl','#EXTM3U\n#EXT-X-TARGETDURATION:6\n#EXTINF:6,\nseg.ts\n#EXT-X-ENDLIST\n');
    }
    throw new Error('unexpected '+method+' '+url);
  }
};
sandbox.globalThis=sandbox;
vm.runInNewContext(src,sandbox,{timeout:5000});
sandbox.module.exports.getStreams({tmdbId:'101',mediaType:'movie',title:'Fixture Movie',year:2020})
  .then(rows=>console.log(JSON.stringify({rows,calls})))
  .catch(err=>{console.error(err);process.exit(1)});
"""
import json
import subprocess
import tempfile
with tempfile.TemporaryDirectory() as directory:
    path = Path(directory) / "bound-chain.cjs"
    path.write_text(runner, encoding="utf-8")
    completed = subprocess.run(
        ["node", str(path), source],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=25,
    )
    assert completed.returncode == 0, completed.stderr
    execution = json.loads(completed.stdout.strip())

assert any(row["url"] == "https://demo.example/player/987" for row in execution["calls"]), execution
assert execution["rows"], execution
assert execution["rows"][0]["url"] == "https://cdn.example/master.m3u8", execution

print("Brain current-observation request recipe contract passed")
