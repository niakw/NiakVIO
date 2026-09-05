#!/usr/bin/env python3
from __future__ import annotations
from typing import Any
from anime_catalogue_runtime_common import apply_runtime
MANAGED_FIX_ID = "PROVIDER.NEKO-SAMA.RUNTIME.V1"
MARKER = "NIAKVIO_NEKO_SAMA_RUNTIME_V1"
def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    return apply_runtime(text, managed_fix_id=MANAGED_FIX_ID, marker=MARKER, defaults={"mode":"neko_wp","base":"https://animes-sama.su","provider":"neko-sama","name":"Neko-Sama"}, options=options)
if __name__ == "__main__": raise SystemExit("patch module only")
