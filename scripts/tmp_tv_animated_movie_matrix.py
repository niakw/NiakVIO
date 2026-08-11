#!/usr/bin/env python3
from __future__ import annotations

import concurrent.futures
import json
import subprocess
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
PROBE = ROOT / "scripts" / "nuvio_tv_probe_v2.cjs"
OUTPUT = ROOT / "animated-movie-matrix.json"

TMDB_ID = "1215638"
YEAR = 2025
ALIASES = [
    ("movie_fr", "movie", "Mon ninja et moi 3"),
    ("movie_original", "movie", "Ternet Ninja 3"),
    ("movie_en", "movie", "Checkered Ninja 3"),
]


def parse_probe(stdout: str):
    for line in reversed(stdout.splitlines()):
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict) and "playable_stream_count" in value:
            return value
    return None


def run_attempt(scraper: dict, label: str, media_type: str, title: str) -> dict:
    fixture = {
        "tmdbId": TMDB_ID,
        "mediaType": media_type,
        "title": title,
        "label": f"{title} ({YEAR})",
        "year": YEAR,
        "category": "animated_movie",
        "expectedDurationMinutes": 88,
    }
    started = time.monotonic()
    try:
        proc = subprocess.run(
            ["node", str(PROBE), str(ROOT / scraper["filename"]), json.dumps(fixture, ensure_ascii=False), "{}"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=55,
            check=False,
        )
        probe = parse_probe(proc.stdout)
        if not probe:
            return {
                "label": label,
                "mediaType": media_type,
                "title": title,
                "status": "probe_error",
                "raw": 0,
                "playable": 0,
                "exit": proc.returncode,
                "duration_ms": round((time.monotonic() - started) * 1000),
            }
        raw = int(probe.get("stream_count") or probe.get("raw_stream_count") or len(probe.get("streams") or []))
        playable = int(probe.get("playable_stream_count") or 0)
        return {
            "label": label,
            "mediaType": media_type,
            "title": title,
            "status": "playable" if playable else ("returned_unplayable" if raw else "no_streams"),
            "raw": raw,
            "playable": playable,
            "duration_ms": round((time.monotonic() - started) * 1000),
            "media_kinds": sorted({str((row.get("media") or {}).get("kind") or "unknown") for row in (probe.get("streams") or []) if isinstance(row, dict)}),
        }
    except subprocess.TimeoutExpired:
        return {
            "label": label,
            "mediaType": media_type,
            "title": title,
            "status": "timeout",
            "raw": 0,
            "playable": 0,
            "duration_ms": round((time.monotonic() - started) * 1000),
        }


def test_provider(scraper: dict) -> dict:
    types = {str(x).casefold() for x in scraper.get("supportedTypes", [])}
    row = {
        "id": scraper.get("id"),
        "name": scraper.get("name"),
        "enabled": bool(scraper.get("enabled")),
        "supportedTypes": sorted(types),
        "attempts": [],
    }
    if "movie" in types:
        for label, media_type, title in ALIASES:
            attempt = run_attempt(scraper, label, media_type, title)
            row["attempts"].append(attempt)
            if attempt["playable"] > 0:
                break
    # Diagnostic only: an animated feature is still a movie. This route is run
    # solely to detect providers whose catalogue incorrectly hides feature
    # animation behind their anime path.
    if not any(a["playable"] > 0 for a in row["attempts"]) and "anime" in types:
        row["attempts"].append(run_attempt(scraper, "anime_diagnostic", "anime", "Ternet Ninja 3"))
    row["best_playable"] = max((a["playable"] for a in row["attempts"]), default=0)
    row["movie_playable"] = max((a["playable"] for a in row["attempts"] if a["mediaType"] == "movie"), default=0)
    row["anime_only_playable"] = row["movie_playable"] == 0 and any(a["mediaType"] == "anime" and a["playable"] > 0 for a in row["attempts"])
    return row


def main() -> int:
    scrapers = [s for s in MANIFEST.get("scrapers", []) if isinstance(s, dict) and ("movie" in {str(x).casefold() for x in s.get("supportedTypes", [])} or "anime" in {str(x).casefold() for x in s.get("supportedTypes", [])})]
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        rows = list(pool.map(test_provider, scrapers))

    rows.sort(key=lambda r: (-int(r["movie_playable"] > 0), -r["movie_playable"], str(r["id"]).casefold()))
    movie_playable = [r for r in rows if r["movie_playable"] > 0]
    anime_only = [r for r in rows if r["anime_only_playable"]]
    enabled_movie_playable = [r for r in movie_playable if r["enabled"]]
    statuses = Counter(a["status"] for r in rows for a in r["attempts"])
    summary = {
        "fixture": {
            "tmdbId": TMDB_ID,
            "year": YEAR,
            "french": "Mon ninja et moi 3",
            "original": "Ternet Ninja 3",
            "english": "Checkered Ninja 3",
            "expected_media_type": "movie",
        },
        "providers_tested": len(rows),
        "movie_playable_providers": len(movie_playable),
        "enabled_movie_playable_providers": len(enabled_movie_playable),
        "anime_only_playable_providers": len(anime_only),
        "movie_playable_ids": [r["id"] for r in movie_playable],
        "anime_only_playable_ids": [r["id"] for r in anime_only],
        "attempt_statuses": dict(statuses),
        "providers": rows,
    }
    OUTPUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "providers"}, ensure_ascii=False, indent=2))
    for row in movie_playable:
        wins = [f"{a['label']}:{a['playable']}" for a in row["attempts"] if a["playable"]]
        print(f"PLAYABLE {row['id']} enabled={row['enabled']} {' '.join(wins)}")
    for row in anime_only:
        print(f"ANIME_ROUTE_ONLY {row['id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
