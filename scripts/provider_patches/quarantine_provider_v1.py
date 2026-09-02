#!/usr/bin/env python3
"""Fail-safe provider quarantine as one owned Core Lego.

The quarantine never replaces or rewrites ProviderBase/provider DATA. It owns one
STARTFIX/CLOSEFIX block which makes the already-composed provider inert at runtime.
"""
from __future__ import annotations

from typing import Any

from provider_patch_blocks import replace_managed_fix

MARKER = "NUVIO_PROVIDER_QUARANTINE_V1"
MANAGED_FIX_ID = "CORE.PROVIDER_QUARANTINE.V1"


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg = dict(options or {})
    reason = str(cfg.get("reason") or "content_identity_mismatch").strip()
    wrapper = f'''/* {MARKER}: {reason} */
;(function(g){{
  "use strict";
  async function quarantinedGetStreams(){{return [];}}
  try{{if(g)g.getStreams=quarantinedGetStreams}}catch(_e){{}}
  try{{if(typeof module!=="undefined"&&module&&module.exports)module.exports.getStreams=quarantinedGetStreams}}catch(_e){{}}
  try{{if(typeof exports!=="undefined")exports.getStreams=quarantinedGetStreams}}catch(_e){{}}
}})(typeof globalThis!=="undefined"?globalThis:this);'''
    return replace_managed_fix(
        text,
        MANAGED_FIX_ID,
        wrapper,
        data={"reason": reason, "mode": "terminal-provider-quarantine"},
    )


if __name__ == "__main__":
    raise SystemExit("patch module; import apply()")
