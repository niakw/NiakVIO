#!/usr/bin/env python3
"""Content-addressed Provider v3 filename policy by execution context."""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any


def matches_provider_v3_filename(
    provider_id: str,
    path: str | Path,
    sha256: str,
    materialization: dict[str, Any] | None,
    *,
    execution_context: str | None = None,
) -> bool:
    pid = str(provider_id or "").strip().casefold()
    name = Path(path).name
    digest = str(sha256 or "").strip().casefold()
    if not pid or not re.fullmatch(r"[0-9a-f]{64}", digest):
        return False

    # The live execution context is the authority. A published tree may retain a
    # historical workspace materialization report as provenance, so that report
    # must never downgrade publication filename validation. Route-proof jobs set
    # NUVIO_PROVIDER_V3_CONTEXT=workspace explicitly; all unspecified contexts
    # fail closed to the stricter publication shape.
    context = str(
        execution_context
        if execution_context is not None
        else os.environ.get("NUVIO_PROVIDER_V3_CONTEXT", "")
    ).strip().casefold()
    if context == "workspace":
        return name == f"{pid}-{digest[:16]}.js"

    # Published/release bytes remain source-qualified and content-addressed.
    expected = rf"{re.escape(pid)}--[A-Za-z0-9._-]+--{digest[:16]}\.js"
    return re.fullmatch(expected, name) is not None
