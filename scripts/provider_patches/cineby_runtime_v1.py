#!/usr/bin/env python3
"""Cineby clean-v3 Wings runtime Lego."""
from __future__ import annotations
from typing import Any
from provider_patch_blocks import replace_managed_fix
from provider_wings_runtime_common import render_wings_runtime

MANAGED_FIX_ID = "PROVIDER.CINEBY.WINGS.V1"
MARKER = "NIAKVIO_CINEBY_WINGS_V1"

def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg=dict(options or {})
    runtime={
      "apiBase":str(cfg.get("api_base") or "https://api.speedracelight.com"),
      "origin":str(cfg.get("origin") or "https://www.cineby.at"),
      "referer":str(cfg.get("referer") or "https://www.cineby.at/"),
      "userAgent":str(cfg.get("user_agent") or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"),
      "providerId":"cineby","providerName":"Cineby","installMarker":"__niakvioCinebyWingsV1",
      "endpoints":list(cfg.get("endpoints") or [{"label":"CDN","path":"cdn/sources-with-title"}])
    }
    return replace_managed_fix(text,MANAGED_FIX_ID,render_wings_runtime(marker=MARKER,config=runtime),data={"runtime":runtime,"family":"wings-v1","identity":"core-tmdb-title-year","legacyExecutableSeed":False})
if __name__ == "__main__": raise SystemExit("patch module only")
