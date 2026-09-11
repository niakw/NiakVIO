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
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
PATCH = SCRIPTS / "provider_patches/anidb_runtime_v1.py"

spec = importlib.util.spec_from_file_location("anidb_runtime_v1", PATCH)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

BASE = r'''
async function getStreams(){ return [{url:"https://legacy.invalid"}]; }
if (typeof module !== "undefined") module.exports = { getStreams };
'''

out = module.apply(BASE)
assert module.MANAGED_FIX_ID == "PROVIDER.ANIDB.RUNTIME.V1"
assert "NIAKVIO_ANIDB_RUNTIME_V1" in out
assert module.apply(out) == out

harness = out + r'''
;(async()=>{
  let calls=[];
  globalThis.fetch=async function(url,opts){
    calls.push(String(url));
    let body="",status=200,ctype="text/plain";
    if(String(url).startsWith("https://anidb.app/browse?q=")){
      ctype="text/html";
      body='<html><a href="/anime/jujutsu-kaisen-1234"><img alt="Jujutsu Kaisen"></a><a href="/anime/jujutsu-kaisen-season-2-2554"><img alt="Jujutsu Kaisen Season 2"></a></html>';
    } else if(String(url)==="https://anidb.app/api/frontend/anime/1234/episodes"){
      ctype="application/json";body=JSON.stringify({episodes:[{id:9001,number:1},{id:9002,number:2}]});
    } else if(String(url)==="https://anidb.app/api/frontend/episode/9001/languages"){
      ctype="application/json";body=JSON.stringify({jpn:{embed_url:"https://embed.test/e/sub"},eng:{embed_url:"https://embed.test/e/dub"}});
    } else if(String(url)==="https://embed.test/e/sub"){
      ctype="text/html";body="<script>var player={file: 'https://cdn.test/sub/master.m3u8'};</script>";
    } else if(String(url)==="https://embed.test/e/dub"){
      ctype="text/html";body="<script>var player={file: 'https://cdn.test/dub/master.m3u8'};</script>";
    } else if(String(url)==="https://cdn.test/sub/master.m3u8" || String(url)==="https://cdn.test/dub/master.m3u8"){
      ctype="application/vnd.apple.mpegurl";body="#EXTM3U\n#EXT-X-VERSION:3\n";
    } else { status=404; body="not found"; }
    return {ok:status>=200&&status<300,status,url:String(url),headers:{get:(k)=>k.toLowerCase()==="content-type"?ctype:null},text:async()=>body,json:async()=>JSON.parse(body)};
  };
  globalThis.__nuvioMediaContext={canonicalMediaType:"anime",tmdbId:"95479",season:1,episode:1,tmdbMetadata:{name:"Jujutsu Kaisen"}};
  const streams=await module.exports.getStreams("95479","tv",1,1);
  if(streams.length!==2) throw new Error("expected two language streams, got "+streams.length);
  if(!streams.some(x=>x.url==="https://cdn.test/sub/master.m3u8")) throw new Error("missing sub HLS");
  if(!streams.some(x=>x.url==="https://cdn.test/dub/master.m3u8")) throw new Error("missing dub HLS");
  if(!calls.includes("https://anidb.app/api/frontend/anime/1234/episodes")) throw new Error("wrong anime id route");
  if(!calls.includes("https://anidb.app/api/frontend/episode/9001/languages")) throw new Error("wrong episode route");
  const before=calls.length;
  globalThis.__nuvioMediaContext={canonicalMediaType:"tv",tmdbId:"1396",season:1,episode:1,tmdbMetadata:{name:"Breaking Bad"}};
  const rejected=await module.exports.getStreams("1396","tv",1,1);
  if(rejected.length!==0 || calls.length!==before) throw new Error("non-anime must fail before provider network");
  globalThis.__nuvioMediaContext={canonicalMediaType:"anime",tmdbId:"95479",season:1,episode:1,tmdbMetadata:{}};
  const beforeMissing=calls.length;
  const noTitle=await module.exports.getStreams("95479","tv",1,1);
  if(noTitle.length!==0 || calls.length!==beforeMissing) throw new Error("missing anime title must fail before provider network");
  console.log("ANIDB_RUNTIME_V1_OK streams=2 sub=1 dub=1 canonical_gate_network=0 missing_title_network=0");
})().catch(e=>{console.error(e);process.exit(1)});
'''

with tempfile.TemporaryDirectory() as td:
    path = Path(td) / "anidb-runtime-test.cjs"
    path.write_text(harness, encoding="utf-8")
    result = subprocess.run(["node", str(path)], text=True, capture_output=True, cwd=ROOT)
    if result.returncode != 0:
        raise AssertionError(result.stdout + result.stderr)
    assert "ANIDB_RUNTIME_V1_OK" in result.stdout, result.stdout
    print(result.stdout.strip())
