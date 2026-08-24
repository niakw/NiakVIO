#!/usr/bin/env python3
"""Temporary diagnosis wrapper for the shared native target-order patch."""
from __future__ import annotations

import importlib.util
import re
from pathlib import Path
from typing import Any

BASE_PATH = Path(__file__).with_name("native_sync_fetch_target_order_v1.py")
spec = importlib.util.spec_from_file_location("native_sync_fetch_target_order_v1_diag_base", BASE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot import native_sync_fetch_target_order_v1.py")
BASE = importlib.util.module_from_spec(spec)
spec.loader.exec_module(BASE)


def apply(source: str, options: dict[str, Any] | None = None, **kwargs: Any) -> str:
    try:
        return BASE.apply(source, options=options, **kwargs)
    except RuntimeError as exc:
        context = kwargs.get("context") if isinstance(kwargs.get("context"), dict) else {}
        provider_id = str(context.get("provider_id") or "unknown")
        signatures = re.findall(r"async\s+function\s+resolve\s*\([^)]*\)", source)
        tv_signatures = re.findall(r"async\s+function\s+tvRows\s*\([^)]*\)", source)
        facts = {
            "provider": provider_id,
            "v4": "NUVIO_TV_TARGET_MEDIA_V4" in source,
            "v5": "NUVIO_TV_TARGET_MEDIA_V5_PLAYBACK_CONTEXT" in source,
            "target_order_marker": BASE.MARKER in source,
            "serial_helper": "function serialNativeTargetRuntime()" in source,
            "ordered_targets": "function orderedTargets(values,ref)" in source,
            "ordered_rows": "function orderedNativeRows(values)" in source,
            "resolve_signatures": signatures[:4],
            "tv_rows_signatures": tv_signatures[:4],
            "context_new_resolve": BASE.CONTEXT_NEW_RESOLVE in source,
            "context_new_rows": BASE.CONTEXT_NEW_TV_ROWS in source,
        }
        raise RuntimeError(f"{exc}; diagnosis={facts}") from exc
