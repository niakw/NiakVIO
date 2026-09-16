#!/usr/bin/env python3
"""V11 terminal sanitizer: recognize exact correlated path-based stream players.

Some current players encode their content identity entirely in a path such as
``/stream/<backend>/<id>/<track>`` instead of an embed/player path or query
parameter. V7's correlated-player contract rejected those even when the provider
had already attached an exact URL correlation proof.

V11 broadens only ``correlatedPlayerFallback``: an HTTP URL carrying the existing
exact private proof may be handed to outer Runtime Media Safety when its path is a
bounded opaque ``/stream/...`` player route. Ordinary unproved HTML URLs and all
normal sanitizer verdicts remain fail-closed.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
V10_PATH = ROOT / "stream_output_sanitizer_v10.py"
MANAGED_FIX_ID = "CORE.STREAM_SANITIZER.V6"
MARKER = "NUVIO_STREAM_OUTPUT_PATH_PLAYER_V11"
MARKER_COMMENT = f"/* {MARKER} */"
OLD = 'if(/\\/(?:embed|e|player|watch)(?:[-/]|$)/i.test(path))return true;\n      if(/\\/(?:shell|video|stream)(?:\\.php|[/?#.-]|$)/i.test(path)){'
NEW = 'if(/\\/(?:embed|e|player|watch)(?:[-/]|$)/i.test(path))return true;\n      if(/^\\/stream\\/(?:[^/?#]+\\/){1,4}[^/?#]+\\/?$/i.test(path))return true;\n      if(/\\/(?:shell|video|stream)(?:\\.php|[/?#.-]|$)/i.test(path)){'


def _load_v10_apply():
    spec = importlib.util.spec_from_file_location("stream_output_sanitizer_v10_for_v11", V10_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {V10_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.apply


V10_APPLY = _load_v10_apply()


def _restore_v10_source(text: str) -> str:
    source = str(text or "")
    if MARKER_COMMENT in source:
        if source.count(MARKER_COMMENT) != 1 or NEW not in source:
            raise ValueError("stream sanitizer v11 existing path-player hook malformed")
        source = source.replace(MARKER_COMMENT + "\n", "", 1).replace(NEW, OLD, 1)
    return source


def apply(text: str, options: dict[str, Any] | None = None, **kwargs: Any) -> str:
    patched = V10_APPLY(_restore_v10_source(text), options=options, **kwargs)
    if patched.count(OLD) != 1:
        raise ValueError(f"stream sanitizer v11 player-shape hook count={patched.count(OLD)}")
    patched = patched.replace(OLD, NEW, 1)
    anchor = "  function clearPrivateProofs(stream){\n"
    if patched.count(anchor) != 1:
        raise ValueError("stream sanitizer v11 marker anchor missing")
    patched = patched.replace(anchor, f"  {MARKER_COMMENT}\n" + anchor, 1)
    validate(patched)
    return patched


def validate(text: str) -> None:
    if text.count(MARKER) != 1:
        raise ValueError(f"stream sanitizer v11 marker count={text.count(MARKER)}")
    if text.count(NEW) != 1:
        raise ValueError("stream sanitizer v11 path-player rule missing")
    for inherited in (
        "NUVIO_STREAM_OUTPUT_CORRELATED_PLAYER_FALLBACK_V7",
        "NUVIO_STREAM_OUTPUT_STRICT_PROBE_V8",
        "NUVIO_STREAM_OUTPUT_FULL_MANIFEST_V9",
        "NUVIO_STREAM_OUTPUT_CORRELATED_HANDOFF_V10",
    ):
        if inherited not in text:
            raise ValueError(f"stream sanitizer v11 lost inherited policy: {inherited}")
    if 'return verdict===true?clearPrivateProofs(item.stream):null;' not in text:
        raise ValueError("stream sanitizer v11 lost ordinary strict verdict")


if __name__ == "__main__":
    raise SystemExit("patch module; import apply()")
