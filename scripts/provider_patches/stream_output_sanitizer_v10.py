#!/usr/bin/env python3
"""V10 terminal sanitizer: hand exact correlated-player proof to outer media safety.

CORE.RUNTIME_MEDIA_SAFETY.V4 is now deliberately composed outside the terminal
sanitizer. V7 predated that order and deleted ``__nuvioCorrelatedPlayerFallbackV1``
inside the sanitizer as soon as the exact player fallback was accepted. The outer
safety layer therefore saw an ordinary HTML/embed URL and correctly rejected it.

V10 preserves that private marker for exactly one path: V7's own exact-URL,
non-direct ``correlatedPlayerFallback`` acceptance. Every ordinary sanitizer path
still clears both private proof fields. The outer runtime-safety brick consumes
and clears the handoff before any stream escapes Core.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
V9_PATH = ROOT / "stream_output_sanitizer_v9.py"
MANAGED_FIX_ID = "CORE.STREAM_SANITIZER.V6"
MARKER = "NUVIO_STREAM_OUTPUT_CORRELATED_HANDOFF_V10"
MARKER_COMMENT = f"/* {MARKER} */"
OLD = "if(correlatedPlayerFallback(item.stream,item.url))return clearPrivateProofs(item.stream);"
NEW = "if(correlatedPlayerFallback(item.stream,item.url))return clearCoreProofOnly(item.stream);"
ANCHOR = "  function clearPrivateProofs(stream){\n"
HELPER = r'''  /* NUVIO_STREAM_OUTPUT_CORRELATED_HANDOFF_V10 */
  function clearCoreProofOnly(stream){
    if(stream&&typeof stream==="object"){
      try{delete stream.__nuvioCoreMediaProofV1}catch(_e){}
    }
    return stream;
  }
'''


def _load_v9_apply():
    spec = importlib.util.spec_from_file_location("stream_output_sanitizer_v9_for_v10", V9_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {V9_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.apply


V9_APPLY = _load_v9_apply()


def _restore_v9_source(text: str) -> str:
    source = str(text or "")
    if MARKER_COMMENT not in source:
        return source
    if source.count(MARKER_COMMENT) != 1:
        raise ValueError(f"stream sanitizer v10 marker count={source.count(MARKER_COMMENT)}")
    if source.count(HELPER) != 1:
        raise ValueError(f"stream sanitizer v10 helper count={source.count(HELPER)}")
    if NEW not in source:
        raise ValueError("stream sanitizer v10 correlated handoff hook missing")
    source = source.replace(HELPER, "", 1).replace(NEW, OLD, 1)
    return source


def apply(text: str, options: dict[str, Any] | None = None, **kwargs: Any) -> str:
    source = _restore_v9_source(text)
    patched = V9_APPLY(source, options=options, **kwargs)
    if patched.count(OLD) != 1:
        raise ValueError(f"stream sanitizer v10 correlated hook count={patched.count(OLD)}")
    patched = patched.replace(OLD, NEW, 1)
    if patched.count(ANCHOR) != 1:
        raise ValueError(f"stream sanitizer v10 cleanup anchor count={patched.count(ANCHOR)}")
    patched = patched.replace(ANCHOR, HELPER + ANCHOR, 1)
    validate(patched)
    return patched


def validate(text: str) -> None:
    if text.count(MARKER) != 1:
        raise ValueError(f"stream sanitizer v10 marker count={text.count(MARKER)}")
    if text.count(NEW) != 1 or OLD in text:
        raise ValueError("stream sanitizer v10 correlated handoff is not authoritative")
    if text.count("function clearCoreProofOnly(stream)") != 1:
        raise ValueError("stream sanitizer v10 handoff cleanup helper missing")
    if "NUVIO_STREAM_OUTPUT_CORRELATED_PLAYER_FALLBACK_V7" not in text:
        raise ValueError("stream sanitizer v10 lost exact correlated-player policy")
    if "NUVIO_STREAM_OUTPUT_STRICT_PROBE_V8" not in text:
        raise ValueError("stream sanitizer v10 lost strict fail-closed policy")
    if "NUVIO_STREAM_OUTPUT_FULL_MANIFEST_V9" not in text:
        raise ValueError("stream sanitizer v10 lost whole-manifest policy")
    # Only the exact correlated path may preserve the correlated marker. Ordinary
    # accepted media still exits through clearPrivateProofs().
    if 'return verdict===true?clearPrivateProofs(item.stream):null;' not in text:
        raise ValueError("stream sanitizer v10 ordinary verdict cleanup drift")
    if "delete stream.__nuvioCorrelatedPlayerFallbackV1" not in text:
        raise ValueError("stream sanitizer v10 lost ordinary private-proof cleanup")


if __name__ == "__main__":
    raise SystemExit("patch module; import apply()")
