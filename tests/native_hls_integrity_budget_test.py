#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / "scripts/provider_patches/native_hls_integrity_budget_v1.py"

spec = importlib.util.spec_from_file_location("native_hls_integrity_budget", PATCH)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

fixture = r'''/* NUVIO_HLS_RUNTIME_INTEGRITY_V1:abc */
;(function(g,config){
  "use strict";
  async function filterRows(value){
    var rows=Array.isArray(value)?value:value&&Array.isArray(value.streams)?value.streams:null;
    if(!rows)return value;
    return rows;
  }
})(typeof globalThis!=="undefined"?globalThis:this,{"timeoutMs":9000,"probeAllUrls":true,"failClosedUnknown":true});
'''

patched = module.apply(fixture)
assert "NUVIO_NATIVE_HLS_INTEGRITY_BUDGET_V1" in patched
assert 'function nativeHlsHost(){try{return typeof g.__native_fetch==="function"}' in patched
assert "if(nativeHlsHost())return value;" in patched
assert module.apply(patched) == patched

plain = "module.exports={getStreams:async()=>[]};\n"
assert module.apply(plain) == plain
print("native HLS integrity budget tests passed")
