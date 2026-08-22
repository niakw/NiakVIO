#!/usr/bin/env python3
"""Purstream migration adapter for the shared structured stream-facts contract.

Purstream historically encoded quality/language/codec/audio/duration/source details
inside presentation text. This adapter deliberately reuses the Core-wide extractor
instead of maintaining a second parsing implementation. It runs before Purstream's
identity guard and before the repository-wide presentation layer, so Purstream
publishes structured facts while final labels/badges remain Core-owned.
"""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
MARKER = "NUVIO_PURSTREAM_STREAM_FACTS_V1"


def _load_core_facts():
    path = HERE / "global_stream_facts_v1.py"
    spec = importlib.util.spec_from_file_location("nuvio_global_stream_facts_v1_for_purstream", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load shared stream facts layer: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_CORE_FACTS = _load_core_facts()


def apply(text: str, options: dict[str, Any] | None = None, **kwargs: Any) -> str:
    marker = f"{MARKER}:{hashlib.sha256(b'purstream-shared-facts-v1').hexdigest()[:12]}"
    if marker in text:
        return text
    output = _CORE_FACTS.apply(text, options=options, **kwargs)
    return output.rstrip() + f"\n/* {marker} */\n"
