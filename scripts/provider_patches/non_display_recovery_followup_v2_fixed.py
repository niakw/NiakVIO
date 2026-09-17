#!/usr/bin/env python3
"""Syntax-corrected renderer for the non-display V2 clean-room runtime."""
from __future__ import annotations

import json
from typing import Any
from provider_patch_blocks import replace_managed_fix
import non_display_recovery_followup_v2 as base

MARKER = base.MARKER
SUPPORTED = base.SUPPORTED
_BAD_NEKO_CLOSE = 'if(rows.length)return rows}}}return[]}'
_GOOD_NEKO_CLOSE = 'if(rows.length)return rows}}return[]}'


def corrected_wrapper() -> str:
    source = base.WRAPPER
    count = source.count(_BAD_NEKO_CLOSE)
    if count != 1:
        raise ValueError(f"non-display V2 Neko syntax anchor count={count}, expected=1")
    fixed = source.replace(_BAD_NEKO_CLOSE, _GOOD_NEKO_CLOSE, 1)
    if _BAD_NEKO_CLOSE in fixed:
        raise ValueError("non-display V2 Neko syntax anchor remains")
    return fixed


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg = dict(options or {})
    provider = str(cfg.get("provider") or "").strip().casefold().replace("_", "-")
    if provider not in SUPPORTED:
        raise ValueError(f"unsupported V2 non-display recovery provider: {provider!r}")
    defaults = {
        "animesama-co": "https://animesama.co",
        "neko-sama": "https://animes-sama.su",
        "sekai": "https://sekai.one",
        "voiranime-rip": "https://voiranime.rip",
    }
    payload = {
        "provider": provider,
        "base": str(cfg.get("base") or defaults[provider]).rstrip("/"),
        "userAgent": str(cfg.get("user_agent") or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145 Safari/537.36"),
        "maxStreams": max(1, min(int(cfg.get("max_streams") or 4), 8)),
    }
    fix_id = "PROVIDER." + provider.upper() + ".NONDISPLAY.RECOVERY.V2"
    wrapper = corrected_wrapper().replace("CONFIG_PLACEHOLDER", json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    return replace_managed_fix(text, fix_id, wrapper, data={
        "runtime": payload,
        "scope": "remaining-live-non-display-followup",
        "upstreamJsExecuted": False,
        "runtimeResolverRegistration": True,
        "sibnetShellResolution": True,
        "syntaxCorrection": "single-extra-neko-close-v1",
        "evidenceRuns": [35129779152, 35129997763, 35130125165, 35130324423, 35131129956],
    })
