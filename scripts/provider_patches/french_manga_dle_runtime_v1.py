#!/usr/bin/env python3
from __future__ import annotations

import json
from typing import Any

from provider_patch_blocks import replace_managed_fix
import dle_anime_runtime_v1 as common

MANAGED_FIX_ID = "PROVIDER.FRENCH-MANGA.DLE.RUNTIME.V1"


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg = dict(options or {})
    payload = {
        "base": str(cfg.get("base") or "https://w16.french-manga.net").rstrip("/"),
        "provider": "french-manga",
        "name": str(cfg.get("name") or "French-Manga"),
        "userAgent": str(cfg.get("user_agent") or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145 Safari/537.36"),
        "maxStreams": max(1, min(int(cfg.get("max_streams") or 6), 12)),
    }
    wrapper = common.WRAPPER.replace("CONFIG_PLACEHOLDER", json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    return replace_managed_fix(text, MANAGED_FIX_ID, wrapper, data={"runtime": payload, "sharedEngine": "dle_anime_runtime_v1", "runtimeResolverRegistration": True, "fallbackOnly": True})


if __name__ == "__main__":
    raise SystemExit("patch module only")
