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

spec = importlib.util.spec_from_file_location(
    "episode_scoped_generator",
    ADAPTIVE / "runtime_recovery_generator.py",
)
assert spec and spec.loader
generator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator)

base_options = {
    "provider_name": "Episode Scope",
    "base_url": "https://episode.example",
    "types": ["tv", "anime"],
    "search_paths": [],
    "direct_paths": [],
    "max_pages": 8,
    "max_embeds": 8,
    "max_depth": 3,
    "timeout_ms": 5000,
}

# Structured JSON: episode 1 and 2 coexist. Only episode 2 may be traversed.
json_options = dict(base_options)
json_options["request_recipes"] = [{
    "route": "/api/episodes",
    "origin": "https://episode.example",
    "role": "episode",
    "method": "GET",
    "bodyKind": "none",
    "body": {},
    "headerNames": ["accept"],
    "response": "json",
    "semanticType": "tv",
    "streamProof": False,
    "requiredBindings": [],
    "executable": True,
    "source": "current-observation",
}]
json_source = generator.apply(
    "module.exports={getStreams:async function(){return []}};\n",
    options=json_options,
)
json_runner = r"""
const vm=require('vm');
const src=process.argv[2],calls=[];
function H(type){return {get:(key)=>{key=String(key).toLowerCase();if(key==='content-type')return type;if(key==='content-disposition'||key==='content-range'||key==='set-cookie')return null;return null},getSetCookie:()=>[]}}
function R(url,type,body,status=200){return {ok:status>=200&&status<400,status,url,headers:H(type),text:async()=>String(body||''),json:async()=>JSON.parse(String(body||'{}'))}}
const sandbox={
  module:{exports:{}},exports:{},URL,AbortController,setTimeout,clearTimeout,Uint8Array,
  atob:(value)=>Buffer.from(String(value),'base64').toString('binary'),
  fetch:async(input,init={})=>{
    const url=String(input);calls.push(url);
    if(url==='https://episode.example/api/episodes')return R(url,'application/json',JSON.stringify({episodes:[
      {season_number:1,episode_number:1,url:'https://episode.example/player/s01e01'},
      {season_number:1,episode_number:2,url:'https://episode.example/player/s01e02'}
    ]}));
    if(url==='https://episode.example/player/s01e02')return R(url,'text/html','<script>var file="https://cdn.example/episode2.m3u8";</script>');
    if(url==='https://episode.example/player/s01e01')throw new Error('wrong JSON episode traversed');
    throw new Error('unexpected '+url);
  }
};
sandbox.globalThis=sandbox;
vm.runInNewContext(src,sandbox,{timeout:7000});
sandbox.module.exports.getStreams({tmdbId:'101',mediaType:'tv',title:'Fixture Show',year:2020,season:1,episode:2})
  .then(rows=>console.log(JSON.stringify({rows,calls})))
  .catch(err=>{console.error(err);process.exit(1)});
"""
with tempfile.TemporaryDirectory() as directory:
    path = Path(directory) / "json-episode.cjs"
    path.write_text(json_runner, encoding="utf-8")
    completed = subprocess.run(
        ["node", str(path), json_source],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=25,
    )
assert completed.returncode == 0, completed.stderr
json_execution = json.loads(completed.stdout.strip())
assert json_execution["rows"], json_execution
assert json_execution["rows"][0]["url"] == "https://cdn.example/episode2.m3u8", json_execution
assert "https://episode.example/player/s01e01" not in json_execution["calls"], json_execution

# HTML episode table: exact S/E identity is enough to authorize traversal even
# when the route itself has no generic player/embed keyword.
native = (
    "module.exports={getStreams:async function(){return "
    + json.dumps([{
        "url": "https://episode.example/show",
        "headers": {"Referer": "https://episode.example/"},
    }])
    + "}};\n"
)
html_source = generator.apply(native, options=base_options)
html_runner = r"""
const vm=require('vm');
const src=process.argv[2],calls=[];
function H(type){return {get:(key)=>{key=String(key).toLowerCase();if(key==='content-type')return type;if(key==='content-disposition'||key==='content-range'||key==='set-cookie')return null;return null},getSetCookie:()=>[]}}
function R(url,type,body,status=200){return {ok:status>=200&&status<400,status,url,headers:H(type),text:async()=>String(body||''),json:async()=>JSON.parse(String(body||'{}'))}}
const sandbox={
  module:{exports:{}},exports:{},URL,AbortController,setTimeout,clearTimeout,Uint8Array,
  atob:(value)=>Buffer.from(String(value),'base64').toString('binary'),
  fetch:async(input,init={})=>{
    const url=String(input);calls.push(url);
    if(url==='https://episode.example/show')return R(url,'text/html',
      '<a href="/fixture-show-s01e01">Episode 1</a><a href="/fixture-show-s01e02">Episode 2</a>');
    if(url==='https://episode.example/fixture-show-s01e02')return R(url,'text/html','<script>var file="https://cdn.example/html-episode2.m3u8";</script>');
    if(url==='https://episode.example/fixture-show-s01e01')throw new Error('wrong HTML episode traversed');
    throw new Error('unexpected '+url);
  }
};
sandbox.globalThis=sandbox;
vm.runInNewContext(src,sandbox,{timeout:7000});
sandbox.module.exports.getStreams({tmdbId:'101',mediaType:'tv',title:'Fixture Show',year:2020,season:1,episode:2})
  .then(rows=>console.log(JSON.stringify({rows,calls})))
  .catch(err=>{console.error(err);process.exit(1)});
"""
with tempfile.TemporaryDirectory() as directory:
    path = Path(directory) / "html-episode.cjs"
    path.write_text(html_runner, encoding="utf-8")
    completed = subprocess.run(
        ["node", str(path), html_source],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=25,
    )
assert completed.returncode == 0, completed.stderr
html_execution = json.loads(completed.stdout.strip())
assert html_execution["rows"], html_execution
assert html_execution["rows"][0]["url"] == "https://cdn.example/html-episode2.m3u8", html_execution
assert "https://episode.example/fixture-show-s01e01" not in html_execution["calls"], html_execution

# Query-shaped episode identity is also authoritative and reversed parameter
# order is supported by the inherited V22.1 semantics.
query_native = (
    "module.exports={getStreams:async function(){return "
    + json.dumps([{
        "url": "https://episode.example/table",
        "headers": {"Referer": "https://episode.example/"},
    }])
    + "}};\n"
)
query_source = generator.apply(query_native, options=base_options)
query_runner = r"""
const vm=require('vm');
const src=process.argv[2],calls=[];
function H(type){return {get:(key)=>{key=String(key).toLowerCase();if(key==='content-type')return type;if(key==='content-disposition'||key==='content-range'||key==='set-cookie')return null;return null},getSetCookie:()=>[]}}
function R(url,type,body,status=200){return {ok:status>=200&&status<400,status,url,headers:H(type),text:async()=>String(body||''),json:async()=>JSON.parse(String(body||'{}'))}}
const sandbox={
  module:{exports:{}},exports:{},URL,AbortController,setTimeout,clearTimeout,Uint8Array,
  fetch:async(input,init={})=>{
    const url=String(input);calls.push(url);
    if(url==='https://episode.example/table')return R(url,'text/html',
      '<a href="/episode?episode=1&season=1">E1</a><a href="/episode?episode=2&season=1">E2</a>');
    if(url==='https://episode.example/episode?episode=2&season=1')return R(url,'text/html','<script>var file="https://cdn.example/query-episode2.m3u8";</script>');
    if(url==='https://episode.example/episode?episode=1&season=1')throw new Error('wrong query episode traversed');
    throw new Error('unexpected '+url);
  }
};
sandbox.globalThis=sandbox;
vm.runInNewContext(src,sandbox,{timeout:7000});
sandbox.module.exports.getStreams({tmdbId:'101',mediaType:'anime',title:'Fixture Anime',year:2020,season:1,episode:2})
  .then(rows=>console.log(JSON.stringify({rows,calls})))
  .catch(err=>{console.error(err);process.exit(1)});
"""
with tempfile.TemporaryDirectory() as directory:
    path = Path(directory) / "query-episode.cjs"
    path.write_text(query_runner, encoding="utf-8")
    completed = subprocess.run(
        ["node", str(path), query_source],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=25,
    )
assert completed.returncode == 0, completed.stderr
query_execution = json.loads(completed.stdout.strip())
assert query_execution["rows"], query_execution
assert query_execution["rows"][0]["url"] == "https://cdn.example/query-episode2.m3u8", query_execution
assert "https://episode.example/episode?episode=1&season=1" not in query_execution["calls"], query_execution

generated = generator.apply(
    "module.exports={getStreams:async function(){return []}};\n",
    options=base_options,
)
for marker in (
    "function episodeMarker(raw,q)",
    "function episodeScopedValue(value,q,depth)",
    "function episodeFilter(rows,q)",
):
    assert marker in generated, marker

print("Brain episode-scoped terminal traversal contract passed")
