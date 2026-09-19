#!/usr/bin/env python3
"""Build the three global adaptive Lab fixture pools from TMDB.

Policy: one movie list, one TV-series list, one anime list. Every row is between
2010 and current-year-1. Native Labs consume one title at a time and only rotate
on a clean zero-stream result; technical/runtime/identity errors never trigger
fixture rotation.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

API = "https://api.themoviedb.org/3"
LANES = ("movie", "tv", "anime")


def _token() -> tuple[str, dict[str, str]]:
    bearer = os.environ.get("TMDB_ACCESS_TOKEN", "").strip()
    api_key = os.environ.get("TMDB_API_KEY", "").strip()
    if bearer:
        return "", {"Authorization": f"Bearer {bearer}", "Accept": "application/json"}
    if api_key:
        return api_key, {"Accept": "application/json"}
    raise SystemExit("TMDB_API_KEY or TMDB_ACCESS_TOKEN is required")


def get(path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    api_key, headers = _token()
    query = dict(params or {})
    if api_key:
        query["api_key"] = api_key
    url = f"{API}{path}?{urllib.parse.urlencode(query, doseq=True)}"
    request = urllib.request.Request(url, headers=headers)
    last: Exception | None = None
    for attempt in range(4):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception as error:  # noqa: BLE001 - bounded external API retry
            last = error
            if attempt == 3:
                break
            time.sleep(1.0 + attempt)
    raise RuntimeError(f"TMDB request failed: {path}: {last}")


def slugify(value: str) -> str:
    text = value.casefold().encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text or "tmdb"


def year_from(value: str) -> int:
    try:
        return int(str(value)[:4])
    except Exception:
        return 0


def discover_year(lane: str, year: int) -> list[dict[str, Any]]:
    if lane == "movie":
        path = "/discover/movie"
        params = {
            "language": "en-US",
            "sort_by": "vote_count.desc",
            "primary_release_date.gte": f"{year}-01-01",
            "primary_release_date.lte": f"{year}-12-31",
            "vote_count.gte": 150,
            "include_adult": "false",
            "page": 1,
        }
    else:
        path = "/discover/tv"
        params = {
            "language": "en-US",
            "sort_by": "vote_count.desc",
            "first_air_date.gte": f"{year}-01-01",
            "first_air_date.lte": f"{year}-12-31",
            "vote_count.gte": 80,
            "include_null_first_air_dates": "false",
            "page": 1,
        }
        if lane == "tv":
            params["without_genres"] = "16"
        else:
            params["with_genres"] = "16"
            params["with_origin_country"] = "JP"
    return list(get(path, params).get("results") or [])


def episode_one(tv_id: int) -> tuple[int, str] | None:
    try:
        season = get(f"/tv/{tv_id}/season/1", {"language": "en-US"})
    except Exception:
        return None
    episodes = [row for row in season.get("episodes") or [] if isinstance(row, dict)]
    episode = next((row for row in episodes if int(row.get("episode_number") or 0) == 1), None)
    if not episode:
        return None
    runtime = int(episode.get("runtime") or 0)
    air_date = str(episode.get("air_date") or "")
    return runtime, air_date


def movie_row(item: dict[str, Any], year: int) -> dict[str, Any] | None:
    title = str(item.get("title") or item.get("original_title") or "").strip()
    tmdb_id = int(item.get("id") or 0)
    release_year = year_from(item.get("release_date") or "")
    if not title or tmdb_id <= 0 or release_year != year:
        return None
    return {
        "slug": f"{slugify(title)}-{release_year}",
        "tmdbId": str(tmdb_id),
        "mediaType": "movie",
        "category": "movie",
        "title": title,
        "year": release_year,
    }


def tv_row(item: dict[str, Any], lane: str, year: int) -> dict[str, Any] | None:
    title = str(item.get("name") or item.get("original_name") or "").strip()
    tmdb_id = int(item.get("id") or 0)
    first_year = year_from(item.get("first_air_date") or "")
    if not title or tmdb_id <= 0 or first_year != year:
        return None
    episode = episode_one(tmdb_id)
    if not episode:
        return None
    runtime, _ = episode
    row = {
        "slug": f"{slugify(title)}-{first_year}-s01e01",
        "tmdbId": str(tmdb_id),
        "mediaType": "anime" if lane == "anime" else "tv",
        "category": lane,
        "title": title,
        "year": first_year,
        "season": 1,
        "episode": 1,
    }
    if runtime > 0:
        row["expectedDurationMinutes"] = runtime
    return row


def build_lane(lane: str, min_year: int, max_year: int, per_lane: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    years = list(range(max_year, min_year - 1, -1))
    # Round-robin across years prevents one fashionable release year from owning
    # the whole list while still preferring recent works within each year.
    buckets: dict[int, list[dict[str, Any]]] = {year: discover_year(lane, year) for year in years}
    cursor = {year: 0 for year in years}
    while len(rows) < per_lane:
        advanced = False
        for year in years:
            bucket = buckets[year]
            while cursor[year] < len(bucket):
                item = bucket[cursor[year]]
                cursor[year] += 1
                row = movie_row(item, year) if lane == "movie" else tv_row(item, lane, year)
                if not row or row["tmdbId"] in seen_ids:
                    continue
                seen_ids.add(row["tmdbId"])
                rows.append(row)
                advanced = True
                break
            if len(rows) >= per_lane:
                break
        if not advanced:
            break
    if len(rows) < per_lane:
        raise RuntimeError(f"TMDB corpus too small for {lane}: {len(rows)} < {per_lane}")
    return rows[:per_lane]


def validate(payload: dict[str, Any], *, min_year: int, max_year: int, per_lane: int) -> None:
    lists = payload.get("lists") or {}
    if set(lists) != set(LANES):
        raise ValueError(f"expected exactly three global lists {LANES}, got {sorted(lists)}")
    all_slugs: set[str] = set()
    for lane in LANES:
        rows = lists.get(lane) or []
        if len(rows) < per_lane:
            raise ValueError(f"{lane}: expected >= {per_lane}, got {len(rows)}")
        ids: set[str] = set()
        for row in rows:
            year = int(row.get("year") or 0)
            if not min_year <= year <= max_year:
                raise ValueError(f"{lane}: out-of-policy year {year}: {row}")
            if str(row.get("category")) != lane:
                raise ValueError(f"{lane}: category mismatch: {row}")
            if lane == "movie":
                if str(row.get("mediaType")) != "movie" or "season" in row or "episode" in row:
                    raise ValueError(f"movie row malformed: {row}")
            else:
                if int(row.get("season") or 0) != 1 or int(row.get("episode") or 0) != 1:
                    raise ValueError(f"{lane}: S01E01 required: {row}")
            tmdb_id = str(row.get("tmdbId") or "")
            slug = str(row.get("slug") or "")
            if not tmdb_id or tmdb_id in ids or not slug or slug in all_slugs:
                raise ValueError(f"duplicate/missing fixture identity: {row}")
            ids.add(tmdb_id)
            all_slugs.add(slug)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=".github/triggers/rotating-popular-corpus.json")
    parser.add_argument("--min-year", type=int, default=2010)
    parser.add_argument("--max-year", type=int, default=dt.datetime.now(dt.timezone.utc).year - 1)
    parser.add_argument("--per-lane", type=int, default=32)
    args = parser.parse_args()
    if args.min_year < 1900 or args.max_year < args.min_year:
        raise SystemExit("invalid year range")
    per_lane = max(20, min(int(args.per_lane), 60))
    payload = {
        "schema_version": 2,
        "purpose": "Three recent global Lab pools. One title at a time; rotate only after a clean zero-stream result.",
        "selection": {
            "mode": "deterministic_seeded_one_at_a_time",
            "min_year": args.min_year,
            "max_year": args.max_year,
            "global_lists": ["movie", "tv", "anime"],
            "initial_per_lane": 1,
            "clean_miss_action": "same_lane_next_random_candidate",
            "technical_error_action": "stop_and_report",
            "identity_contradiction_action": "stop_and_report",
            "positive_action": "stop_and_retain_proof",
            "fixed_batch_size": None,
            "exhaustion_action": "catalogue_unproven_not_broken",
        },
        "lists": {
            lane: build_lane(lane, args.min_year, args.max_year, per_lane)
            for lane in LANES
        },
    }
    validate(payload, min_year=args.min_year, max_year=args.max_year, per_lane=per_lane)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    counts = {lane: len(payload["lists"][lane]) for lane in LANES}
    print(f"RECENT_GLOBAL_LAB_CORPUS_OK range={args.min_year}-{args.max_year} counts={counts} one_at_a_time=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
