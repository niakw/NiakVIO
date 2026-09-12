#!/usr/bin/env python3
from __future__ import annotations
from typing import Any
from stremio_json_runtime_common import apply_runtime

MANAGED_FIX_ID = "PROVIDER.DESIFLIX.RUNTIME.V1"
MARKER = "NIAKVIO_DESIFLIX_RUNTIME_V1"


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    # Live evidence 2026-09-12: the public manifest host still serves the
    # addon but its IMDb stream routes intermittently stall/time out, while
    # the Worker mirror returns the same current catalogue promptly for both
    # movie and series lanes. Prefer the responsive mirror at runtime and
    # retain the declared official manifest host as a bounded fallback.
    return apply_runtime(
        text,
        managed_fix_id=MANAGED_FIX_ID,
        marker=MARKER,
        defaults={
            "base": "https://desiflix.stremioaddon.workers.dev",
            "fallbackBases": ["https://manifest.desitvhub.eu.org"],
            "provider": "desiflix",
            "name": "DesiFlix",
        },
        options=options,
    )


if __name__ == "__main__":
    raise SystemExit("patch module only")
