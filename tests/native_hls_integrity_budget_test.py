#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
PATCH = ROOT / "scripts/provider_patches/hls_runtime_integrity_v1.py"

spec = importlib.util.spec_from_file_location("hls_runtime_integrity", PATCH)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

base = r'''globalThis.getStreams=async function(){
  return [{url:"https://media.example/master.m3u8",type:"hls"}];
};'''

patched = module.apply(base, {"timeout_ms": 2000})
assert "/* STARTFIX:CORE.HLS_RUNTIME_INTEGRITY.V1 */" in patched
assert "/* CLOSEFIX:CORE.HLS_RUNTIME_INTEGRITY.V1 */" in patched
assert patched.count('function nativeHlsHost(){try{return typeof g.__native_fetch==="function"}') == 1
assert patched.count("if(nativeHlsHost())return value;") == 1
assert module.apply(patched, {"timeout_ms": 2000}) == patched

runner = r'''
let calls=0;
globalThis.__native_fetch=function(){calls++;throw new Error("HLS integrity must not call native bridge");};
globalThis.fetch=async function(){calls++;throw new Error("HLS integrity must skip native fetch");};
PATCHED
(async function(){
  const rows=await globalThis.getStreams("1","movie");
  if(calls!==0)throw new Error("unexpected native HLS probes: "+calls);
  if(!Array.isArray(rows)||rows.length!==1)throw new Error("native HLS row was lost");
})().catch(function(e){console.error(e);process.exit(1)});
'''.replace("PATCHED", patched)

with tempfile.NamedTemporaryFile("w", suffix=".cjs", encoding="utf-8", delete=False) as handle:
    handle.write(runner)
    tmp = Path(handle.name)
try:
    proc = subprocess.run(["node", str(tmp)], cwd=ROOT, text=True, capture_output=True, timeout=10)
    assert proc.returncode == 0, proc.stdout + proc.stderr
finally:
    tmp.unlink(missing_ok=True)

print("native HLS budget is intrinsic to the single HLS brick")
