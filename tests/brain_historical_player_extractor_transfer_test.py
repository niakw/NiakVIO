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
    runner = f"""
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
run_case(
    "https://player.example/explicit",
    f'<script>showVideo("{explicit}")</script>',
    explicit_url,
)

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

generated = generator.apply(
    "module.exports={getStreams:async function(){return []}};\n",
    options=OPTIONS,
)
for marker in (
    "function unpackPackedPlayer(code)",
    "function explicitPlayerPayloadUrls(text,base)",
    "function decodedObfuscatedHls(html,pageUrl)",
):
    assert marker in generated, marker

# The packer is decoded structurally. No remote code evaluation primitive is used.
assert "return eval(" not in generated
assert "=eval(" not in generated

print("Brain historical player extractor transfer contract passed")
