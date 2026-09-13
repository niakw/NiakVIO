#!/usr/bin/env python3
"""Deterministic adaptive catalogue corpus shared by Labs and Brain/Repair.

Canonical native-Lab policy:
- exactly three global pools: movie, tv, anime;
- every global fixture year is 2010..(current year - 1);
- select one fixture at a time;
- rotate only after a clean runtime success with zero streams;
- technical/runtime/identity errors stop rotation and remain visible.

The older regression corpus remains addressable by exact slug for targeted probes,
but it never contaminates the three global recent pools.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
ROTATING_CORPUS = ROOT / ".github/triggers/rotating-popular-corpus.json"
REGRESSION_CORPUS = ROOT / ".github/triggers/nuvio-client-lab.json"
LANES = ("movie", "tv", "anime")
MIN_GLOBAL_YEAR = 2010


def max_global_year() -> int:
    return dt.datetime.now(dt.timezone.utc).year - 1


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


def _normalize_row(row: dict[str, Any], lane_hint: str | None = None) -> dict[str, Any] | None:
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
    if lane_hint and fixture["lane"] != lane_hint:
        raise ValueError(f"fixture lane mismatch: expected={lane_hint} slug={slug} actual={fixture['lane']}")
    return fixture


def _global_lists() -> dict[str, list[dict[str, Any]]]:
    data = _load(ROTATING_CORPUS)
    if int(data.get("schema_version") or 1) >= 2 and isinstance(data.get("lists"), dict):
        raw_lists = data["lists"]
        if set(raw_lists) != set(LANES):
            raise ValueError(f"global corpus must expose exactly {LANES}; got {sorted(raw_lists)}")
        result: dict[str, list[dict[str, Any]]] = {}
        upper = max_global_year()
        for lane in LANES:
            rows: list[dict[str, Any]] = []
            for raw in raw_lists.get(lane) or []:
                row = _normalize_row(raw, lane)
                if not row:
                    continue
                year = int(row.get("year") or 0)
                if not MIN_GLOBAL_YEAR <= year <= upper:
                    raise ValueError(f"global fixture outside {MIN_GLOBAL_YEAR}-{upper}: {row['slug']} year={year}")
                if lane != "movie":
                    if int(row.get("season") or 0) <= 0 or int(row.get("episode") or 0) <= 0:
                        raise ValueError(f"episodic global fixture requires season/episode: {row['slug']}")
                rows.append(row)
            if not rows:
                raise ValueError(f"empty global corpus lane: {lane}")
            result[lane] = rows
        return result

    # Backward-compatible read for a pre-v2 branch checkout. Old rows are filtered
    # to policy years, but canonical publication must migrate to schema v2.
    result = {lane: [] for lane in LANES}
    upper = max_global_year()
    for raw in data.get("fixtures", []):
        row = _normalize_row(raw)
        if not row:
            continue
        year = int(row.get("year") or 0)
        if MIN_GLOBAL_YEAR <= year <= upper:
            result[row["lane"]].append(row)
    return result


def global_fixtures() -> list[dict[str, Any]]:
    lists = _global_lists()
    return [dict(row) for lane in LANES for row in lists[lane]]


def regression_fixtures() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for raw in _load(REGRESSION_CORPUS).get("fixtures", []):
        row = _normalize_row(raw)
        if row:
            rows.append(row)
    return rows


def all_fixtures() -> list[dict[str, Any]]:
    # Global fixtures win duplicate slugs so exact lookup used by native Labs sees
    # the same recent-row metadata as the adaptive pool. Regression-only fixtures
    # remain available for explicit targeted diagnostics.
    merged: dict[str, dict[str, Any]] = {row["slug"]: row for row in regression_fixtures()}
    for row in global_fixtures():
        merged[row["slug"]] = row
    return list(merged.values())


def fixtures_by_lane(lane: str, *, global_only: bool = True) -> list[dict[str, Any]]:
    value = str(lane).strip().casefold()
    if value not in LANES:
        raise ValueError(f"unknown lane: {lane}")
    source = global_fixtures() if global_only else all_fixtures()
    rows = [row for row in source if row["lane"] == value]
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
    rows = [row for row in fixtures_by_lane(lane, global_only=True) if row["slug"] not in excluded]
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
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(newline="\n")

    parser = argparse.ArgumentParser(description="Select adaptive NiakVIO global Lab fixtures")
    sub = parser.add_subparsers(dest="command", required=True)

    select = sub.add_parser("select")
    select.add_argument("--lane", choices=("all", *LANES), default="all")
    select.add_argument("--seed", default=None)
    select.add_argument("--provider", default="")
    select.add_argument("--attempt", type=int, default=0)
    select.add_argument("--count-per-lane", type=int, default=1)
    select.add_argument("--exclude", action="append", default=[])
    select.add_argument("--json", action="store_true")

    pool = sub.add_parser("pool")
    pool.add_argument("--lane", choices=LANES, required=True)
    pool.add_argument("--seed", default=None)
    pool.add_argument("--provider", default="")
    pool.add_argument("--json", action="store_true")

    show = sub.add_parser("fixture")
    show.add_argument("slug")

    args = parser.parse_args()
    if args.command == "fixture":
        print(json.dumps(fixture_by_slug(args.slug), ensure_ascii=False, sort_keys=True))
        return 0
    if args.command == "pool":
        rows = rotated_candidates(args.lane, seed=args.seed, provider=args.provider)
        if args.json:
            print(json.dumps(rows, ensure_ascii=False, indent=2))
        else:
            for row in rows:
                print(row["slug"])
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
