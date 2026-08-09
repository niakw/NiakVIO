#!/usr/bin/env python3
"""Apply the strict stream sanitizer with UTF-8 BOM-aware HLS parsing.

The V4 sanitizer intentionally validates the response body rather than trusting
an URL suffix or Content-Type. V5 keeps that policy and fixes the binary-prefix
reader case where an UTF-8 BOM (EF BB BF) becomes the mojibake string ï»¿ before
`#EXTM3U`.

Reapplication is deliberately supported: durable provider overrides may change
probe policy later. A stale V5 marker must therefore never cause a newly
regenerated V4 wrapper to skip the V5 normalization step, while an unchanged
configuration must remain byte-for-byte idempotent.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
BASE_PATH = ROOT / "stream_output_sanitizer.py"
MARKER = "NUVIO_STREAM_OUTPUT_SANITIZER_UTF8_BOM_V5"
MARKER_COMMENT = f"/* {MARKER} */"


def _load_base_apply():
    spec = importlib.util.spec_from_file_location("stream_output_sanitizer_v4", BASE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {BASE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.apply


BASE_APPLY = _load_base_apply()


def apply(text: str, options: dict[str, Any] | None = None, **kwargs: Any) -> str:
    # Let V4 decide first. If its content-addressed configuration marker already
    # matches, it returns the original text untouched. In that common case an
    # existing V5 marker proves this exact wrapper was already normalized, so
    # preserve the bytes exactly instead of moving the marker to the file tail.
    patched = BASE_APPLY(text, options=options, **kwargs)
    if patched == text and MARKER_COMMENT in text:
        return text

    # When V4 really regenerated its wrapper, an older standalone V5 marker may
    # survive outside the replaced V4 block. Remove only that marker, normalize
    # the newly generated wrapper, then append one canonical V5 marker.
    patched = patched.replace(MARKER_COMMENT, "").rstrip()
    source = 'replace(/^\\uFEFF/,"").trimStart()'
    target = 'replace(/^(?:\\uFEFF|\\u00EF\\u00BB\\u00BF)/,"").trimStart()'
    if target not in patched:
        if source not in patched:
            raise ValueError("stream sanitizer HLS normalization hook not found")
        patched = patched.replace(source, target, 1)

    return patched.rstrip() + f"\n{MARKER_COMMENT}\n"
