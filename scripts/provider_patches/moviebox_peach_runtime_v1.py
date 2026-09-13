#!/usr/bin/env python3
"""MovieBox Hub-46 runtime via the clean Peach encrypted TMDB endpoint.

This adapter intentionally uses only the MovieBox lane exposed by the Peach
backend. It does not fall back to unrelated provider paths, so a positive row
remains attributable to MovieBox. The endpoint is direct TMDB identity:
  /moviebox/movie/<tmdb>
  /moviebox/tv/<tmdb>/<season>/<episode>
"""
from __future__ import annotations

import json
from typing import Any

from provider_patch_blocks import replace_managed_fix
from peachify_runtime_v1 import WRAPPER

MANAGED_FIX_ID = "PROVIDER.MOVIEBOX.PEACH.RUNTIME.V1"
MARKER = "NIAKVIO_MOVIEBOX_PEACH_RUNTIME_V1"


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg = dict(options or {})
    payload = {
        "keyHex": str(
            cfg.get("key_hex")
            or "a8f2a1b5e9c470814f6b2c3a5d8e7f9c1a2b3c4d5e3f7a8b8cad1e2d0a4d5c5d"
        ),
        "origin": str(cfg.get("origin") or "https://peachify.top"),
        "referer": str(cfg.get("referer") or "https://peachify.top/"),
        "userAgent": str(
            cfg.get("user_agent")
            or "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 Chrome/124 Mobile Safari/537.36"
        ),
        "servers": cfg.get("servers")
        or [{"label": "MovieBox", "base": "https://uwu.eat-peach.sbs", "path": "moviebox"}],
    }
    wrapper = WRAPPER.replace(
        "CONFIG_PLACEHOLDER",
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
    )
    # Keep the shared audited crypto implementation, but expose MovieBox
    # branding/identity to the downstream stream presentation layer.
    wrapper = wrapper.replace('name:"Peachify | "+server.label', 'name:"MovieBox | "+server.label')
    wrapper = wrapper.replace('title:"Peachify | "+server.label', 'title:"MovieBox | "+server.label')
    wrapper = wrapper.replace('provider:"peachify"', 'provider:"moviebox"')
    wrapper = wrapper.replace("/* NIAKVIO_PEACHIFY_RUNTIME_V1 */", f"/* {MARKER} */")
    return replace_managed_fix(
        text,
        MANAGED_FIX_ID,
        wrapper,
        data={
            "runtime": payload,
            "crypto": "pure-js-aes-256-gcm",
            "identity": "tmdb-direct",
            "provider": "moviebox",
            "crossProviderFallback": False,
        },
    )


if __name__ == "__main__":
    raise SystemExit("patch module only")
