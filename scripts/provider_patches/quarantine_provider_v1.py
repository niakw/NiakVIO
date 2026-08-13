#!/usr/bin/env python3
"""Replace a proven content-mismatch provider with a fail-safe empty export.

This is deliberately stronger than a manifest activation flag. Nuvio clients
may preserve an existing local enabled state across a manifest refresh, so a
provider which has returned unrelated content must also be inert at runtime.
"""
from __future__ import annotations

from typing import Any

MARKER = "NUVIO_PROVIDER_QUARANTINE_V1"


def apply(_text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    cfg = dict(options or {})
    reason = str(cfg.get("reason") or "content_identity_mismatch").strip()
    return f'''/* {MARKER}: {reason} */
"use strict";
async function getStreams(){{return [];}}
if(typeof globalThis!=="undefined")globalThis.getStreams=getStreams;
if(typeof module!=="undefined"&&module&&module.exports)module.exports={{getStreams:getStreams}};
'''


if __name__ == "__main__":
    raise SystemExit("patch module; import apply()")
