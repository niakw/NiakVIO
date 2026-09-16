#!/usr/bin/env python3
from __future__ import annotations
from typing import Any
import non_display_recovery_followup_v2 as common

MANAGED_FIX_ID = "PROVIDER.ANIMESAMA-CO.NONDISPLAY.RECOVERY.V2"
MARKER = common.MARKER

def apply(text: str, options: dict[str, Any] | None = None, **kwargs: Any) -> str:
    cfg = dict(options or {}); cfg["provider"] = "animesama-co"
    return common.apply(text, cfg, **kwargs)
