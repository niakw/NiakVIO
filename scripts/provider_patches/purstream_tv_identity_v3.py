#!/usr/bin/env python3
"""Compose Purstream structured facts with provider-specific identity validation.

Purstream first migrates its legacy presentation-heavy rows into the shared structured
facts contract. It then applies only the provider-specific episodic duration/identity
validation. Final user-facing formatting, badge selection and TMDB fallback remain
owned by the repository-wide Core presentation layer.
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
        raise RuntimeError(f"cannot load Purstream identity layer dependency: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_FACTS = _load("purstream_stream_facts_v1.py", "nuvio_purstream_stream_facts_v1")
_IDENTITY = _load("purstream_tv_identity_impl_v3.py", "nuvio_purstream_tv_identity_impl_v3")
MARKER = _IDENTITY.MARKER


def apply(source: str, options: dict[str, Any] | None = None, **kwargs: Any) -> str:
    with_facts = _FACTS.apply(source, options=options, **kwargs)
    return _IDENTITY.apply(with_facts, options=options, **kwargs)
