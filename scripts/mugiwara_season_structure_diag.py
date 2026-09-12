#!/usr/bin/env python3
"""CI-only safe diagnostic for Mugiwara season/episode mapping.

Runs the existing TMDB-aware provider probe, extracts the exact Mugiwara catalogue
page it visited, fetches that page once, and prints only season identifiers/counts
and the row/index selected by the current generic Mugiwara mapping logic. Player
and media URLs are never printed or persisted.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "scripts" / "nuvio_tv_probe_tmdb_ci.cjs"
MANIFEST = ROOT / "manifest.json"


def _provider_file() -> Path:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    for row in manifest.get("scrapers", []):
        if str(row.get("id") or "").strip().casefold() == "mugiwarastream":
            return ROOT / str(row["filename"])
    raise RuntimeError("mugiwarastream missing from manifest")


def _probe(fixture: dict) -> dict:
    proc = subprocess.run(
        ["node", str(PROBE), str(_provider_file()), json.dumps(fixture, separators=(",", ":")), "{}"],
        cwd=ROOT,
        env=os.environ.copy(),
        capture_output=True,
        text=True,
        timeout=100,
        check=False,
    )
    for line in reversed(proc.stdout.splitlines()):
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict) and "playable_stream_count" in value:
            return value
    raise RuntimeError(f"probe failed rc={proc.returncode}")


def _catalogue_url(probe: dict) -> str:
    debug = probe.get("debug") if isinstance(probe.get("debug"), dict) else {}
    for row in debug.get("fetches") or []:
        if not isinstance(row, dict):
            continue
        raw = str(row.get("url") or "")
        try:
            parsed = urlsplit(raw)
        except ValueError:
            continue
        if parsed.hostname and "mugiwara-no-streaming.com" in parsed.hostname.casefold() and "/catalogue/" in parsed.path and "/episodes/" in parsed.path:
            return raw
    return ""


def _fetch_text(url: str) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "text/html,*/*",
            "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.7",
        },
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return response.read(4_000_000).decode("utf-8", "replace")


def _next_payload(html: str) -> str:
    marker = 'self.__next_f.push([1,'
    decoder = json.JSONDecoder()
    chunks: list[str] = []
    pos = 0
    while True:
        start = html.find(marker, pos)
        if start < 0:
            break
        cursor = start + len(marker)
        while cursor < len(html) and html[cursor].isspace():
            cursor += 1
        try:
            value, used = decoder.raw_decode(html[cursor:])
        except json.JSONDecodeError:
            pos = cursor + 1
            continue
        if isinstance(value, str):
            chunks.append(value)
        pos = cursor + max(used, 1)
    return "".join(chunks)


def _anime_server(html: str) -> dict:
    payload = _next_payload(html)
    marker = '"animeServer":'
    at = payload.find(marker)
    if at < 0:
        return {}
    cursor = at + len(marker)
    while cursor < len(payload) and payload[cursor].isspace():
        cursor += 1
    try:
        value, _ = json.JSONDecoder().raw_decode(payload[cursor:])
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def _parse_value(value):
    current = value
    for _ in range(3):
        if not isinstance(current, str):
            break
        text = current.strip()
        if not text or text == "$undefined":
            break
        try:
            current = json.loads(text)
        except json.JSONDecodeError:
            break
    return current


def _episode_count(row: dict) -> int:
    langs = _parse_value(row.get("lang"))
    if not isinstance(langs, dict):
        return 0
    best = 0
    for raw in langs.values():
        servers = _parse_value(raw)
        if not isinstance(servers, list):
            continue
        for server in servers:
            episodes = _parse_value(server)
            if isinstance(episodes, list):
                best = max(best, len(episodes))
    return best


def _language_counts(row: dict) -> dict[str, int]:
    langs = _parse_value(row.get("lang"))
    if not isinstance(langs, dict):
        return {}
    out: dict[str, int] = {}
    for key, raw in langs.items():
        servers = _parse_value(raw)
        if not isinstance(servers, list):
            continue
        best = 0
        for server in servers:
            episodes = _parse_value(server)
            if isinstance(episodes, list):
                best = max(best, len(episodes))
        out[str(key)[:24]] = best
    return out


def _select(rows: list[dict], season: int, episode: int) -> dict:
    wanted = str(season)
    for row in rows:
        if row.get("notASeason"):
            continue
        if str(row.get("id") or "") == wanted and episode <= _episode_count(row):
            return {"mode": "exact-id", "rowId": wanted, "index": episode - 1}
    parts = [row for row in rows if not row.get("notASeason") and str(row.get("id") or "").split("-")[0] == wanted]
    parts.sort(key=lambda row: int((str(row.get("id") or "0").split("-") + ["0"])[1] or 0))
    if parts:
        start = 0
        for row in parts:
            count = _episode_count(row)
            if episode > start and episode <= start + count:
                return {"mode": "split-id", "rowId": str(row.get("id") or ""), "index": episode - start - 1}
            start += count
    ordered = [row for row in rows if not row.get("notASeason")]
    if 0 <= season - 1 < len(ordered) and episode <= _episode_count(ordered[season - 1]):
        return {"mode": "positional-fallback", "rowId": str(ordered[season - 1].get("id") or ""), "index": episode - 1}
    return {"mode": "none", "rowId": "", "index": None}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", required=True)
    parser.add_argument("--tmdb", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--season", type=int, required=True)
    parser.add_argument("--episode", type=int, required=True)
    args = parser.parse_args()
    fixture = {
        "tmdbId": args.tmdb,
        "mediaType": "anime",
        "title": args.title,
        "year": args.year,
        "season": args.season,
        "episode": args.episode,
        "expectedDurationMinutes": 24,
    }
    probe = _probe(fixture)
    catalogue = _catalogue_url(probe)
    if not catalogue:
        print("FIELD_MUGIWARA_SEASON_DIAG " + json.dumps({"case": args.case, "state": "no_catalogue_url"}, separators=(",", ":")))
        return 0
    server = _anime_server(_fetch_text(catalogue))
    options = server.get("options") if isinstance(server.get("options"), dict) else {}
    rows = _parse_value(options.get("saisons"))
    if not isinstance(rows, list):
        rows = []
    safe_rows = []
    typed_rows = []
    for raw in rows[:32]:
        if not isinstance(raw, dict):
            continue
        typed_rows.append(raw)
        safe_rows.append({
            "id": str(raw.get("id") or "")[:40],
            "notASeason": bool(raw.get("notASeason")),
            "episodeCount": _episode_count(raw),
            "languageCounts": _language_counts(raw),
            "name": str(raw.get("name") or raw.get("title") or "")[:100],
        })
    parsed = urlsplit(catalogue)
    result = {
        "case": args.case,
        "state": "ok" if safe_rows else "no_seasons",
        "cataloguePath": parsed.path,
        "requestedSeason": args.season,
        "requestedEpisode": args.episode,
        "selection": _select(typed_rows, args.season, args.episode),
        "seasons": safe_rows,
        "probeRaw": int(probe.get("raw_stream_count") or 0),
        "probePlayable": int(probe.get("playable_stream_count") or 0),
    }
    print("FIELD_MUGIWARA_SEASON_DIAG " + json.dumps(result, ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
