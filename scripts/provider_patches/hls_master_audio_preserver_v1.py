#!/usr/bin/env python3
"""Compose playback safety with the final shared stream presentation layer.

The historical HLS/audio/runtime-safety implementation is retained byte-for-byte
in ``hls_master_audio_preserver_impl_v1.py``. This stable public hook normalizes
the layer stack before applying playback safety, then materializes exactly one
common NiakVIO presentation wrapper as the final outer layer.

Presentation is therefore outside playback validation: it can decorate only rows
that survived the real media guards and it never rewrites URL/headers. Removing
an existing presentation wrapper before re-running the inner HLS compositor also
keeps repeated override application byte-identical for stable hashes/cache keys.
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
_PRESENTATION = _load("global_stream_presentation_v1.py", "nuvio_global_stream_presentation_v1")

# Preserve the module API used by existing tests/tools.
AUDIO_MARKER = _IMPL.AUDIO_MARKER
SAFETY_MARKER = _IMPL.SAFETY_MARKER
HLS_INTEGRITY_MARKER = _IMPL.HLS_INTEGRITY_MARKER
GUARD = _IMPL.GUARD
TV_PREDICATE = _IMPL.TV_PREDICATE
SAFETY_WRAPPER = _IMPL.SAFETY_WRAPPER


def apply(text: str, options: dict[str, Any] | None = None, **kwargs: Any) -> str:
    # Normalize the outer presentation layer away before asking the historical
    # HLS compositor to reason about tail ordering. Otherwise the inner helper
    # quite correctly moves HLS integrity behind that later wrapper on a second
    # application, after which presentation moves itself back to the end. The
    # semantics stay equal but bytes/hash change. Starting from the same inner
    # stack makes the whole composed transform strictly idempotent.
    without_presentation = _PRESENTATION._strip_existing(text)
    playback_safe = _IMPL.apply(without_presentation, options=options, **kwargs)

    # Metadata presentation is optional/bounded and may never become a playback
    # dependency. Keep its timeout short even when a provider raises HLS bounds.
    return _PRESENTATION.apply(
        playback_safe,
        options={"tmdb_timeout_ms": 1200},
        **kwargs,
    )
