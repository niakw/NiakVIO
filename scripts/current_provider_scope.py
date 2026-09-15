#!/usr/bin/env python3
"""Current NiakVIO provider scope.

Provider cardinality is data, never policy.

* ``providers/`` contains executable/active Provider v3 artifacts only.
* ``provider-disabled/`` contains disabled artifacts still visible in manifest.json.
* ``provider-old/`` is terminal archive and is not part of the current catalogue.

No caller should encode a fixed provider count (44/46/96/etc.).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ACTIVE_DIR = (ROOT / "providers").resolve()
DISABLED_DIR = (ROOT / "provider-disabled").resolve()
MANIFEST = ROOT / "manifest.json"


def cid(value: Any) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def _manifest_rows() -> list[dict[str, Any]]:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    rows = [row for row in data.get("scrapers") or [] if isinstance(row, dict)]
    ids = [cid(row.get("id")) for row in rows]
    if any(not value for value in ids):
        raise RuntimeError("current manifest contains provider row without id")
    if len(ids) != len(set(ids)):
        raise RuntimeError("current manifest contains duplicate provider ids")
    return rows


def _resolved_asset(row: dict[str, Any]) -> Path:
    filename = str(row.get("filename") or "").strip()
    if not filename:
        raise RuntimeError(f"{cid(row.get('id'))}: missing current provider filename")
    path = (ROOT / filename).resolve()
    if not path.is_file():
        raise RuntimeError(f"{cid(row.get('id'))}: current provider asset missing: {filename}")
    return path


def active_provider_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in _manifest_rows():
        if row.get("enabled") is False:
            continue
        path = _resolved_asset(row)
        if ACTIVE_DIR not in path.parents:
            raise RuntimeError(
                f"{cid(row.get('id'))}: enabled provider must live in providers/, got {path.relative_to(ROOT)}"
            )
        rows.append(row)
    return rows


def disabled_provider_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in _manifest_rows():
        if row.get("enabled") is not False:
            continue
        path = _resolved_asset(row)
        if DISABLED_DIR not in path.parents:
            raise RuntimeError(
                f"{cid(row.get('id'))}: disabled provider must live in provider-disabled/, got {path.relative_to(ROOT)}"
            )
        rows.append(row)
    return rows


def visible_provider_rows() -> list[dict[str, Any]]:
    active = active_provider_rows()
    disabled = disabled_provider_rows()
    return active + disabled


def active_provider_ids() -> set[str]:
    return {cid(row.get("id")) for row in active_provider_rows()}


def disabled_provider_ids() -> set[str]:
    return {cid(row.get("id")) for row in disabled_provider_rows()}


def visible_provider_ids() -> set[str]:
    ids = active_provider_ids() | disabled_provider_ids()
    if len(ids) != len(visible_provider_rows()):
        raise RuntimeError("visible provider identity collision")
    return ids


def active_provider_count() -> int:
    return len(active_provider_ids())


def disabled_provider_count() -> int:
    return len(disabled_provider_ids())


def visible_provider_count() -> int:
    return len(visible_provider_ids())


def assert_directory_contract() -> None:
    """Ensure the physical active folder is exactly the enabled manifest set.

    Historical duplicate files are not allowed to silently inflate or define the
    provider count. Only manifest-referenced current artifacts participate.
    """
    active_rows = active_provider_rows()
    referenced = {_resolved_asset(row).resolve() for row in active_rows}
    manifest_named = {path for path in ACTIVE_DIR.glob("*.js") if path.resolve() in referenced}
    if manifest_named != referenced:
        raise RuntimeError("providers/ current artifact set differs from enabled manifest set")
