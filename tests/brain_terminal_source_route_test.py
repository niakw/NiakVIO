#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "adaptive_runtime" / "runtime_repair.py"
spec = importlib.util.spec_from_file_location("terminal_source_runtime", SCRIPT)
assert spec and spec.loader
runtime = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runtime)

assert runtime._route_role("/file/{binding:id}") == "source"
assert runtime._route_role("/drive/{binding:slug}") == "source"
assert runtime._route_role("/download/{binding:id}") == "source"
assert runtime._route_role("/download-{slug}-movie-2026/") == "detail"
assert runtime._route_role("/player/{binding:id}") == "player"
assert runtime._route_role("/api/sources/{binding:id}") == "api"

config = {
    "provider_patches": {
        "demo": {
            "official_site": "https://demo.example",
            "candidate_learned_routes": [
                "/?s={query}",
                "/file/{binding:id}",
                "/drive/{binding:slug}",
                "/download-{slug}-movie-2026/",
                "/movie/{id}",
            ],
        }
    },
    "provider_capabilities": {
        "demo": {
            "strategy": "html_scraper",
            "catalogue_types": ["movie"],
        }
    },
}

for variant in (0, 4):
    candidate = {
        "canonical_id": "demo",
        "metadata": {
            "name": "Demo",
            "baseUrl": "https://demo.example",
            "supportedTypes": ["movie"],
        },
        "brain_repair_plan": {
            "failureClass": "media_extraction_gap",
            "experimentVariant": variant,
            "experimentGeneration": 2 if variant == 4 else 1,
        },
        "brain_observed_request_recipes": [],
    }
    options = runtime._adaptive_runtime_options(candidate, config)
    assert options is not None
    direct = options["direct_paths"]
    assert "/file/{binding:id}" in direct, (variant, direct)
    assert "/drive/{binding:slug}" in direct, (variant, direct)
    assert "/download-{slug}-movie-2026/" not in direct, (variant, direct)
    assert "/movie/{id}" not in direct, (variant, direct)
    assert options["search_paths"] == ["/?s={query}"], (variant, options["search_paths"])

prefs0 = runtime._experiment_role_preferences({}, "media_extraction_gap", 0)
assert prefs0.index("source") < prefs0.index("api"), prefs0

source = SCRIPT.read_text(encoding="utf-8")
assert 'TERMINAL_MEDIA_ROLES = {"player", "source", "api"}' in source
assert 'if _route_role(route) in TERMINAL_MEDIA_ROLES' in source



GENERATOR = ROOT / "scripts" / "adaptive_runtime" / "runtime_recovery_generator.py"
gen_spec = importlib.util.spec_from_file_location("terminal_source_generator", GENERATOR)
assert gen_spec and gen_spec.loader
generator = importlib.util.module_from_spec(gen_spec)
gen_spec.loader.exec_module(generator)

wrapped = generator.apply(
    "module.exports={getStreams:async function(){return []}};\n",
    options={
        "provider_name": "Demo",
        "base_url": "https://demo.example",
        "types": ["movie"],
        "search_paths": [],
        "direct_paths": ["/title/{slug}"],
        "request_recipes": [],
        "max_pages": 8,
        "max_embeds": 8,
        "max_depth": 4,
    },
)

runner = r"""
const vm=require('vm');
const src=process.argv[2],calls=[];
function H(type){return {get:(key)=>String(key).toLowerCase()==='content-type'?type:null,getSetCookie:()=>[]}}
function R(url,type,body,status=200){return {ok:status>=200&&status<300,status,url,headers:H(type),text:async()=>String(body||''),json:async()=>JSON.parse(String(body||'{}'))}}
const sandbox={
  module:{exports:{}},exports:{},URL,AbortController,setTimeout,clearTimeout,Uint8Array,
  fetch:async(input,init={})=>{
    const url=String(input); calls.push(url);
    if(url==='https://demo.example/title/fixture-movie') return R(url,'text/html','<a href="/drive/tokenabc">drive</a>');
    if(url==='https://demo.example/drive/tokenabc') return R(url,'text/html','<a href="/file/12345">file</a>');
    if(url==='https://demo.example/file/12345') return R(url,'text/html','<script>const media="https://cdn.example/master.m3u8";</script>');
    if(url==='https://cdn.example/master.m3u8') return R(url,'application/vnd.apple.mpegurl','#EXTM3U\n#EXT-X-ENDLIST\n');
    throw new Error('unexpected '+url);
  }
};
sandbox.globalThis=sandbox;
vm.runInNewContext(src,sandbox,{timeout:5000});
sandbox.module.exports.getStreams({tmdbId:'101',mediaType:'movie',title:'Fixture Movie',year:2020})
 .then(rows=>console.log(JSON.stringify({rows,calls})))
 .catch(err=>{console.error(err);process.exit(1)});
"""
with tempfile.TemporaryDirectory() as directory:
    path = Path(directory) / "source-chain.cjs"
    path.write_text(runner, encoding="utf-8")
    completed = subprocess.run(
        ["node", str(path), wrapped],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=25,
    )
    assert completed.returncode == 0, completed.stderr
    execution = json.loads(completed.stdout.strip())

assert "https://demo.example/drive/tokenabc" in execution["calls"], execution
assert "https://demo.example/file/12345" in execution["calls"], execution
assert execution["rows"], execution
assert execution["rows"][0]["url"] == "https://cdn.example/master.m3u8", execution

generator_source = GENERATOR.read_text(encoding="utf-8")
assert 'order={player:0,source:1,api:2,episode:3,detail:4,search:5}' in generator_source
assert '(?:file|drive|download)' in generator_source

print("Brain terminal source-route preservation contract passed")
