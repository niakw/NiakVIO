#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / "scripts/provider_patches/safe_structured_parse_v1.py"

spec = importlib.util.spec_from_file_location("safe_structured_parse_v1", PATCH)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

source = r'''
function parse(rawFile) {
  let fileData = null;
  try {
    const unescaped = rawFile.replace(/\\(.)/g, "$1");
    fileData = JSON.parse(unescaped);
  } catch (error) {
    try { fileData = JSON.parse(rawFile); } catch (again) { fileData = rawFile; }
  }
  return fileData;
}
'''
patched = module.apply(source)
assert "NUVIO_SAFE_STRUCTURED_PARSE_V1" in patched
assert r'replace(/\\(.)/g, "$1")' not in patched
assert "const unescaped = rawFile;" in patched
assert "JSON.parse(unescaped)" in patched
assert "JSON.parse(rawFile)" in patched

inline = r'const parsed = JSON.parse(payload.replace(/\\(.)/g, "$1"));'
inline_patched = module.apply(inline)
assert "JSON.parse(payload)" in inline_patched
assert r'replace(/\\(.)/g, "$1")' not in inline_patched

# Do not mutate unrelated replacements or a temporary that is not used as JSON.
untouched = r'''
const cleaned = value.replace(/\\(.)/g, "$1");
console.log(cleaned);
const quotesOnly = value.replace(/\\"/g, '"');
'''
assert module.apply(untouched) == untouched

print("safe structured parse global skill test passed")
