#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
ADAPTIVE = SCRIPTS / "adaptive_runtime"
sys.path.insert(0, str(ADAPTIVE))
sys.path.insert(1, str(SCRIPTS))
SCRIPT = ADAPTIVE / "runtime_repair.py"
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
                "/download/{slug}/",
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
    assert "/file/{binding:id}" not in direct, (variant, direct)
    assert "/drive/{binding:slug}" not in direct, (variant, direct)
    assert "/download/{slug}/" in direct, (variant, direct)
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


# Native-provider fetch capture must retain the provider's observed Referer.
# Some terminal hosts allow navigation but reject replay from the catalogue root.
captured_wrapped = generator.apply(
    """
module.exports={getStreams:async function(){
  await globalThis.fetch("https://files.example/drive/native-token",{
    headers:{Referer:"https://demo.example/detail/fixture-movie"}
  });
  return [];
}};
""",
    options={
        "provider_name": "Demo",
        "base_url": "https://demo.example",
        "types": ["movie"],
        "search_paths": [],
        "direct_paths": [],
        "request_recipes": [],
        "max_pages": 8,
        "max_embeds": 8,
        "max_depth": 4,
    },
)

capture_runner = r"""
const vm=require('vm');
const src=process.argv[2],calls=[];
function header(init,name){
  const h=(init||{}).headers||{},wanted=String(name).toLowerCase();
  for(const k of Object.keys(h)) if(String(k).toLowerCase()===wanted) return String(h[k]||'');
  return '';
}
function H(type){return {get:(key)=>String(key).toLowerCase()==='content-type'?type:null,getSetCookie:()=>[]}}
function R(url,type,body,status=200){return {ok:status>=200&&status<300,status,url,headers:H(type),text:async()=>String(body||''),json:async()=>JSON.parse(String(body||'{}'))}}
const sandbox={
  module:{exports:{}},exports:{},URL,AbortController,setTimeout,clearTimeout,Uint8Array,
  fetch:async(input,init={})=>{
    const url=String(input),ref=header(init,'referer'); calls.push({url,ref});
    if(url==='https://files.example/drive/native-token'){
      if(ref!=='https://demo.example/detail/fixture-movie') return R(url,'text/plain','hotlink blocked',403);
      return R(url,'text/html','<a href="/file/native-id">file</a>');
    }
    if(url==='https://files.example/file/native-id'){
      if(ref!=='https://files.example/drive/native-token') return R(url,'text/plain','bad referer',403);
      return R(url,'text/html','<script>const media="https://cdn.example/native.m3u8";</script>');
    }
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
    path = Path(directory) / "capture-referer.cjs"
    path.write_text(capture_runner, encoding="utf-8")
    completed = subprocess.run(
        ["node", str(path), captured_wrapped],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=25,
    )
    assert completed.returncode == 0, completed.stderr
    captured_execution = json.loads(completed.stdout.strip())

assert captured_execution["rows"], captured_execution
assert captured_execution["rows"][0]["url"] == "https://cdn.example/native.m3u8", captured_execution
drive_calls = [row for row in captured_execution["calls"] if row["url"] == "https://files.example/drive/native-token"]
assert len(drive_calls) >= 2, captured_execution
assert all(row["ref"] == "https://demo.example/detail/fixture-movie" for row in drive_calls), captured_execution


# Extensionless API/file terminals that prove binary partial content must remain
# sandbox media candidates. Final playable/identity validation still happens
# outside this resolver.
partial_wrapped = generator.apply(
    "module.exports={getStreams:async function(){return []}};\n",
    options={
        "provider_name": "Demo",
        "base_url": "https://demo.example",
        "types": ["movie"],
        "search_paths": [],
        "direct_paths": ["/api/file/abc123"],
        "request_recipes": [],
        "max_pages": 4,
        "max_embeds": 4,
        "max_depth": 2,
    },
)

partial_runner = r"""
const vm=require('vm');
const src=process.argv[2];
function H(values){return {get:(key)=>values[String(key).toLowerCase()]||null,getSetCookie:()=>[]}}
const sandbox={
  module:{exports:{}},exports:{},URL,AbortController,setTimeout,clearTimeout,Uint8Array,
  fetch:async(input,init={})=>{
    const url=String(input);
    if(url==='https://demo.example/api/file/abc123') return {
      ok:true,status:206,url,
      headers:H({'content-type':'application/octet-stream','content-range':'bytes 0-16383/999999'}),
      text:async()=>{throw new Error('binary endpoint must not be read as text')},
      json:async()=>{throw new Error('not json')}
    };
    throw new Error('unexpected '+url);
  }
};
sandbox.globalThis=sandbox;
vm.runInNewContext(src,sandbox,{timeout:5000});
sandbox.module.exports.getStreams({tmdbId:'101',mediaType:'movie',title:'Fixture Movie',year:2020})
 .then(rows=>console.log(JSON.stringify(rows)))
 .catch(err=>{console.error(err);process.exit(1)});
"""
with tempfile.TemporaryDirectory() as directory:
    path = Path(directory) / "partial-content.cjs"
    path.write_text(partial_runner, encoding="utf-8")
    completed = subprocess.run(
        ["node", str(path), partial_wrapped],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=25,
    )
    assert completed.returncode == 0, completed.stderr
    partial_rows = json.loads(completed.stdout.strip())

assert partial_rows, partial_rows
assert partial_rows[0]["url"] == "https://demo.example/api/file/abc123", partial_rows
assert partial_rows[0]["isDirect"] is True, partial_rows


# Reusable terminal adapters learned from multiple historical providers:
# encoded destination wrappers and Pixeldrain share URLs.
adapter_wrapped = generator.apply(
    """
module.exports={getStreams:async function(){
  return [
    {url:"https://wrapper.example/dl.php?link=https%253A%252F%252Fcdn.example%252Fwrapped.m3u8"},
    {url:"https://pixeldrain.net/u/pd123"}
  ];
}};
""",
    options={
        "provider_name": "Demo",
        "base_url": "https://demo.example",
        "types": ["movie"],
        "search_paths": [],
        "direct_paths": [],
        "request_recipes": [],
        "max_pages": 4,
        "max_embeds": 4,
        "max_depth": 2,
    },
)

adapter_runner = r"""
const vm=require('vm');
const src=process.argv[2],calls=[];
function H(values){return {get:(key)=>values[String(key).toLowerCase()]||null,getSetCookie:()=>[]}}
const sandbox={
  module:{exports:{}},exports:{},URL,AbortController,setTimeout,clearTimeout,Uint8Array,decodeURIComponent,
  fetch:async(input,init={})=>{
    const url=String(input); calls.push(url);
    if(url==='https://pixeldrain.net/api/file/pd123') return {
      ok:true,status:206,url,
      headers:H({'content-type':'application/octet-stream','content-range':'bytes 0-99/1000'}),
      text:async()=>{throw new Error('binary pixeldrain API must not be text-read')},
      json:async()=>{throw new Error('not json')}
    };
    throw new Error('unexpected fetch '+url);
  }
};
sandbox.globalThis=sandbox;
vm.runInNewContext(src,sandbox,{timeout:5000});
sandbox.module.exports.getStreams({tmdbId:'101',mediaType:'movie',title:'Fixture Movie',year:2020})
 .then(rows=>console.log(JSON.stringify({rows,calls})))
 .catch(err=>{console.error(err);process.exit(1)});
"""
with tempfile.TemporaryDirectory() as directory:
    path = Path(directory) / "terminal-adapters.cjs"
    path.write_text(adapter_runner, encoding="utf-8")
    completed = subprocess.run(
        ["node", str(path), adapter_wrapped],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=25,
    )
    assert completed.returncode == 0, completed.stderr
    adapter_execution = json.loads(completed.stdout.strip())

adapter_urls = {row["url"] for row in adapter_execution["rows"]}
assert "https://cdn.example/wrapped.m3u8" in adapter_urls, adapter_execution
assert "https://pixeldrain.net/api/file/pd123" in adapter_urls, adapter_execution
assert "https://wrapper.example/dl.php?link=https%253A%252F%252Fcdn.example%252Fwrapped.m3u8" not in adapter_execution["calls"], adapter_execution
assert "https://pixeldrain.net/api/file/pd123" in adapter_execution["calls"], adapter_execution

generator_source = GENERATOR.read_text(encoding="utf-8")
assert 'order={player:0,source:1,api:2,episode:3,detail:4,search:5}' in generator_source
assert '(?:file|drive|download)' in generator_source

print("Brain terminal source-route preservation contract passed")
