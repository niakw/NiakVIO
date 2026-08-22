#!/usr/bin/env python3
"""Stable public HLS master/audio playback-safety hook.

The historical implementation remains in ``hls_master_audio_preserver_impl_v1.py``.
Presentation is deliberately *not* composed here: ``apply_provider_overrides`` owns
one Core-wide final presentation pass after every playback/media layer. Keeping this
hook playback-only prevents a second override application from moving HLS wrappers
around the presentation/facts layers and changing provider bytes/cache hashes.
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

# Preserve the module API used by existing tests/tools.
AUDIO_MARKER = _IMPL.AUDIO_MARKER
SAFETY_MARKER = _IMPL.SAFETY_MARKER
HLS_INTEGRITY_MARKER = _IMPL.HLS_INTEGRITY_MARKER
GUARD = _IMPL.GUARD
TV_PREDICATE = _IMPL.TV_PREDICATE
SAFETY_WRAPPER = _IMPL.SAFETY_WRAPPER


def apply(text: str, options: dict[str, Any] | None = None, **kwargs: Any) -> str:
    return _IMPL.apply(text, options=options, **kwargs)
