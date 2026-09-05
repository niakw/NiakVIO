#!/usr/bin/env python3
from __future__ import annotations
from typing import Any
from anime_catalogue_runtime_common import apply_runtime
MANAGED_FIX_ID = "PROVIDER.ANIMEVOST-FR.RUNTIME.V1"
MARKER = "NIAKVIO_ANIMEVOST_FR_RUNTIME_V1"
def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    return apply_runtime(text, managed_fix_id=MANAGED_FIX_ID, marker=MARKER, defaults={"mode":"animevost_api","base":"https://animevost.fr","provider":"animevost-fr","name":"AnimeVOST.fr"}, options=options)
if __name__ == "__main__": raise SystemExit("patch module only")
