#!/usr/bin/env python3
from __future__ import annotations

import base64
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
    "historical_player_generator",
    ADAPTIVE / "runtime_recovery_generator.py",
)
assert spec and spec.loader
generator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator)

OPTIONS = {
    "provider_name": "Historical Player",
    "base_url": "https://origin.example",
    "types": ["movie"],
    "search_paths": [],
    "direct_paths": [],
    "request_recipes": [],
    "max_pages": 6,
    "max_embeds": 8,
    "max_depth": 3,
    "timeout_ms": 5000,
}

def run_case(player_url: str, body: str, expected: str) -> dict:
    native = (
        "module.exports={getStreams:async function(){return "
        + json.dumps([{"url": player_url, "headers": {"Referer": "https://origin.example/detail"}}])
        + "}};\n"
    )
    source = generator.apply(native, options=OPTIONS)
    runner = rf"""
const vm=require('vm');
const src=process.argv[2];
const player={json.dumps(player_url)};
const expected={json.dumps(expected)};
const body={json.dumps(body)};
const calls=[];
function H(type){{return {{
  get:(key)=>{{key=String(key).toLowerCase();if(key==='content-type')return type;if(key==='content-disposition')return null;if(key==='content-range')return null;if(key==='set-cookie')return null;return null}},
  getSetCookie:()=>[]
}}}}
function R(url,type,text,status=200){{return {{ok:status>=200&&status<400,status,url,headers:H(type),text:async()=>String(text||''),json:async()=>JSON.parse(String(text||'{{}}'))}}}}
const sandbox={{
  module:{{exports:{{}}}},exports:{{}},URL,AbortController,setTimeout,clearTimeout,Uint8Array,
  atob:(value)=>Buffer.from(String(value),'base64').toString('binary'),
  fetch:async(input,init={{}})=>{{
    const url=String(input); calls.push({{url,referer:(init.headers&&init.headers.Referer)||''}});
    if(url===player)return R(url,'text/html',body);
    if(url===expected)return R(url,'application/vnd.apple.mpegurl','#EXTM3U\n#EXTINF:6,\nseg.ts\n');
    throw new Error('unexpected fetch '+url);
  }}
}};
sandbox.globalThis=sandbox;
vm.runInNewContext(src,sandbox,{{timeout:7000}});
sandbox.module.exports.getStreams({{tmdbId:'101',mediaType:'movie',title:'Fixture Movie',year:2020}})
  .then(rows=>console.log(JSON.stringify({{rows,calls}})))
  .catch(err=>{{console.error(err);process.exit(1)}});
"""
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "runner.cjs"
        path.write_text(runner, encoding="utf-8")
        completed = subprocess.run(
            ["node", str(path), source],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=25,
        )
    assert completed.returncode == 0, completed.stderr
    result = json.loads(completed.stdout.strip())
    assert result["rows"], result
    assert result["rows"][0]["url"] == expected, result
    assert result["rows"][0]["isDirect"] is True, result
    return result

packed = (
    "<script>"
    "eval(function(p,a,c,k,e,d){return p}"
    "('0=\"1://2/3.4\"',10,5,'file|https|packed.example|master|m3u8'.split('|'),0,{}))"
    "</script>"
)
run_case(
    "https://player.example/packed",
    packed,
    "https://packed.example/master.m3u8",
)

explicit_url = "https://explicit.example/master.m3u8"
explicit = base64.b64encode(explicit_url.encode()).decode()
explicit_result = run_case(
    "https://player.example/explicit",
    f'<a href="https://wrong.example/incidental.mp4">raw download</a><script>showVideo("{explicit}", 10)</script>',
    explicit_url,
)
assert all(row["url"] != "https://wrong.example/incidental.mp4" for row in explicit_result["rows"]), explicit_result

xor_url = "https://xor.example/master.m3u8"
hostname = "player.example"
host_hash = sum(ord(ch) for ch in hostname) & 255
transformed = bytes(
    (ord(ch) ^ ((0x3D + index * 89 + host_hash) & 255))
    for index, ch in enumerate(xor_url)
)
encoded_xor = base64.b64encode(transformed[::-1]).decode()
obfuscated = (
    '<script>var decoy="https://player.example/troll/master.m3u8";'
    'function marker(){return "reverse().join";})("'
    + encoded_xor
    + '")</script>'
)
result = run_case(
    "https://player.example/obfuscated",
    obfuscated,
    xor_url,
)
assert all("/troll/master.m3u8" not in row["url"] for row in result["rows"]), result


# Mature ProviderBase v10 behavior: a bare unrelated external origin is not a
# resolver and must not consume the crawl budget, while a meaningful external
# /file route remains traversable.
guard_native = (
    "module.exports={getStreams:async function(){return "
    + json.dumps([{"url": "https://player.example/rootguard", "headers": {"Referer": "https://origin.example/detail"}}])
    + "}};\n"
)
guard_source = generator.apply(guard_native, options=OPTIONS)
guard_runner = r"""
const vm=require('vm');
const src=process.argv[2],calls=[];
function H(type){return {get:(key)=>{key=String(key).toLowerCase();if(key==='content-type')return type;if(key==='content-disposition'||key==='content-range'||key==='set-cookie')return null;return null},getSetCookie:()=>[]}}
function R(url,type,body,status=200){return {ok:status>=200&&status<400,status,url,headers:H(type),text:async()=>String(body||''),json:async()=>JSON.parse(String(body||'{}'))}}
const sandbox={
  module:{exports:{}},exports:{},URL,AbortController,setTimeout,clearTimeout,Uint8Array,
  atob:(value)=>Buffer.from(String(value),'base64').toString('binary'),
  fetch:async(input,init={})=>{
    const url=String(input);calls.push(url);
    if(url==='https://player.example/rootguard')return R(url,'text/html','<a href="https://noise.example/">ad</a><a href="https://media.example/file/abc">server</a>');
    if(url==='https://media.example/file/abc')return R(url,'text/html','<script>var file="https://cdn.example/guard.m3u8";</script>');
    if(url==='https://cdn.example/guard.m3u8')return R(url,'application/vnd.apple.mpegurl','#EXTM3U\n');
    if(url==='https://noise.example/')throw new Error('bare external root must not be fetched');
    throw new Error('unexpected '+url);
  }
};
sandbox.globalThis=sandbox;
vm.runInNewContext(src,sandbox,{timeout:7000});
sandbox.module.exports.getStreams({tmdbId:'101',mediaType:'movie',title:'Fixture Movie',year:2020})
  .then(rows=>console.log(JSON.stringify({rows,calls})))
  .catch(err=>{console.error(err);process.exit(1)});
"""
with tempfile.TemporaryDirectory() as directory:
    path = Path(directory) / "guard-runner.cjs"
    path.write_text(guard_runner, encoding="utf-8")
    completed = subprocess.run(
        ["node", str(path), guard_source],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=25,
    )
assert completed.returncode == 0, completed.stderr
guard_execution = json.loads(completed.stdout.strip())
assert guard_execution["rows"], guard_execution
assert guard_execution["rows"][0]["url"] == "https://cdn.example/guard.m3u8", guard_execution
assert "https://noise.example/" not in guard_execution["calls"], guard_execution


# Mature handoff/canonical-player families: same-origin hidden POST form,
# opaque /embed/<id> -> /v/<id> representation, and player identifiers carried
# only in a query parameter. These are traversal candidates, not media proof.
handoff_native = (
    "module.exports={getStreams:async function(){return "
    + json.dumps([
        {"url": "https://form.example/e/abc", "headers": {"Referer": "https://origin.example/detail"}},
        {"url": "https://variant.example/embed/xyz", "headers": {"Referer": "https://origin.example/detail"}},
        {"url": "https://query.example/seed", "headers": {"Referer": "https://origin.example/detail"}},
    ])
    + "}};\n"
)
handoff_source = generator.apply(handoff_native, options=OPTIONS)
handoff_runner = r"""
const vm=require('vm');
const src=process.argv[2],calls=[];
function H(type){return {get:(key)=>{key=String(key).toLowerCase();if(key==='content-type')return type;if(key==='content-disposition'||key==='content-range'||key==='set-cookie')return null;return null},getSetCookie:()=>[]}}
function R(url,type,body,status=200){return {ok:status>=200&&status<400,status,url,headers:H(type),text:async()=>String(body||''),json:async()=>JSON.parse(String(body||'{}'))}}
const sandbox={
  module:{exports:{}},exports:{},URL,AbortController,setTimeout,clearTimeout,Uint8Array,
  atob:(value)=>Buffer.from(String(value),'base64').toString('binary'),
  fetch:async(input,init={})=>{
    const url=String(input),method=String(init.method||'GET').toUpperCase(),body=String(init.body||'');
    calls.push({url,method,body,referer:(init.headers&&init.headers.Referer)||''});
    if(url==='https://form.example/e/abc'&&method==='GET')return R(url,'text/html','<form id="F1" method="post" action="/submit"><input type="hidden" name="token" value="x"></form>');
    if(url==='https://form.example/submit'&&method==='POST'){
      if(body!=='token=x&file_code=abc')throw new Error('bad form body '+body);
      return R(url,'text/html','<script>var file="https://cdn.example/form.m3u8";</script>');
    }
    if(url==='https://variant.example/embed/xyz')return R(url,'text/html','<html>landing</html>');
    if(url==='https://variant.example/v/xyz')return R(url,'text/html','<script>var file="https://cdn.example/variant.m3u8";</script>');
    if(url==='https://query.example/seed')return R(url,'text/html','<a href="/?video=xyz">watch</a>');
    if(url==='https://query.example/?video=xyz')return R(url,'text/html','<script>var file="https://cdn.example/query.m3u8";</script>');
    throw new Error('unexpected '+method+' '+url);
  }
};
sandbox.globalThis=sandbox;
vm.runInNewContext(src,sandbox,{timeout:7000});
sandbox.module.exports.getStreams({tmdbId:'101',mediaType:'movie',title:'Fixture Movie',year:2020})
  .then(rows=>console.log(JSON.stringify({rows,calls})))
  .catch(err=>{console.error(err);process.exit(1)});
"""
with tempfile.TemporaryDirectory() as directory:
    path = Path(directory) / "handoff-runner.cjs"
    path.write_text(handoff_runner, encoding="utf-8")
    completed = subprocess.run(
        ["node", str(path), handoff_source],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=25,
    )
assert completed.returncode == 0, completed.stderr
handoff_execution = json.loads(completed.stdout.strip())
handoff_urls = {row["url"] for row in handoff_execution["rows"]}
assert {
    "https://cdn.example/form.m3u8",
    "https://cdn.example/variant.m3u8",
    "https://cdn.example/query.m3u8",
}.issubset(handoff_urls), handoff_execution
assert any(row["url"] == "https://form.example/submit" and row["method"] == "POST" for row in handoff_execution["calls"]), handoff_execution
assert any(row["url"] == "https://variant.example/v/xyz" for row in handoff_execution["calls"]), handoff_execution
assert any(row["url"] == "https://query.example/?video=xyz" for row in handoff_execution["calls"]), handoff_execution


# V20-style HTML catalogue identity correlation: multiple ids are present, but
# only the anchor whose visible title matches the fixture may bind the player id.
html_binding_options = dict(OPTIONS)
html_binding_options["request_recipes"] = [
    {
        "route": "/search?q={query}",
        "origin": "https://catalog.example",
        "role": "search",
        "method": "GET",
        "bodyKind": "none",
        "body": {},
        "headerNames": ["accept"],
        "response": "html-or-text",
        "semanticType": "movie",
        "streamProof": False,
        "requiredBindings": [],
        "executable": True,
        "source": "current-observation",
    },
    {
        "route": "/player/{binding:id}",
        "origin": "https://catalog.example",
        "role": "player",
        "method": "GET",
        "bodyKind": "none",
        "body": {},
        "headerNames": ["accept"],
        "response": "html-or-text",
        "semanticType": "movie",
        "streamProof": False,
        "requiredBindings": ["id"],
        "executable": True,
        "source": "current-observation",
    },
]
html_binding_source = generator.apply(
    "module.exports={getStreams:async function(){return []}};\n",
    options=html_binding_options,
)
html_binding_runner = r"""
const vm=require('vm');
const src=process.argv[2],calls=[];
function H(type){return {get:(key)=>{key=String(key).toLowerCase();if(key==='content-type')return type;if(key==='content-disposition'||key==='content-range'||key==='set-cookie')return null;return null},getSetCookie:()=>[]}}
function R(url,type,body,status=200){return {ok:status>=200&&status<400,status,url,headers:H(type),text:async()=>String(body||''),json:async()=>JSON.parse(String(body||'{}'))}}
const sandbox={
  module:{exports:{}},exports:{},URL,AbortController,setTimeout,clearTimeout,Uint8Array,
  atob:(value)=>Buffer.from(String(value),'base64').toString('binary'),
  fetch:async(input,init={})=>{
    const url=String(input);calls.push(url);
    if(url==='https://catalog.example/search?q=Fixture%20Movie')return R(url,'text/html',
      '<a data-id="555" href="/movie/555-wrong-movie">Wrong Movie (2020)</a>'+
      '<a data-id="987" href="/movie/987-fixture-movie">Fixture Movie (2020)</a>');
    if(url==='https://catalog.example/player/987')return R(url,'text/html','<script>var file="https://cdn.example/html-binding.m3u8";</script>');
    if(url==='https://catalog.example/player/555')throw new Error('wrong catalogue identity selected');
    throw new Error('unexpected '+url);
  }
};
sandbox.globalThis=sandbox;
vm.runInNewContext(src,sandbox,{timeout:7000});
sandbox.module.exports.getStreams({tmdbId:'101',mediaType:'movie',title:'Fixture Movie',year:2020})
  .then(rows=>console.log(JSON.stringify({rows,calls})))
  .catch(err=>{console.error(err);process.exit(1)});
"""
with tempfile.TemporaryDirectory() as directory:
    path = Path(directory) / "html-binding-runner.cjs"
    path.write_text(html_binding_runner, encoding="utf-8")
    completed = subprocess.run(
        ["node", str(path), html_binding_source],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=25,
    )
assert completed.returncode == 0, completed.stderr
html_binding_execution = json.loads(completed.stdout.strip())
assert html_binding_execution["rows"], html_binding_execution
assert html_binding_execution["rows"][0]["url"] == "https://cdn.example/html-binding.m3u8", html_binding_execution
assert "https://catalog.example/player/987" in html_binding_execution["calls"], html_binding_execution
assert "https://catalog.example/player/555" not in html_binding_execution["calls"], html_binding_execution

generated = generator.apply(
    "module.exports={getStreams:async function(){return []}};\n",
    options=OPTIONS,
)
for marker in (
    "function unpackPackedPlayer(code)",
    "function explicitPlayerPayloadUrls(text,base)",
    "function decodedObfuscatedHls(html,pageUrl)",
    "function followable(u,parent)",
    "function playerForm(html,pageUrl)",
    "function playerRouteVariants(raw)",
    "function correlatedBindings(body,m)",
):
    assert marker in generated, marker

# The packer is decoded structurally. No remote code evaluation primitive is used.
assert "return eval(" not in generated
assert "=eval(" not in generated

print("Brain historical player extractor transfer contract passed")
