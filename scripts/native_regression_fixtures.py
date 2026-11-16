#!/usr/bin/env python3
"""Shared mandatory native regression fixtures.

These fixtures are additive to the rotating movie/tv/anime discovery reserve.
They are not allowed to replace ordinary catalogue sampling, and a prior
positive in the same lane must not skip them.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / ".github" / "triggers" / "nuvio-client-lab.json"


def _load() -> dict[str, Any]:
    data = json.loads(CONFIG.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise RuntimeError("native lab config must be an object")
    return data


def mandatory_fixture_slugs() -> list[str]:
    data = _load()
    acceptance = data.get("native_reader_acceptance")
    if not isinstance(acceptance, dict):
        raise RuntimeError("native_reader_acceptance missing")
    values = acceptance.get("mandatory_regression_fixtures") or []
    if not isinstance(values, list):
        raise RuntimeError("mandatory_regression_fixtures must be a list")
    slugs = [str(value or "").strip() for value in values if str(value or "").strip()]
    if len(slugs) != len(set(slugs)):
        raise RuntimeError("duplicate mandatory native regression fixture")
    known = {
        str(row.get("slug") or "").strip()
        for row in data.get("fixtures") or []
        if isinstance(row, dict)
    }
    missing = sorted(set(slugs) - known)
    if missing:
        raise RuntimeError("unknown mandatory native regression fixtures: " + ",".join(missing))
    return slugs


def fixture_row(slug: str) -> dict[str, Any]:
    for row in _load().get("fixtures") or []:
        if isinstance(row, dict) and str(row.get("slug") or "").strip() == slug:
            fixture = row.get("fixture")
            if not isinstance(fixture, dict):
                raise RuntimeError(f"{slug}: fixture object missing")
            return {"slug": slug, **fixture}
    raise KeyError(slug)


def mandatory_fixture_rows() -> list[dict[str, Any]]:
    return [fixture_row(slug) for slug in mandatory_fixture_slugs()]


def main() -> int:
    for slug in mandatory_fixture_slugs():
        print(slug)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
