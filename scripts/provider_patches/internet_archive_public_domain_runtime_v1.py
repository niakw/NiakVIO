#!/usr/bin/env python3
"""Internet Archive binding for the shared explicit-public-domain archive Lego."""
from __future__ import annotations

from typing import Any

from open_archive_public_domain_runtime_common import MARKER, apply_runtime

MANAGED_FIX_ID = "PROVIDER.INTERNET-ARCHIVE.OPEN_ARCHIVE.RUNTIME.V1"


def apply(text: str, options: dict[str, Any] | None = None, **_kwargs: Any) -> str:
    return apply_runtime(text, managed_fix_id=MANAGED_FIX_ID, options=options)


if __name__ == "__main__":
    raise SystemExit("patch module only")
