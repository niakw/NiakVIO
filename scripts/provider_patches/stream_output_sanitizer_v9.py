#!/usr/bin/env python3
"""V9 terminal sanitizer: fetch text manifests whole before validating them.

V8 correctly made ordinary probe outcomes fail closed, but the inherited probe
always sent ``Range: bytes=0-32767``. Some HLS/CDN endpoints honour that range
for the manifest itself and return HTTP 206 with a syntactically truncated
playlist. Treating that fragment as the complete playlist creates false
invalidity (for example a cut ``#EXT-X-STREAM-INF`` without its following URI).

V9 keeps the strict V8 verdict and all hard 403/404/410 rejection. It only drops
the Range header for explicit HLS/DASH text manifest URLs; binary media probes
retain the bounded Range request.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
V8_PATH = ROOT / "stream_output_sanitizer_v8.py"
MANAGED_FIX_ID = "CORE.STREAM_SANITIZER.V6"
MARKER = "NUVIO_STREAM_OUTPUT_FULL_MANIFEST_V9"
MARKER_COMMENT = f"/* {MARKER} */"

OLD_FETCH = 'var response=await g.fetch(url,{method:"GET",headers:headersFor(stream,referer),redirect:"follow",signal:controller.signal});'
NEW_FETCH = '''var requestHeaders=headersFor(stream,referer);
      if(/\\.(?:m3u8?|mpd)(?:[?#]|$)/i.test(String(url||""))){
        try{Object.keys(requestHeaders).forEach(function(key){if(String(key).toLowerCase()==="range")delete requestHeaders[key]})}catch(_e){}
      }
      var response=await g.fetch(url,{method:"GET",headers:requestHeaders,redirect:"follow",signal:controller.signal});'''
ANCHOR = "  function clearPrivateProofs(stream){\n"


def _load_v8_apply():
    spec = importlib.util.spec_from_file_location("stream_output_sanitizer_v8_for_v9", V8_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {V8_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.apply


V8_APPLY = _load_v8_apply()


def _restore_v8_source(text: str) -> str:
    source = str(text or "")
    if MARKER_COMMENT in source:
        if source.count(MARKER_COMMENT) != 1:
            raise ValueError(f"stream sanitizer v9 marker count={source.count(MARKER_COMMENT)}")
        source = source.replace(MARKER_COMMENT + "\n", "", 1)
        if NEW_FETCH not in source:
            raise ValueError("stream sanitizer v9 manifest fetch hook missing")
        source = source.replace(NEW_FETCH, OLD_FETCH, 1)
    return source


def apply(text: str, options: dict[str, Any] | None = None, **kwargs: Any) -> str:
    source = _restore_v8_source(text)
    patched = V8_APPLY(source, options=options, **kwargs)
    if patched.count(OLD_FETCH) != 1:
        raise ValueError(f"stream sanitizer v9 fetch hook count={patched.count(OLD_FETCH)}")
    patched = patched.replace(OLD_FETCH, NEW_FETCH, 1)
    if patched.count(ANCHOR) != 1:
        raise ValueError(f"stream sanitizer v9 marker anchor count={patched.count(ANCHOR)}")
    patched = patched.replace(ANCHOR, f"  {MARKER_COMMENT}\n" + ANCHOR, 1)
    validate(patched)
    return patched


def validate(text: str) -> None:
    if text.count(MARKER) != 1:
        raise ValueError(f"stream sanitizer v9 marker count={text.count(MARKER)}")
    if text.count(NEW_FETCH) != 1:
        raise ValueError(f"stream sanitizer v9 whole-manifest hook count={text.count(NEW_FETCH)}")
    if OLD_FETCH in text:
        raise ValueError("stream sanitizer v9 retained unconditional ranged manifest fetch")
    if "NUVIO_STREAM_OUTPUT_STRICT_PROBE_V8" not in text:
        raise ValueError("stream sanitizer v9 lost V8 strict verdict policy")
    if 'return verdict===true?clearPrivateProofs(item.stream):null;' not in text:
        raise ValueError("stream sanitizer v9 lost V8 fail-closed verdict")
    if 'status===403||status===404||status===410' not in text:
        raise ValueError("stream sanitizer v9 lost hard HTTP rejection")


if __name__ == "__main__":
    raise SystemExit("patch module; import apply()")
