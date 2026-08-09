#!/usr/bin/env python3
"""Apply the strict stream sanitizer with UTF-8 BOM-aware HLS parsing.

The V4 sanitizer intentionally validates the response body rather than trusting
an URL suffix or Content-Type. V5 keeps that policy and fixes the binary-prefix
reader case where an UTF-8 BOM (EF BB BF) becomes the mojibake string ï»¿ before
`#EXTM3U`.

Reapplication is deliberately supported: durable provider overrides may change
probe policy later. A stale V5 marker must therefore never cause a newly
regenerated V4 wrapper to skip the V5 normalization step.
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
    # Remove an old standalone V5 marker before regenerating the configurable
    # V4 body. Otherwise BASE_APPLY can replace the V4 wrapper while leaving
    # this marker behind, making V5 incorrectly believe the new body is already
    # BOM-normalized.
    clean = text.replace(MARKER_COMMENT, "").rstrip()
    patched = BASE_APPLY(clean, options=options, **kwargs)

    source = 'replace(/^\\uFEFF/,"").trimStart()'
    target = 'replace(/^(?:\\uFEFF|\\u00EF\\u00BB\\u00BF)/,"").trimStart()'
    if target not in patched:
        if source not in patched:
            raise ValueError("stream sanitizer HLS normalization hook not found")
        patched = patched.replace(source, target, 1)

    return patched.rstrip() + f"\n{MARKER_COMMENT}\n"
