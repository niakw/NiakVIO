#!/usr/bin/env python3
"""Remove previously published global media-safety wrappers before reapplying the current engine.

The media-safety wrapper is content-addressed but keeps a stable marker name. Older
published providers can therefore carry a field-safety-v1/v2 implementation forever
if the current patcher simply sees the marker and exits. This migration is deliberately
provider-agnostic: every existing global runtime media-safety wrapper is removed, then
the normal hls_master_audio_preserver_v1 patch appends exactly one current wrapper.
"""
from __future__ import annotations

from typing import Any

SAFETY_PREFIX = "/* NUVIO_GLOBAL_RUNTIME_MEDIA_SAFETY_V1:"
SAFETY_CALL = '})(typeof globalThis!=="undefined"?globalThis:this,'
MIGRATION_MARKER = "NUVIO_RUNTIME_MEDIA_SAFETY_MIGRATION_V1"


def _strip_safety_wrappers(text: str) -> tuple[str, int]:
    cursor = 0
    parts: list[str] = []
    removed = 0
    while True:
        start = text.find(SAFETY_PREFIX, cursor)
        if start < 0:
            parts.append(text[cursor:])
            break
        marker_end = text.find("*/", start)
        call = text.find(SAFETY_CALL, marker_end + 2 if marker_end >= 0 else start)
        end = text.find(");", call + len(SAFETY_CALL)) if call >= 0 else -1
        if marker_end < 0 or call < 0 or end < 0:
            raise ValueError("unterminated global runtime media safety wrapper")
        parts.append(text[cursor:start])
        cursor = end + 2
        removed += 1
    return "".join(parts), removed


def apply(text: str, options: dict[str, Any] | None = None, **kwargs: Any) -> str:
    output, removed = _strip_safety_wrappers(text)
    if MIGRATION_MARKER not in output:
        output = output.rstrip() + f"\n/* {MIGRATION_MARKER} */\n"
    return output
