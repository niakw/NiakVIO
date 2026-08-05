#!/usr/bin/env python3
"""Expose the wrapped catalogue function for catalogue-only unit tests.

Playback still uses the strict outer wrapper. Tests that only validate search and
catalogue recovery can intentionally unwrap strict media adapters without
bypassing the provider's catalogue recovery layer.
"""
from __future__ import annotations

from typing import Any

MARKER = "NUVIO_EXPOSE_STRICT_WRAPPER_ORIGINAL_V1"


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    del options
    if MARKER in text:
        return text
    replacements = {
        "wrap.__nuvioTvDirectV2=true;obj[key]=wrap;":
            "wrap.__nuvioTvDirectV2=true;wrap.__nuvioOriginal=old;obj[key]=wrap;",
        "wrap.__nuvioTargetMediaV3=true;obj[key]=wrap;":
            "wrap.__nuvioTargetMediaV3=true;wrap.__nuvioOriginal=old;obj[key]=wrap;",
    }
    patched = text
    for source, target in replacements.items():
        patched = patched.replace(source, target)
    return patched.rstrip() + f"\n/* {MARKER} */\n"
