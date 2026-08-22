#!/usr/bin/env python3
"""Compose Core-global stream facts with Purstream-specific identity validation.

The structured facts layer is shared by every provider. Purstream keeps only its
provider-specific episodic duration/identity validation here. Final user-facing
formatting and badges remain entirely owned by the repository-wide Core layer.
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


_FACTS = _load("global_stream_facts_v1.py", "nuvio_global_stream_facts_v1")
_IDENTITY = _load("purstream_tv_identity_impl_v3.py", "nuvio_purstream_tv_identity_impl_v3")
MARKER = _IDENTITY.MARKER


def apply(source: str, options: dict[str, Any] | None = None, **kwargs: Any) -> str:
    with_facts = _FACTS.apply(source, options=options, **kwargs)
    return _IDENTITY.apply(with_facts, options=options, **kwargs)
