#!/usr/bin/env python3
from __future__ import annotations

from typing import Any

from tmdb_catalog_direct_embed_runtime_v1 import apply_owned

MANAGED_FIX_ID = "PROVIDER.CHILLFLIX.TMDB_CATALOG_DIRECT_EMBED.RUNTIME.V1"


def apply(text: str, options: dict[str, Any] | None = None, **kwargs: Any) -> str:
    return apply_owned(text, MANAGED_FIX_ID, options=options, **kwargs)


if __name__ == "__main__":
    raise SystemExit("patch module only")
