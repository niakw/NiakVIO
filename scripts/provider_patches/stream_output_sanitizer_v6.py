#!/usr/bin/env python3
"""Harden V5 all-URL probing and preserve terminal wrapper order.

V5 treats ``maxProbes`` as a probing budget, but rows beyond that budget are
returned unchanged even when ``probe_all_urls`` is true. That is acceptable for
best-effort probing, but not for a strict publication boundary: every published
row must either have media proof or be discarded.

A second subtlety matters on durable/LKG rematerialization. Some target-media
profiles deliberately remove their old wrapper and append a fresh one. If an
already-materialized sanitizer is left in place, the new target-media wrapper is
installed after it and therefore becomes the outer wrapper at runtime. The final
media URL then bypasses the terminal sanitizer entirely. V6 detects that stale
textual order, removes only its own sanitizer wrapper/markers, and lets V5
rebuild it after target-media. This keeps reapplication deterministic without
weakening fail-closed probing or adding provider-specific behavior.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
V5_PATH = ROOT / "stream_output_sanitizer_v5.py"
MARKER = "/* NUVIO_STREAM_OUTPUT_SANITIZER_ALL_URL_FAIL_CLOSED_V6 */"
OLD = "if(!item.probe)return item.stream;"
NEW = "if(!item.probe)return config.probeAllUrls?null:item.stream;"
SANITIZER_PREFIX = "/* NUVIO_STREAM_OUTPUT_SANITIZER_V4:"
SANITIZER_CALL = '})(typeof globalThis!=="undefined"?globalThis:this,'
V5_MARKERS = (
    "/* NUVIO_STREAM_OUTPUT_SANITIZER_UTF8_BOM_V5 */",
    "/* NUVIO_STREAM_OUTPUT_HLS_HTML_REPAIR_V7 */",
)
TARGET_MEDIA_MARKERS = (
    "/* NUVIO_TV_TARGET_MEDIA_V3:",
    "/* NUVIO_TV_TARGET_MEDIA_V4 */",
    "/* NUVIO_TV_TARGET_MEDIA_V5_PLAYBACK_CONTEXT */",
    "/* NUVIO_TV_TARGET_MEDIA_HLS_PROOF_V6 */",
)


def _load_v5_apply():
    spec = importlib.util.spec_from_file_location("stream_output_sanitizer_v5_for_v6", V5_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {V5_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.apply


V5_APPLY = _load_v5_apply()


def _latest_target_media_position(text: str) -> int:
    return max((text.rfind(marker) for marker in TARGET_MEDIA_MARKERS), default=-1)


def _sanitizer_position(text: str) -> int:
    return text.find(SANITIZER_PREFIX)


def _needs_relocation(text: str) -> bool:
    sanitizer = _sanitizer_position(text)
    target = _latest_target_media_position(text)
    return sanitizer >= 0 and target > sanitizer


def _strip_existing_sanitizer(text: str) -> str:
    """Remove the existing V4/V5/V6 sanitizer materialization only.

    The wrapper boundary is stable because the base sanitizer is emitted as one
    IIFE. Other provider/global wrappers are preserved byte-for-byte.
    """
    output = text
    removed = 0
    while True:
        start = output.find(SANITIZER_PREFIX)
        if start < 0:
            break
        call = output.find(SANITIZER_CALL, start)
        end = output.find(");", call) if call >= 0 else -1
        if call < 0 or end < 0:
            raise ValueError("unterminated stream sanitizer wrapper during relocation")
        output = (output[:start] + output[end + 2 :]).rstrip()
        removed += 1
    if removed == 0:
        raise ValueError("stream sanitizer relocation requested without wrapper")
    for marker in (*V5_MARKERS, MARKER):
        output = output.replace(marker, "")
    return output.rstrip()


def apply(text: str, options: dict[str, Any] | None = None, **kwargs: Any) -> str:
    cfg = dict(options or {})
    if not bool(cfg.get("probe_all_urls")):
        raise ValueError("stream sanitizer v6 requires probe_all_urls=true")
    if int(cfg.get("max_probes") or 0) <= 0:
        raise ValueError("stream sanitizer v6 requires max_probes>0")

    relocated = _needs_relocation(text)
    source = _strip_existing_sanitizer(text) if relocated else text

    # V5 owns the content-addressed configuration. Always let it run first so
    # changing blocked paths or probe policy cannot be hidden by a static V6
    # marker from an older materialization.
    patched = V5_APPLY(source, options=cfg, **kwargs)
    if not relocated and patched == text and MARKER in text:
        return text

    patched = patched.replace(MARKER, "").rstrip()
    if NEW not in patched:
        if OLD not in patched:
            raise ValueError("stream sanitizer all-URL overflow hook not found")
        patched = patched.replace(OLD, NEW, 1)

    # The actual sanitizer IIFE—not a trailing compatibility marker—must be
    # installed after the latest target-media wrapper so final media is probed.
    sanitizer = _sanitizer_position(patched)
    target = _latest_target_media_position(patched)
    if sanitizer < 0 or (target >= 0 and sanitizer <= target):
        raise ValueError(
            f"stream sanitizer terminal order invalid: sanitizer={sanitizer} target_media={target}"
        )

    return patched.rstrip() + "\n" + MARKER + "\n"


if __name__ == "__main__":
    raise SystemExit("patch module; import apply()")
