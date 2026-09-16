#!/usr/bin/env python3
from __future__ import annotations
from typing import Any
import non_display_recovery_html_security_v3 as common

MANAGED_FIX_ID = "PROVIDER.SEKAI.NONDISPLAY.HTML.SECURITY.V3"
MARKER = common.MARKER

def apply(text: str, options: dict[str, Any] | None = None, **kwargs: Any) -> str:
    return common.apply_security(text, managed_fix_id=MANAGED_FIX_ID, provider="sekai", **kwargs)
