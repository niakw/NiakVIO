#!/usr/bin/env python3
"""Content-addressed Provider v3 filename policy by materialization context."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any


def matches_provider_v3_filename(
    provider_id: str,
    path: str | Path,
    sha256: str,
    materialization: dict[str, Any] | None,
) -> bool:
    pid = str(provider_id or "").strip().casefold()
    name = Path(path).name
    digest = str(sha256 or "").strip().casefold()
    if not pid or not re.fullmatch(r"[0-9a-f]{64}", digest):
        return False

    report = materialization if isinstance(materialization, dict) else {}
    is_workspace = (
        report.get("publication") is False
        and str(report.get("context") or "").strip().casefold() == "workspace"
    )
    if is_workspace:
        # Raw materialization is source-agnostic: provider + content digest.
        return name == f"{pid}-{digest[:16]}.js"

    # Published/release bytes remain source-qualified and content-addressed.
    expected = rf"{re.escape(pid)}--[A-Za-z0-9._-]+--{digest[:16]}\.js"
    return re.fullmatch(expected, name) is not None
