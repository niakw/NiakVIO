#!/usr/bin/env python3
from __future__ import annotations
from typing import Any
from stremio_json_runtime_common import apply_runtime
MANAGED_FIX_ID = "PROVIDER.PERSIANSTREMIO.RUNTIME.V1"
MARKER = "NIAKVIO_PERSIANSTREMIO_RUNTIME_V1"
def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    return apply_runtime(text, managed_fix_id=MANAGED_FIX_ID, marker=MARKER, defaults={"base":"https://persianstremio.vercel.app","provider":"persianstremio","name":"PersianStremio"}, options=options)
if __name__ == "__main__": raise SystemExit("patch module only")
