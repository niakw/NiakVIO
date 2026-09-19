#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / "scripts" / "provider_patches" / "stream_output_sanitizer_v7.py"

spec = importlib.util.spec_from_file_location("stream_output_sanitizer_v7_test", PATCH)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

source = "module.exports={getStreams:async function(){return globalThis.__rows||[];}};\n"
options = {
    "probe_direct_media": True,
    "probe_all_urls": True,
    "max_probes": 20,
    "probe_timeout_ms": 2000,
    "min_vod_duration_seconds": 60,
}
patched = module.apply(source, options=options)
assert module.apply(patched, options=options) == patched
module.validate(patched)

node = r'''
globalThis.__fetchCalls=0;
globalThis.fetch=async function(){
  globalThis.__fetchCalls++;
  return {ok:false,status:403,url:"https://blocked.invalid/",headers:{get:function(){return "";}}};
};
globalThis.__rows=[
  {url:"https://player.invalid/shell.php?videoid=42",__nuvioCorrelatedPlayerFallbackV1:{url:"https://player.invalid/shell.php?videoid=42"}},
  {url:"https://media.invalid/master.m3u8",__nuvioCorrelatedPlayerFallbackV1:{url:"https://media.invalid/master.m3u8"}},
  {url:"https://player.invalid/embed/other",__nuvioCorrelatedPlayerFallbackV1:{url:"https://player.invalid/embed/mismatch"}}
];
'''
node += patched
node += r'''
;(async function(){
  var out=await module.exports.getStreams();
  process.stdout.write(JSON.stringify({out:out,calls:globalThis.__fetchCalls}));
})().catch(function(e){console.error(e);process.exit(1)});
'''
proc = subprocess.run(["node", "-e", node], cwd=ROOT, check=True, capture_output=True, text=True)
result = json.loads(proc.stdout)
assert len(result["out"]) == 1, result
assert result["out"][0]["url"] == "https://player.invalid/shell.php?videoid=42", result
assert "__nuvioCorrelatedPlayerFallbackV1" not in result["out"][0], result
assert result["calls"] >= 1, result

print("stream output correlated player fallback V7 tests passed")
