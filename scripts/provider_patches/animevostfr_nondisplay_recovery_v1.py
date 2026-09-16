#!/usr/bin/env python3
from __future__ import annotations
from typing import Any
import non_display_recovery_runtime_v1 as common

MANAGED_FIX_ID = "PROVIDER.ANIMEVOSTFR.NONDISPLAY.RECOVERY.V1"
MARKER = common.MARKER

def apply(text: str, options: dict[str, Any] | None = None, **kwargs: Any) -> str:
    cfg = dict(options or {}); cfg["provider"] = "animevostfr"
    return common.apply(text, cfg, **kwargs)
