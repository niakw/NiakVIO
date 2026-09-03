#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
PATCH = ROOT / "scripts/provider_patches/hls_runtime_integrity_v1.py"
OVERRIDES = ROOT / "provider-overrides.json"

spec = importlib.util.spec_from_file_location("hls_runtime_integrity", PATCH)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

base = r'''globalThis.getStreams=async function(){
  return [{url:"https://media.example/media.m3u8",type:"hls",headers:{Referer:"https://player.example/watch",Origin:"https://player.example"}}];
};'''

# Default Core keeps the historical zero-extra-network behavior on native clients.
default_patched = module.apply(base, {"timeout_ms": 2000})
assert "/* STARTFIX:CORE.HLS_RUNTIME_INTEGRITY.V1 */" in default_patched
assert "/* CLOSEFIX:CORE.HLS_RUNTIME_INTEGRITY.V1 */" in default_patched
assert '"probeFirstSegmentNative":true' not in default_patched
assert module.apply(default_patched, {"timeout_ms": 2000}) == default_patched

# Providers with positive evidence of malformed HLS playback can opt into one
# generic Core capability: validate a bounded number of first media containers.
native_options = {
    "timeout_ms": 2000,
    "probe_first_segment_native": True,
    "native_probe_max_rows": 3,
    "native_probe_timeout_ms": 1500,
}
native_patched = module.apply(base, native_options)
assert '"probeFirstSegmentNative":true' in native_patched
assert '"nativeProbeMaxRows":3' in native_patched
assert '"nativeProbeTimeoutMs":1500' in native_patched
assert '"implementationRevision":"native-first-segment-container-proof-v8-tv-byte-capability"' in native_patched
assert module.apply(native_patched, native_options) == native_patched

cfg = json.loads(OVERRIDES.read_text(encoding="utf-8"))
kehflix = cfg["provider_patches"]["kehflix"]["core_options"]["hls_runtime_integrity"]
assert kehflix["probe_first_segment_native"] is True
assert 1 <= int(kehflix["native_probe_max_rows"]) <= 8
assert 900 <= int(kehflix["native_probe_timeout_ms"]) <= 5000


def run_node(source: str) -> None:
    with tempfile.NamedTemporaryFile("w", suffix=".cjs", encoding="utf-8", delete=False) as handle:
        handle.write(source)
        tmp = Path(handle.name)
    try:
        proc = subprocess.run(["node", str(tmp)], cwd=ROOT, text=True, capture_output=True, timeout=12)
        assert proc.returncode == 0, proc.stdout + proc.stderr
    finally:
        tmp.unlink(missing_ok=True)


# No opt-in means no native HLS probe at all.
run_node(
    r'''
let calls=0;
globalThis.__native_fetch=function(){};
globalThis.fetch=async function(){calls++;throw new Error("default native HLS path must not probe");};
PATCHED
(async function(){
  const rows=await globalThis.getStreams("1","movie");
  if(calls!==0)throw new Error("unexpected default native HLS probes: "+calls);
  if(!Array.isArray(rows)||rows.length!==1)throw new Error("default native HLS row was lost");
})().catch(function(e){console.error(e);process.exit(1)});
'''.replace("PATCHED", default_patched)
)

# Valid MPEG-TS: playlist + a bounded first-segment read, with playback headers retained.
run_node(
    r'''
let calls=[];
globalThis.__native_fetch=function(){};
function response(url,contentType,text,bytes){
  return {
    ok:true,status:200,url,
    headers:{get:function(name){return String(name).toLowerCase()==="content-type"?contentType:"";}},
    text:async function(){return text||"";},
    arrayBuffer:async function(){
      const b=bytes||new Uint8Array(0);
      return b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength);
    }
  };
}
const ts=new Uint8Array(376);ts[0]=0x47;ts[188]=0x47;
globalThis.fetch=async function(url,init){
  calls.push({url,headers:Object.assign({},init&&init.headers||{})});
  if(url.endsWith("media.m3u8"))return response(url,"application/vnd.apple.mpegurl","#EXTM3U\n#EXTINF:6,\nseg-1.ts\n");
  if(url.endsWith("seg-1.ts"))return response(url,"video/mp2t","",ts);
  throw new Error("unexpected "+url);
};
PATCHED
(async function(){
  const rows=await globalThis.getStreams("1","movie");
  if(!Array.isArray(rows)||rows.length!==1)throw new Error("valid TS row rejected");
  if(calls.length!==2)throw new Error("expected playlist+segment probe, got "+calls.length);
  for(const call of calls){
    if(call.headers.Referer!=="https://player.example/watch")throw new Error("referer lost");
    if(call.headers.Origin!=="https://player.example")throw new Error("origin lost");
  }
})().catch(function(e){console.error(e);process.exit(1)});
'''.replace("PATCHED", native_patched)
)

# A .ts URL serving HTML/garbage is conclusively invalid and is filtered before playback.
run_node(
    r'''
let calls=0;
globalThis.__native_fetch=function(){};
function response(url,contentType,text,bytes){
  return {
    ok:true,status:200,url,
    headers:{get:function(name){return String(name).toLowerCase()==="content-type"?contentType:"";}},
    text:async function(){return text||"";},
    arrayBuffer:async function(){
      const b=bytes||new TextEncoder().encode(text||"");
      return b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength);
    }
  };
}
globalThis.fetch=async function(url){
  calls++;
  if(url.endsWith("media.m3u8"))return response(url,"application/vnd.apple.mpegurl","#EXTM3U\n#EXTINF:6,\nseg-1.ts\n");
  if(url.endsWith("seg-1.ts"))return response(url,"text/html","<!doctype html><html>blocked</html>");
  throw new Error("unexpected "+url);
};
PATCHED
(async function(){
  const rows=await globalThis.getStreams("1","movie");
  if(!Array.isArray(rows)||rows.length!==0)throw new Error("malformed TS row survived");
  if(calls!==2)throw new Error("unexpected malformed probe count "+calls);
})().catch(function(e){console.error(e);process.exit(1)});
'''.replace("PATCHED", native_patched)
)

# Android TV contract: fetch exposes text()/json() but no body/arrayBuffer and
# TextEncoder/TextDecoder are absent. Lack of readable segment bytes is unknown,
# not positive malformed-media evidence, so the stream must survive.
run_node(
    r'''
globalThis.TextEncoder=undefined;
globalThis.TextDecoder=undefined;
let calls=0;
globalThis.__native_fetch=function(){};
globalThis.fetch=async function(url){
  calls++;
  if(url.endsWith("media.m3u8"))return {
    ok:true,status:200,url,
    headers:{get:function(){return "application/vnd.apple.mpegurl";}},
    text:async function(){return "#EXTM3U\n#EXTINF:6,\nseg-1.ts\n";},
    json:async function(){return null;}
  };
  if(url.endsWith("seg-1.ts"))return {
    ok:true,status:200,url,
    headers:{get:function(){return "video/mp2t";}},
    text:async function(){return "binary-not-byte-addressable-on-tv";},
    json:async function(){return null;}
  };
  throw new Error("unexpected "+url);
};
PATCHED
(async function(){
  const rows=await globalThis.getStreams("1","movie");
  if(!Array.isArray(rows)||rows.length!==1)throw new Error("TV byte-unavailable HLS row rejected");
  if(calls!==2)throw new Error("unexpected TV probe count "+calls);
})().catch(function(e){console.error(e);process.exit(1)});
'''.replace("PATCHED", native_patched)
)

# Network uncertainty must not become a false stream rejection.
run_node(
    r'''
let calls=0;
globalThis.__native_fetch=function(){};
globalThis.fetch=async function(url){
  calls++;
  if(url.endsWith("media.m3u8"))return {
    ok:true,status:200,url,
    headers:{get:function(){return "application/vnd.apple.mpegurl";}},
    text:async function(){return "#EXTM3U\n#EXTINF:6,\nseg-1.ts\n";}
  };
  throw new Error("temporary network failure");
};
PATCHED
(async function(){
  const rows=await globalThis.getStreams("1","movie");
  if(!Array.isArray(rows)||rows.length!==1)throw new Error("unknown network state rejected stream");
  if(calls!==2)throw new Error("unexpected unknown probe count "+calls);
})().catch(function(e){console.error(e);process.exit(1)});
'''.replace("PATCHED", native_patched)
)

print("native HLS first-segment container proof is bounded, opt-in and fail-closed only on positive invalid evidence")
