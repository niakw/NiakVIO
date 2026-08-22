#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / "scripts/provider_patches/global_media_enrichment_v1.py"
spec = importlib.util.spec_from_file_location("global_media_enrichment_v1", PATCH)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

base = r'''
globalThis.getStreams = async function(){
  return [
    {name:"Opaque Hub", url:"https://hub.example/download?id=1", headers:{"User-Agent":"NUVIO-UA"}},
    {name:"Already Direct", url:"https://cdn.example/movie.mkv", type:"mkv"}
  ];
};
'''
patched = module.apply(base, options={"default_user_agent": "FALLBACK-UA"})
assert "scoped-playback-context-v6-direct-safe-opaque-media" in patched
assert "content-disposition" in patched
assert "metadataKind" in patched
assert "declaredDirect" in patched

runtime = patched + r'''
let binaryBodyReads = 0;
let fetches = [];
globalThis.fetch = async function(url, init){
  fetches.push(String(url));
  if (String(url).startsWith("https://hub.example/download")) {
    return {
      ok: true,
      status: 206,
      url: "https://files.example/token/opaque-123",
      headers: {
        get(name){
          const key = String(name).toLowerCase();
          if (key === "content-type") return "video/x-matroska";
          if (key === "content-disposition") return "attachment; filename=Movie.2026.1080p.mkv";
          return "";
        }
      },
      async text(){ binaryBodyReads++; throw new Error("opaque binary body must not be consumed"); }
    };
  }
  throw new Error("unexpected fetch: " + url);
};
(async()=>{
  const rows = await globalThis.getStreams({tmdbId:"123", mediaType:"movie"});
  console.log(JSON.stringify({rows, binaryBodyReads, fetches}));
})().catch(err=>{console.error(err);process.exit(2)});
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
assert payload["binaryBodyReads"] == 0, payload
assert payload["fetches"] == ["https://hub.example/download?id=1"], payload
assert len(rows) == 2, rows

resolved = rows[0]
assert resolved["url"] == "https://files.example/token/opaque-123", resolved
assert resolved["type"] == "mkv", resolved
assert resolved["isDirect"] is True, resolved
assert resolved["headers"]["User-Agent"] == "NUVIO-UA", resolved
assert resolved["headers"]["Referer"] == "https://hub.example/download?id=1", resolved
assert resolved["headers"]["Origin"] == "https://hub.example", resolved
assert all(row["url"] != "https://hub.example/download?id=1" for row in rows), rows

direct = rows[1]
assert direct["url"] == "https://cdn.example/movie.mkv", direct

print("opaque native media enrichment tests passed")
