#!/usr/bin/env python3
"""Apply the strict stream sanitizer with UTF-8 BOM-aware HLS parsing.

The V4 sanitizer intentionally validates the response body rather than trusting
an URL suffix or Content-Type. V5 keeps that policy and fixes the binary-prefix
reader case where an UTF-8 BOM (EF BB BF) becomes the mojibake string ï»¿ before
`#EXTM3U`.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
BASE_PATH = ROOT / "stream_output_sanitizer.py"
MARKER = "NUVIO_STREAM_OUTPUT_SANITIZER_UTF8_BOM_V5"


def _load_base_apply():
    spec = importlib.util.spec_from_file_location("stream_output_sanitizer_v4", BASE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {BASE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.apply


BASE_APPLY = _load_base_apply()


def apply(text: str, options: dict[str, Any] | None = None, **kwargs: Any) -> str:
    patched = BASE_APPLY(text, options=options, **kwargs)
    if MARKER in patched:
        return patched

    source = 'replace(/^\\uFEFF/,"").trimStart()'
    target = 'replace(/^(?:\\uFEFF|\\u00EF\\u00BB\\u00BF)/,"").trimStart()'
    if source not in patched:
        raise ValueError("stream sanitizer HLS normalization hook not found")
    patched = patched.replace(source, target, 1)
    return patched.rstrip() + f"\n/* {MARKER} */\n"
