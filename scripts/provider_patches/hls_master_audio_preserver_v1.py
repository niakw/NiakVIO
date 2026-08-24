#!/usr/bin/env python3
"""Stable public HLS master/audio playback-safety hook.

The historical implementation remains in ``hls_master_audio_preserver_impl_v1.py``.
Presentation is deliberately *not* composed here: ``apply_provider_overrides`` owns
one Core-wide final presentation pass after every playback/media layer.

The historical implementation still moves the HLS integrity wrapper to the absolute
bundle tail. That was correct before Core facts/identity/presentation/security existed,
but it now makes a repeated reconstruction move HLS across Core-owned final layers.
This public adapter restores the canonical boundary without changing playback
semantics: media recovery/safety -> HLS validation -> security -> facts/identity/
presentation.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent


def _load(filename: str, module_name: str):
    path = HERE / filename
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load provider Core layer: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_IMPL = _load("hls_master_audio_preserver_impl_v1.py", "nuvio_hls_master_audio_impl_v1")

AUDIO_MARKER = _IMPL.AUDIO_MARKER
SAFETY_MARKER = _IMPL.SAFETY_MARKER
HLS_INTEGRITY_MARKER = _IMPL.HLS_INTEGRITY_MARKER
GUARD = _IMPL.GUARD
TV_PREDICATE = _IMPL.TV_PREDICATE
SAFETY_WRAPPER = _IMPL.SAFETY_WRAPPER

_CORE_FINALIZERS = (
    "NUVIO_GLOBAL_PROVIDER_SECURITY_HOOK_V1",
    "NUVIO_GLOBAL_STREAM_FACTS_V1",
    "NUVIO_GLOBAL_STREAM_IDENTITY_V1",
    "NUVIO_GLOBAL_STREAM_PRESENTATION_V1",
)


def _wrapper_bounds(text: str, marker: str) -> tuple[int, int] | None:
    start = text.find(f"/* {marker}:")
    if start < 0:
        return None
    call = text.find('})(typeof globalThis!=="undefined"?globalThis:this,', start)
    end = text.find(");", call) if call >= 0 else -1
    if call < 0 or end < 0:
        raise ValueError(f"unterminated {marker} wrapper")
    return start, end + 2


def _ensure_audio_marker_before_safety(text: str) -> str:
    marker_comment = f"/* {AUDIO_MARKER} */"
    if marker_comment in text:
        return text
    safety_start = text.find(f"/* {SAFETY_MARKER}:")
    if safety_start < 0:
        return text.rstrip() + f"\n{marker_comment}\n"
    return text[:safety_start].rstrip() + "\n" + marker_comment + "\n" + text[safety_start:].lstrip()


def _place_hls_before_core_finalizers(text: str) -> str:
    bounds = _wrapper_bounds(text, HLS_INTEGRITY_MARKER)
    if bounds is None:
        return text
    start, end = bounds
    core_positions = [
        position
        for position in (text.find(f"/* {marker}") for marker in _CORE_FINALIZERS)
        if position >= 0
    ]
    if not core_positions or start < min(core_positions):
        return text

    segment = text[start:end].strip()
    before = text[:start].rstrip()
    after = text[end:].strip()
    body = before
    if after:
        body = (body + "\n" + after) if body else after

    core_positions = [
        position
        for position in (body.find(f"/* {marker}") for marker in _CORE_FINALIZERS)
        if position >= 0
    ]
    if not core_positions:
        return body.rstrip() + "\n" + segment + "\n"
    insertion = min(core_positions)
    prefix = body[:insertion].rstrip()
    suffix = body[insertion:].lstrip()
    output = (prefix + "\n" + segment) if prefix else segment
    if suffix:
        output += "\n" + suffix
    return output.rstrip() + "\n"


def _place_safety_before_hls(text: str) -> str:
    """Keep audio-marker -> media-safety -> HLS as a deterministic generated unit."""
    bounds = _wrapper_bounds(text, SAFETY_MARKER)
    if bounds is None:
        return _ensure_audio_marker_before_safety(text)

    start, end = bounds
    safety_segment = text[start:end].strip()
    marker_comment = f"/* {AUDIO_MARKER} */"
    body = (text[:start] + text[end:]).replace(marker_comment, "").strip()

    candidates: list[int] = []
    hls_start = body.find(f"/* {HLS_INTEGRITY_MARKER}:")
    if hls_start >= 0:
        candidates.append(hls_start)
    candidates.extend(
        position
        for position in (body.find(f"/* {marker}") for marker in _CORE_FINALIZERS)
        if position >= 0
    )

    if candidates:
        insertion = min(candidates)
        prefix = body[:insertion].rstrip()
        suffix = body[insertion:].lstrip()
    else:
        prefix = body.rstrip()
        suffix = ""

    unit = marker_comment + "\n" + safety_segment
    output = (prefix + "\n" + unit) if prefix else unit
    if suffix:
        output += "\n" + suffix
    return output.rstrip() + "\n"


def apply(text: str, options: dict[str, Any] | None = None, **kwargs: Any) -> str:
    output = _IMPL.apply(text, options=options, **kwargs)
    output = _place_safety_before_hls(output)
    return _place_hls_before_core_finalizers(output)
