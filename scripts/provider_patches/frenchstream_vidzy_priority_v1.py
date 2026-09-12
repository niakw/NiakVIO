#!/usr/bin/env python3
"""Frenchstream movie player ordering refinement.

The exact runtime v3 is structurally correct, but its bounded movie resolver
attempted eight FSVID/Uqload variants before reaching the three currently proven
Vidzy variants. This Lego changes movie-only host order to Vidzy first; TV order
is intentionally unchanged. The existing terminal validator still requires 2xx
+ #EXTM3U and rejects /troll/master.m3u8.
"""
from __future__ import annotations

from typing import Any
from provider_patch_blocks import replace_managed_fix

MANAGED_FIX_ID = "PROVIDER.FRENCHSTREAM.VIDZY.PRIORITY.V1"
MARKER = "NIAKVIO_FRENCHSTREAM_VIDZY_PRIORITY_V1"
OLD = 'function movieRows(d){var out=[],players=d&&d.players,hosts=["premium","uqload","vidzy"],langs='
NEW = 'function movieRows(d){var out=[],players=d&&d.players,hosts=["vidzy","premium","uqload"],langs='


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    if OLD not in text:
        raise RuntimeError("Frenchstream exact runtime v3 movieRows signature not found")
    text = text.replace(OLD, NEW, 1)
    return replace_managed_fix(
        text,
        MANAGED_FIX_ID,
        f"/* {MARKER} */",
        data={
            "scope": "movie-only",
            "playerOrder": ["vidzy", "premium", "uqload"],
            "reason": "three proven historical movie terminals are Vidzy while bounded v3 stopped before reaching them",
            "terminalPolicyUnchanged": "2xx + EXTM3U; reject /troll/master.m3u8",
        },
    )


if __name__ == "__main__":
    raise SystemExit("patch module only")
