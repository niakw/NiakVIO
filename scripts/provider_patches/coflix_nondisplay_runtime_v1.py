#!/usr/bin/env python3
"""Provider-owned v3 adapter for the shared non-display recovery runtime."""
from __future__ import annotations
from typing import Any
import non_display_recovery_runtime_v1 as shared

MANAGED_FIX_ID = "PROVIDER.COFLIX.NONDISPLAY.RECOVERY.V1"
PROVIDER_ID = "coflix"
DEFAULT_BASE = "https://coflix.wiki"

def apply(text: str, options: dict[str, Any] | None = None, **kwargs: Any) -> str:
    cfg = dict(options or {})
    cfg["provider"] = PROVIDER_ID
    cfg.setdefault("base", DEFAULT_BASE)
    return shared.apply(text, cfg, **kwargs)
