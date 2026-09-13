#!/usr/bin/env python3
"""Deterministic rotating catalogue corpus shared by Labs and Brain/Repair.

A declared provider lane is a technical capability. A particular title is only a
catalogue sample. Therefore a successful runtime call returning zero streams is a
CATALOG_MISS and must rotate to another title rather than failing the lane.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
ROTATING_CORPUS = ROOT / ".github/triggers/rotating-popular-corpus.json"
REGRESSION_CORPUS = ROOT / ".github/triggers/nuvio-client-lab.json"
LANES = ("movie", "tv", "anime")


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_lane(fixture: dict[str, Any]) -> str:
    category = str(fixture.get("category") or "").strip().casefold()
    media_type = str(fixture.get("mediaType") or fixture.get("media_type") or "").strip().casefold()
    if category == "anime" or media_type == "anime":
        return "anime"
    if media_type in {"tv", "series"} or category in {"tv", "series"}:
        return "tv"
    return "movie"


def _normalize_row(row: dict[str, Any]) -> dict[str, Any] | None:
    if not isinstance(row, dict):
        return None
    if isinstance(row.get("fixture"), dict):
        fixture = dict(row["fixture"])
        slug = str(row.get("slug") or fixture.get("slug") or "").strip()
    else:
        fixture = dict(row)
        slug = str(fixture.get("slug") or "").strip()
    if not slug or not str(fixture.get("tmdbId") or "").strip():
        return None
    fixture["slug"] = slug
    fixture["lane"] = canonical_lane(fixture)
    return fixture


def all_fixtures() -> list[dict[str, Any]]:
    # Regression fixtures win on duplicate slugs because they may carry identity
    # collision aliases/duration constraints that the broad discovery pool omits.
    merged: dict[str, dict[str, Any]] = {}
    for raw in _load(REGRESSION_CORPUS).get("fixtures", []):
        row = _normalize_row(raw)
        if row:
            merged[row["slug"]] = row
    for raw in _load(ROTATING_CORPUS).get("fixtures", []):
        row = _normalize_row(raw)
        if row and row["slug"] not in merged:
            merged[row["slug"]] = row
    return list(merged.values())


def fixtures_by_lane(lane: str) -> list[dict[str, Any]]:
    value = str(lane).strip().casefold()
    if value not in LANES:
        raise ValueError(f"unknown lane: {lane}")
    rows = [row for row in all_fixtures() if row["lane"] == value]
    return sorted(rows, key=lambda row: row["slug"])


def fixture_by_slug(slug: str) -> dict[str, Any]:
    wanted = str(slug).strip()
    for row in all_fixtures():
        if row["slug"] == wanted:
            return dict(row)
    raise KeyError(f"unknown rotating corpus fixture: {slug}")


def default_seed() -> str:
    for name in ("NIAKVIO_CORPUS_SEED", "GITHUB_RUN_NUMBER", "GITHUB_RUN_ID", "GITHUB_SHA"):
        value = str(os.environ.get(name) or "").strip()
        if value:
            return value
    return "0"


def _rank(seed: str, lane: str, provider: str, slug: str) -> str:
    value = f"{seed}\0{lane}\0{provider.casefold()}\0{slug}".encode("utf-8")
    return hashlib.sha256(value).hexdigest()


def rotated_candidates(
    lane: str,
    *,
    seed: str | None = None,
    provider: str = "",
    exclude: Iterable[str] = (),
) -> list[dict[str, Any]]:
    resolved_seed = str(seed if seed is not None else default_seed())
    excluded = {str(value).strip() for value in exclude if str(value).strip()}
    rows = [row for row in fixtures_by_lane(lane) if row["slug"] not in excluded]
    return sorted(rows, key=lambda row: (_rank(resolved_seed, lane, provider, row["slug"]), row["slug"]))


def select_fixtures(
    lane: str,
    *,
    count: int = 1,
    seed: str | None = None,
    provider: str = "",
    attempt: int = 0,
    exclude: Iterable[str] = (),
) -> list[dict[str, Any]]:
    rows = rotated_candidates(lane, seed=seed, provider=provider, exclude=exclude)
    if not rows:
        return []
    count = max(1, int(count))
    start = max(0, int(attempt)) % len(rows)
    return [rows[(start + offset) % len(rows)] for offset in range(min(count, len(rows)))]


def classify_outcome(*, runtime_ok: bool, stream_count: int, runtime_error: bool = False, contradiction: bool = False) -> str:
    if contradiction:
        return "identity_contradiction"
    if runtime_error or not runtime_ok:
        return "technical_error"
    if int(stream_count or 0) <= 0:
        return "catalog_miss"
    return "positive"


def main() -> int:
    parser = argparse.ArgumentParser(description="Select deterministic rotating NiakVIO catalogue fixtures")
    sub = parser.add_subparsers(dest="command", required=True)

    select = sub.add_parser("select")
    select.add_argument("--lane", choices=("all", *LANES), default="all")
    select.add_argument("--seed", default=None)
    select.add_argument("--provider", default="")
    select.add_argument("--attempt", type=int, default=0)
    select.add_argument("--count-per-lane", type=int, default=1)
    select.add_argument("--exclude", action="append", default=[])
    select.add_argument("--json", action="store_true")

    show = sub.add_parser("fixture")
    show.add_argument("slug")

    args = parser.parse_args()
    if args.command == "fixture":
        print(json.dumps(fixture_by_slug(args.slug), ensure_ascii=False, sort_keys=True))
        return 0

    lanes = LANES if args.lane == "all" else (args.lane,)
    selected: list[dict[str, Any]] = []
    for lane in lanes:
        selected.extend(select_fixtures(
            lane,
            count=args.count_per_lane,
            seed=args.seed,
            provider=args.provider,
            attempt=args.attempt,
            exclude=args.exclude,
        ))
    if args.json:
        print(json.dumps(selected, ensure_ascii=False, indent=2))
    else:
        for row in selected:
            print(row["slug"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
