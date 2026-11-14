#!/usr/bin/env python3
"""Terminal playback matrix for user-reported NiakVIO regressions.

Runs the exact published provider bytes through the hardened provider worker and
the existing terminal media probe. Persisted output never contains stream URLs or
header values.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import json
from pathlib import Path
from typing import Any

import run_provider_upstream_parity_v3 as parity3

ROOT = Path(__file__).resolve().parents[1]

FIXTURES: dict[str, dict[str, Any]] = {
    "spartacus_s00e01": {
        "tmdbId": "46296",
        "mediaType": "tv",
        "category": "tv",
        "title": "Spartacus",
        "year": 2010,
        "season": 0,
        "episode": 1,
    },
    "visionquest_s01e01": {
        "tmdbId": "213375",
        "mediaType": "tv",
        "category": "tv",
        "title": "VisionQuest",
        "year": 2026,
        "season": 1,
        "episode": 1,
    },
    "fahrenheit_451_2018": {
        "tmdbId": "401905",
        "mediaType": "movie",
        "category": "movie",
        "title": "Fahrenheit 451",
        "year": 2018,
    },
}


def cid(value: object) -> str:
    return str(value or "").strip().casefold()


def canonical_types(row: dict[str, Any]) -> set[str]:
    raw = row.get("canonicalSupportedTypes") or row.get("supportedTypes") or []
    if isinstance(raw, str):
        raw = [raw]
    return {cid(v) for v in raw if cid(v) in {"movie", "tv", "anime"}}


def provider_rows() -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for manifest_path in (ROOT / "manifest.json", ROOT / "vf" / "manifest.json"):
        if not manifest_path.is_file():
            continue
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        for row in data.get("scrapers") or []:
            if not isinstance(row, dict):
                continue
            provider_id = cid(row.get("id"))
            filename = str(row.get("filename") or "").strip()
            if not provider_id or not filename or not (ROOT / filename).is_file():
                continue
            # Keep an enabled projection over a disabled duplicate when both
            # manifests reference the same canonical provider.
            existing = out.get(provider_id)
            if existing is None or (row.get("enabled") is not False and existing.get("enabled") is False):
                out[provider_id] = row
    return out


def safe(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "stream_count": int(result.get("stream_count") or 0),
        "candidate_stream_count": int(result.get("candidate_stream_count") or 0),
        "raw_stream_count": int(result.get("raw_stream_count") or 0),
        "terminal_verified": bool(result.get("terminal_verified")),
        "terminal_reasons": list(result.get("terminal_reasons") or [])[:8],
        "terminal_media_duration_seconds": list(result.get("terminal_media_duration_seconds") or [])[:8],
        "http_statuses": list(result.get("http_statuses") or [])[:12],
        "timeout": bool(result.get("timeout")),
        "error_class": result.get("error_class"),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--providers", default="")
    parser.add_argument("--fixtures", default=",".join(FIXTURES))
    parser.add_argument("--output", default="automation/user-fixture-terminal-matrix.json")
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--timeout", type=int, default=35)
    args = parser.parse_args()

    rows = provider_rows()
    requested = {cid(v) for v in args.providers.split(",") if cid(v)}
    providers = sorted(pid for pid, row in rows.items() if row.get("enabled") is not False and (not requested or pid in requested))
    fixture_ids = [v.strip() for v in args.fixtures.split(",") if v.strip()]
    unknown = [v for v in fixture_ids if v not in FIXTURES]
    if unknown:
        raise SystemExit("unknown fixtures: " + ",".join(unknown))
    if not providers:
        raise SystemExit("no active providers selected")

    tasks: list[tuple[str, str, Path, dict[str, Any]]] = []
    for provider_id in providers:
        row = rows[provider_id]
        lanes = canonical_types(row)
        path = ROOT / str(row["filename"])
        for fixture_id in fixture_ids:
            fixture = dict(FIXTURES[fixture_id])
            lane = fixture["mediaType"]
            if lane == "movie" and "movie" not in lanes:
                continue
            if lane == "tv" and not ({"tv", "anime"} & lanes):
                continue
            tasks.append((provider_id, fixture_id, path, fixture))

    def run_one(task: tuple[str, str, Path, dict[str, Any]]) -> dict[str, Any]:
        provider_id, fixture_id, path, fixture = task
        try:
            result = parity3._run_verified(path, fixture, max(5, min(int(args.timeout), 90)))
            compact = safe(result)
        except Exception as exc:
            compact = {
                "stream_count": 0,
                "candidate_stream_count": 0,
                "raw_stream_count": 0,
                "terminal_verified": False,
                "terminal_reasons": [],
                "terminal_media_duration_seconds": [],
                "http_statuses": [],
                "timeout": False,
                "error_class": type(exc).__name__,
            }
        return {"provider": provider_id, "fixture": fixture_id, **compact}

    results: list[dict[str, Any]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, min(args.workers, 8))) as pool:
        for row in pool.map(run_one, tasks):
            results.append(row)
            print(
                "USER_FIXTURE_PLAYBACK "
                f"provider={row['provider']} fixture={row['fixture']} "
                f"streams={row['stream_count']} terminal={str(row['terminal_verified']).lower()} "
                f"statuses={','.join(str(v) for v in row['http_statuses']) or '-'}"
            )

    positives = [r for r in results if r["stream_count"] > 0 and r["terminal_verified"]]
    summary = {}
    for fixture_id in fixture_ids:
        subset = [r for r in results if r["fixture"] == fixture_id]
        good = [r for r in subset if r["stream_count"] > 0 and r["terminal_verified"]]
        summary[fixture_id] = {
            "tested": len(subset),
            "terminal_positive_providers": len(good),
            "terminal_positive_streams": sum(r["stream_count"] for r in good),
            "providers": [r["provider"] for r in good],
        }

    payload = {
        "schema_version": 1,
        "providers_requested": sorted(requested),
        "providers_tested": providers,
        "fixtures": fixture_ids,
        "summary": summary,
        "results": sorted(results, key=lambda r: (r["fixture"], r["provider"])),
    }
    out = Path(args.output)
    if not out.is_absolute():
        out = ROOT / out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("USER_FIXTURE_MATRIX_OK " + json.dumps(summary, sort_keys=True))
    return 0 if positives else 2


if __name__ == "__main__":
    raise SystemExit(main())
