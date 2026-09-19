#!/usr/bin/env python3
"""Branch-only manual-TV live evidence probe.

Runs one published provider bundle against one exact fixture through the existing
TMDB-aware TV probe, then emits a bounded/sanitized JSON summary.  URLs,
headers, cookies, request bodies and signed values are deliberately excluded.
This is evidence-only: a provider may legitimately be unavailable upstream.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manifest.json"
PROBE = ROOT / "scripts" / "nuvio_tv_probe_tmdb_ci.cjs"
SAFE_TEXT = re.compile(r"https?://\S+", re.I)


def clean_text(value: object, limit: int = 180) -> str:
    text = str(value or "").strip()
    text = SAFE_TEXT.sub("<url-redacted>", text)
    return text[:limit]


def cid(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def parse_probe(stdout: str) -> dict | None:
    for raw in reversed(stdout.splitlines()):
        raw = raw.strip()
        if not raw.startswith("{"):
            continue
        try:
            value = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict) and "playable_stream_count" in value:
            return value
    return None


def observed_transport_types(probe: dict) -> list[str]:
    debug = probe.get("debug") if isinstance(probe.get("debug"), dict) else {}
    rows = debug.get("fetches") if isinstance(debug.get("fetches"), list) else []
    values: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        raw = str(row.get("url") or "")
        if "api.themoviedb.org" in raw.casefold():
            continue
        try:
            parsed = urlsplit(raw)
            for key, items in parse_qs(parsed.query).items():
                if key.casefold() in {"type", "mediatype", "media_type"}:
                    for item in items:
                        item = cid(item)
                        if item in {"movie", "tv", "anime", "series"}:
                            values.add(item)
        except ValueError:
            continue
    return sorted(values)


def safe_stream(item: object) -> dict:
    if not isinstance(item, dict):
        return {}
    row = item.get("row") if isinstance(item.get("row"), dict) else {}
    media = item.get("media") if isinstance(item.get("media"), dict) else {}
    identity = item.get("identity") if isinstance(item.get("identity"), dict) else {}
    metadata_identity = item.get("metadata_identity") if isinstance(item.get("metadata_identity"), dict) else {}
    duration_identity = item.get("duration_identity") if isinstance(item.get("duration_identity"), dict) else {}
    ratio = duration_identity.get("ratio")
    if not isinstance(ratio, (int, float)):
        ratio = None
    return {
        "name": clean_text(row.get("name")),
        "title": clean_text(row.get("title")),
        "quality": clean_text(row.get("quality"), 48),
        "language": clean_text(row.get("language") or row.get("lang"), 64),
        "playable": media.get("playable") is True,
        "httpStatus": int(media.get("status") or 0),
        "kind": clean_text(media.get("kind"), 32),
        "identity": clean_text(identity.get("status"), 32),
        "identityReason": clean_text(identity.get("reason"), 80),
        "metadataIdentity": clean_text(metadata_identity.get("status"), 32),
        "durationIdentity": clean_text(duration_identity.get("status"), 32),
        "durationRatio": round(float(ratio), 3) if ratio is not None else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", required=True)
    parser.add_argument("--provider", required=True)
    parser.add_argument("--tmdb", required=True)
    parser.add_argument("--media-type", required=True, choices=["movie", "tv", "anime"])
    parser.add_argument("--title", required=True)
    parser.add_argument("--year", required=True, type=int)
    parser.add_argument("--season", type=int)
    parser.add_argument("--episode", type=int)
    parser.add_argument("--duration", type=int, required=True)
    parser.add_argument("--aliases", default="[]")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    if not (str(os.environ.get("TMDB_API_KEY") or "").strip() or str(os.environ.get("TMDB_ACCESS_TOKEN") or "").strip()):
        raise SystemExit("missing TMDB credential")

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    provider_id = cid(args.provider)
    row = next((r for r in manifest.get("scrapers", []) if isinstance(r, dict) and cid(r.get("id")) == provider_id), None)
    if not row:
        raise SystemExit(f"unknown provider {provider_id}")
    filename = str(row.get("filename") or "").strip()
    provider_path = ROOT / filename
    if not filename or not provider_path.is_file():
        raise SystemExit(f"missing provider bytes {provider_id}")

    try:
        aliases = json.loads(args.aliases)
    except json.JSONDecodeError:
        aliases = []
    if not isinstance(aliases, list):
        aliases = []

    fixture = {
        "tmdbId": str(args.tmdb),
        "mediaType": args.media_type,
        "title": args.title,
        "year": args.year,
        "category": args.media_type,
        "expectedDurationMinutes": args.duration,
        "aliases": [str(v) for v in aliases if str(v).strip()][:12],
    }
    if args.season is not None:
        fixture["season"] = args.season
    if args.episode is not None:
        fixture["episode"] = args.episode

    command = ["node", str(PROBE), str(provider_path), json.dumps(fixture, separators=(",", ":")), "{}"]
    try:
        proc = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=95, check=False, env=os.environ.copy())
    except subprocess.TimeoutExpired:
        summary = {
            "case": args.case,
            "provider": provider_id,
            "fixtureType": args.media_type,
            "probeState": "timeout",
            "raw": 0,
            "playable": 0,
            "verified": 0,
            "contradictions": 0,
            "streams": [],
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("FIELD_MANUAL_TV_LIVE " + json.dumps(summary, ensure_ascii=False, separators=(",", ":")))
        return 0

    probe = parse_probe(proc.stdout)
    if probe is None:
        print(clean_text(proc.stderr[-1200:]), file=sys.stderr)
        return 3

    streams = [safe_stream(item) for item in (probe.get("streams") or []) if isinstance(item, dict)]
    summary = {
        "case": args.case,
        "provider": provider_id,
        "fixtureType": args.media_type,
        "probeState": "runtime_error" if probe.get("runtime_error") else "completed",
        "debugStage": clean_text((probe.get("debug") or {}).get("stage"), 64),
        "raw": int(probe.get("raw_stream_count") or 0),
        "playable": int(probe.get("playable_stream_count") or 0),
        "verified": int(probe.get("content_verified_count") or probe.get("identity_verified_count") or 0),
        "unverified": int(probe.get("identity_unverified_count") or 0),
        "contradictions": int(probe.get("identity_contradiction_count") or 0),
        "transportTypesObserved": observed_transport_types(probe),
        "returned403Rows": sum(1 for s in streams if s.get("httpStatus") == 403),
        "returned4xx5xxRows": sum(1 for s in streams if int(s.get("httpStatus") or 0) >= 400),
        "qualities": sorted({str(s.get("quality")) for s in streams if s.get("quality")}),
        "languages": sorted({str(s.get("language")) for s in streams if s.get("language")}),
        "streams": streams,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("FIELD_MANUAL_TV_LIVE " + json.dumps(summary, ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
