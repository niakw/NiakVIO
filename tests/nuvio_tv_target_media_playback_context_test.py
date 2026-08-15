#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / "scripts/provider_patches/nuvio_tv_target_media_v4.py"


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("target_media_playback_context_test", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    module = load_module(PATCH)
    source = (
        'module.exports={getStreams:async function(){return [{'
        'name:"StreamZo",title:"Mon ninja et moi 3",language:"fr",quality:"HD",'
        'url:"https://site.example.com/title",headers:{Referer:"https://site.example.com/title"}'
        '}]}};\n'
    )
    options = {
        "provider_name": "StreamZo",
        "max_candidates": 22,
        "timeout_ms": 20000,
        "blocked_hosts": ["fstream.top"],
        "strip_legacy_direct_media_v2": True,
        "force_rewrap_target_media": True,
    }
    patched = module.apply(source, options=options)
    assert module.V4_MARKER in patched
    assert module.V5_MARKER in patched
    assert module.FETCH_COMPAT_MARKER in patched
    assert module.PROTOCOL_RELATIVE_MARKER in patched
    assert module.apply(patched, options=options) == patched

    harness = r'''
const fs=require('fs'),vm=require('vm');
const code=fs.readFileSync('provider.js','utf8');
const requests=[];
function response(url,body,contentType,setCookie){
  return {
    ok:true,status:200,url,
    headers:{get:function(name){name=String(name).toLowerCase();if(name==='content-type')return contentType||'text/html';if(name==='set-cookie')return setCookie||null;return null;}},
    text:async function(){return body;},
    json:async function(){try{return JSON.parse(body)}catch(_){return null;}}
  };
}
const ctx={console,URL,setTimeout,clearTimeout,module:{exports:{}},exports:{}};ctx.globalThis=ctx;
ctx.fetch=async function(url,opt){
  const headers=Object.assign({},opt&&opt.headers||{});requests.push({url,headers});
  if(url==='https://site.example.com/title'){
    return response(url,'<iframe src="https://player.example.com/embed/1"></iframe>','text/html','sid=abc; Domain=.example.com; Path=/; Secure');
  }
  if(url==='https://player.example.com/embed/1'){
    return response(url,'<script>var file="https://cdn.example.com/master.m3u8";</script>','text/html','play=xyz; Domain=.example.com; Path=/; Secure');
  }
  if(url==='https://cdn.example.com/master.m3u8'){
    return response(url,'#EXTM3U\n#EXTINF:600,\nseg.ts\n#EXTINF:600,\nseg2.ts\n','application/vnd.apple.mpegurl',null);
  }
  return {ok:false,status:404,url,headers:{get:()=> 'text/plain'},text:async()=>''};
};
vm.createContext(ctx);vm.runInContext(code,ctx);
(async()=>{
  const rows=await ctx.module.exports.getStreams('123','movie');
  console.log(JSON.stringify({rows,requests}));
})().catch(e=>{console.error(e&&e.stack||e);process.exit(1)});
'''
    with tempfile.TemporaryDirectory() as td:
        work = Path(td)
        (work / "provider.js").write_text(patched, encoding="utf-8")
        (work / "harness.cjs").write_text(harness, encoding="utf-8")
        proc = subprocess.run(
            ["node", "harness.cjs"], cwd=work, text=True, capture_output=True, timeout=20
        )
    if proc.returncode != 0:
        raise AssertionError(f"node harness failed\nstdout={proc.stdout}\nstderr={proc.stderr}")
    result = json.loads(proc.stdout.strip().splitlines()[-1])
    rows = result["rows"]
    assert len(rows) == 1, rows
    row = rows[0]
    assert row["url"] == "https://cdn.example.com/master.m3u8", row
    assert row["type"] == "hls", row
    assert row["headers"]["Referer"] == "https://player.example.com/embed/1", row
    assert row["headers"]["Origin"] == "https://player.example.com", row
    assert row["headers"]["Cookie"] in ("sid=abc; play=xyz", "play=xyz; sid=abc"), row
    assert row["headers"]["User-Agent"].startswith("Mozilla/5.0"), row
    assert row.get("size") == "fr • HLS", row

    req = {item["url"]: item["headers"] for item in result["requests"]}
    assert req["https://player.example.com/embed/1"]["Referer"] == "https://site.example.com/title"
    assert req["https://player.example.com/embed/1"]["Cookie"] == "sid=abc"
    assert req["https://cdn.example.com/master.m3u8"]["Referer"] == "https://player.example.com/embed/1"
    assert req["https://cdn.example.com/master.m3u8"]["Origin"] == "https://player.example.com"
    assert req["https://cdn.example.com/master.m3u8"]["Cookie"] in ("sid=abc; play=xyz", "play=xyz; sid=abc")

    print("NuvioTV target-media playback-context tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
