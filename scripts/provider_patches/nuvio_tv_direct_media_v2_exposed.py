#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent


def load_apply(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.apply


DIRECT = load_apply(ROOT / "nuvio_tv_direct_media_v2.py")
EXPOSE = load_apply(ROOT / "expose_strict_wrapper_original.py")


def apply(text: str, options: dict[str, Any] | None = None, **kwargs: Any) -> str:
    return EXPOSE(DIRECT(text, options=options, **kwargs))
