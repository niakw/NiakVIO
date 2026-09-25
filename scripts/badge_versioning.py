#!/usr/bin/env python3
"""Resolve the newest immutable NiakVIO badge catalogue/mapping snapshot."""
from __future__ import annotations
import re
from pathlib import Path

CATALOG_RE = re.compile(r"^badge_catalog_v(\d+)_complete\.json$")
MAPPING_RE = re.compile(r"^mapping_core_brain_ui_v(\d+)_complete\.json$")

def _latest(assets: Path, pattern: re.Pattern[str], label: str) -> tuple[int, Path]:
    rows=[]
    for path in assets.iterdir():
        match=pattern.match(path.name)
        if match and path.is_file():
            rows.append((int(match.group(1)),path))
    if not rows:
        raise RuntimeError(f"no versioned {label} found in {assets}")
    return max(rows,key=lambda row:row[0])

def latest_catalog(root: Path) -> tuple[int, Path]:
    return _latest(root/"assets",CATALOG_RE,"badge catalogue")

def latest_mapping(root: Path) -> tuple[int, Path]:
    return _latest(root/"assets",MAPPING_RE,"badge mapping")
