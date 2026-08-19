#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / "scripts/provider_patches/global_media_enrichment_v1.py"
spec = importlib.util.spec_from_file_location("global_media_enrichment_direct_safety", PATCH)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

base = r'''
globalThis.getStreams=async function(){return [
  {name:"nested-direct",url:{url:"https://cdn.example/signed/movie",headers:{Authorization:"Bearer one-shot"}},type:"video/x-matroska"},
  {name:"bad-youtube",url:"https://www.youtube.com/watch?v=bad"},
  {name:"player-page",url:"https://player.example/e/abc"},
  {name:"dead-page",url:"https://dead.example/player/abc"}
]};
'''
patched = module.apply(base, options={"preserve_original": True})
# Lock the behavior, not an implementation revision string: direct nested rows
# must keep their request context, opaque containers must be provable from final
# response metadata, and unresolved player pages must not leak as playable rows.
assert "declaredDirect" in patched
assert "metadataKind" in patched
assert "content-disposition" in patched
assert "row.url&&typeof row.url===\"object\"&&row.url.headers" in patched
assert "Unresolved player/download pages are not playable streams" in patched

runtime = patched + r'''
const fetches=[];
globalThis.fetch=async function(url,init){
  url=String(url);fetches.push({url,headers:(init&&init.headers)||{}});
  if(url==="https://player.example/e/abc")return {
    ok:true,status:200,url,headers:{get:(k)=>String(k).toLowerCase()==="content-type"?"text/html":null},
    text:async()=>'<html><video src="https://media.example/final.m3u8"></video></html>'
  };
  if(url==="https://media.example/final.m3u8")return {
    ok:true,status:200,url,headers:{get:(k)=>String(k).toLowerCase()==="content-type"?"application/vnd.apple.mpegurl":null},
    text:async()=>"#EXTM3U\n#EXT-X-TARGETDURATION:6\n#EXTINF:6,\nseg.ts\n"
  };
  if(url==="https://dead.example/player/abc")return {
    ok:true,status:200,url,headers:{get:(k)=>String(k).toLowerCase()==="content-type"?"text/html":null},
    text:async()=>"<html>no playable media</html>"
  };
  throw new Error("unexpected fetch "+url);
};
(async()=>{
  const rows=await globalThis.getStreams({tmdbId:"1",mediaType:"movie"});
  console.log(JSON.stringify({rows,fetches}));
})().catch(e=>{console.error(e);process.exit(2)});
'''

with tempfile.NamedTemporaryFile("w", suffix=".cjs", delete=False, encoding="utf-8") as handle:
    handle.write(runtime)
    filename = handle.name
try:
    result = subprocess.run(["node", filename], capture_output=True, text=True, timeout=20)
finally:
    Path(filename).unlink(missing_ok=True)
assert result.returncode == 0, result.stderr
payload = json.loads(result.stdout.strip().splitlines()[-1])
rows = payload["rows"]
fetches = payload["fetches"]

by_name = {row.get("name"): row for row in rows}
assert "nested-direct" in by_name, rows
assert by_name["nested-direct"]["url"] == "https://cdn.example/signed/movie"
assert by_name["nested-direct"]["headers"]["Authorization"] == "Bearer one-shot"
assert "bad-youtube" not in by_name, rows
assert "dead-page" not in by_name, rows
assert "player-page" in by_name, rows
assert by_name["player-page"]["url"] == "https://media.example/final.m3u8"
assert by_name["player-page"].get("isDirect") is True
assert all(item["url"] != "https://cdn.example/signed/movie" for item in fetches), fetches

print("global media enrichment direct-safety tests passed")
