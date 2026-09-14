#!/usr/bin/env python3
"""Short field-priority provider probe for the current NuvioTV regression corpus.

This is deliberately NOT a Native Lab. It executes only the currently published
provider bytes through provider_worker.cjs, in parallel and with a short hard
per-attempt timeout. It answers why a provider is absent before any player/UI
work: positive rows, clean zero, settings/profile gap, timeout, runtime failure,
or provider HTTP/anti-bot failure. No stream URL is printed or persisted.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manifest.json"
WORKER = ROOT / "scripts" / "provider_worker.cjs"
DEFAULT_OUTPUT = ROOT / "automation" / "field-priority-probe-20260914.json"

FIXTURES: tuple[dict[str, Any], ...] = (
    {
        "slug": "interstellar-2014",
        "tmdbId": "157336",
        "mediaType": "movie",
        "title": "Interstellar",
        "year": 2014,
        "label": "Interstellar (2014)",
        "category": "movie",
        "metadata": {
            "id": 157336,
            "mediaType": "movie",
            "type": "movie",
            "category": "movie",
            "title": "Interstellar",
            "original_title": "Interstellar",
            "release_date": "2014-11-05",
            "year": 2014,
            "origin_country": ["US"],
            "original_language": "en",
            "genres": [{"id": 12, "name": "Adventure"}, {"id": 878, "name": "Science Fiction"}],
            "keywords": {"keywords": []},
            "anime": False,
        },
    },
    {
        "slug": "house-of-the-dragon-s01e02",
        "tmdbId": "94997",
        "mediaType": "tv",
        "title": "House of the Dragon",
        "year": 2022,
        "season": 1,
        "episode": 2,
        "label": "House of the Dragon S01E02",
        "category": "tv",
        "metadata": {
            "id": 94997,
            "mediaType": "tv",
            "type": "tv",
            "category": "tv",
            "name": "House of the Dragon",
            "original_name": "House of the Dragon",
            "first_air_date": "2022-08-21",
            "year": 2022,
            "origin_country": ["US"],
            "original_language": "en",
            "genres": [{"id": 18, "name": "Drama"}],
            "keywords": {"results": []},
            "anime": False,
        },
    },
    {
        "slug": "hell-mode-s02e10",
        "tmdbId": "280049",
        "mediaType": "anime",
        "title": "Hell Mode: The Hardcore Gamer Dominates in Another World with Garbage Balancing",
        "year": 2026,
        "season": 2,
        "episode": 10,
        "label": "Hell Mode S02E10",
        "category": "anime",
        "metadata": {
            "id": 280049,
            "mediaType": "tv",
            "type": "tv",
            "category": "anime",
            "name": "Hell Mode: The Hardcore Gamer Dominates in Another World with Garbage Balancing",
            "first_air_date": "2026-01-01",
            "year": 2026,
            "origin_country": ["JP"],
            "original_language": "ja",
            "genres": [{"id": 16, "name": "Animation"}],
            "keywords": {"results": []},
            "anime": True,
        },
    },
)


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"{path}: expected JSON object")
    return value


def canonical(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def context_for(fixture: dict[str, Any], max_profiles: int) -> dict[str, Any]:
    return {
        "platform": "android",
        "locale": "fr-FR",
        "language": "fr",
        "languages": ["fr-FR", "fr", "en-US", "en"],
        "settings": {},
        "storage": {},
        "injectAcceptLanguage": True,
        "fixtureMetadata": fixture["metadata"],
        "routeProofTrace": True,
        "maxSettingsProfiles": max_profiles,
        "singleProfileZeroStreamPreflight": False,
        "tmdbApiKey": str(os.environ.get("TMDB_API_KEY") or "").strip() or "niakvio-fixture",
        "tmdbAccessToken": str(os.environ.get("TMDB_ACCESS_TOKEN") or "").strip(),
        "networkLimits": {
            "maxFetches": 32,
            "maxResponseBytes": 5 * 1024 * 1024,
            "maxTotalResponseBytes": 18 * 1024 * 1024,
            "maxDistinctHosts": 16,
            "maxRedirects": 5,
        },
        "nuvioTransportType": fixture["mediaType"],
    }


def worker_payload(stdout: str) -> dict[str, Any] | None:
    payload = None
    for line in stdout.splitlines():
        if not line.startswith("NUVIO_HEALTH_RESULT="):
            continue
        try:
            candidate = json.loads(line.split("=", 1)[1])
        except json.JSONDecodeError:
            continue
        if isinstance(candidate, dict):
            payload = candidate
    return payload


def run_once(filename: str, fixture: dict[str, Any], timeout: int, max_profiles: int) -> dict[str, Any]:
    request = {key: value for key, value in fixture.items() if key != "metadata"}
    command = [
        "node",
        "--max-old-space-size=768",
        str(WORKER),
        str(ROOT / filename),
        json.dumps(request, ensure_ascii=False, separators=(",", ":")),
        json.dumps(context_for(fixture, max_profiles), ensure_ascii=False, separators=(",", ":")),
    ]
    try:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            env=os.environ.copy(),
        )
    except subprocess.TimeoutExpired:
        return {
            "ok": False,
            "stream_count": 0,
            "exit_code": None,
            "error_class": "timeout",
            "error_message": "provider worker hard timeout",
            "provider_http_ok": False,
            "provider_hosts": [],
            "http_statuses": [],
            "invocation_diagnostics": [],
        }

    payload = worker_payload(completed.stdout)
    if payload is None:
        return {
            "ok": False,
            "stream_count": 0,
            "exit_code": completed.returncode,
            "error_class": "missing_worker_result",
            "error_message": (completed.stderr or "")[-800:],
            "provider_http_ok": False,
            "provider_hosts": [],
            "http_statuses": [],
            "invocation_diagnostics": [],
        }
    details = payload.get("error_details") if isinstance(payload.get("error_details"), dict) else {}
    return {
        "ok": bool(payload.get("ok")),
        "stream_count": int(payload.get("stream_count") or 0),
        "exit_code": completed.returncode,
        "error_class": str(details.get("code") or payload.get("error") or "")[:160] or None,
        "error_message": str(details.get("message") or "")[:400] or None,
        "provider_http_ok": bool(payload.get("provider_server_successful_response")),
        "provider_hosts": [str(value)[:120] for value in (payload.get("provider_server_hosts") or [])[:12]],
        "http_statuses": [int(value) for value in (payload.get("provider_server_http_statuses") or []) if isinstance(value, int)][:16],
        "invocation_diagnostics": (payload.get("invocation_diagnostics") or [])[:8],
    }


def classify(strict: dict[str, Any], diagnostic: dict[str, Any] | None) -> str:
    if strict.get("stream_count", 0) > 0:
        return "automatic_streams"
    if diagnostic and diagnostic.get("stream_count", 0) > 0:
        return "settings_profile_gap"
    values = [strict, diagnostic or {}]
    if any(row.get("error_class") == "timeout" for row in values):
        return "timeout"
    statuses = {status for row in values for status in row.get("http_statuses", [])}
    if statuses & {401, 403, 429}:
        return "http_or_antibot_block"
    if any(row.get("exit_code") not in {0, None} or row.get("error_class") for row in values):
        return "runtime_error"
    if any(row.get("provider_http_ok") for row in values):
        return "clean_zero_after_provider_http"
    return "no_provider_http_or_zero"


def supports(row: dict[str, Any], fixture: dict[str, Any]) -> bool:
    types = {canonical(value) for value in row.get("supportedTypes") or []}
    media_type = canonical(fixture["mediaType"])
    if media_type == "anime":
        return "anime" in types
    return media_type in types


def probe(row: dict[str, Any], fixture: dict[str, Any], timeout: int) -> dict[str, Any]:
    filename = str(row.get("filename") or "")
    strict = run_once(filename, fixture, timeout, 1)
    diagnostic = None
    if strict.get("stream_count", 0) <= 0 and bool(row.get("hasSettings")):
        diagnostic = run_once(filename, fixture, timeout, 4)
    return {
        "provider": canonical(row.get("id")),
        "version": row.get("version"),
        "filename": filename,
        "fixture": fixture["slug"],
        "contentLanguage": row.get("contentLanguage") or [],
        "strict": strict,
        "diagnostic": diagnostic,
        "classification": classify(strict, diagnostic),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--workers", type=int, default=10)
    parser.add_argument("--timeout", type=int, default=12)
    args = parser.parse_args()

    manifest = load_json(MANIFEST)
    rows = [row for row in manifest.get("scrapers") or [] if isinstance(row, dict) and row.get("enabled") is True]
    workers = max(1, min(12, int(args.workers)))
    timeout = max(8, min(20, int(args.timeout)))
    jobs: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for fixture in FIXTURES:
        for row in rows:
            if supports(row, fixture):
                jobs.append((row, fixture))

    results: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(probe, row, fixture, timeout): (row, fixture) for row, fixture in jobs}
        done = 0
        for future in as_completed(futures):
            done += 1
            row, fixture = futures[future]
            provider = canonical(row.get("id"))
            try:
                result = future.result()
            except Exception as exc:
                result = {
                    "provider": provider,
                    "version": row.get("version"),
                    "filename": row.get("filename"),
                    "fixture": fixture["slug"],
                    "contentLanguage": row.get("contentLanguage") or [],
                    "strict": {"ok": False, "stream_count": 0, "error_class": f"probe_exception:{type(exc).__name__}"},
                    "diagnostic": None,
                    "classification": "runtime_error",
                }
            results.append(result)
            print(
                "FIELD_PRIORITY_PROBE "
                f"progress={done}/{len(jobs)} fixture={result['fixture']} provider={provider} "
                f"class={result['classification']} streams={result.get('strict',{}).get('stream_count',0)}",
                flush=True,
            )

    results.sort(key=lambda row: (row["fixture"], row["provider"]))
    by_fixture: dict[str, dict[str, list[str]]] = {}
    for fixture in FIXTURES:
        slug = fixture["slug"]
        current = [row for row in results if row["fixture"] == slug]
        classes: dict[str, list[str]] = {}
        for row in current:
            classes.setdefault(str(row["classification"]), []).append(str(row["provider"]))
        for values in classes.values():
            values.sort()
        by_fixture[slug] = classes
        print(f"FIELD_PRIORITY_SUMMARY fixture={slug} classes={json.dumps(classes, ensure_ascii=False, sort_keys=True)}")

    report = {
        "schemaVersion": 1,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "manifestVersion": manifest.get("version"),
        "timeoutSeconds": timeout,
        "workers": workers,
        "fixtures": [{key: value for key, value in fixture.items() if key != "metadata"} for fixture in FIXTURES],
        "summary": by_fixture,
        "results": results,
    }
    output = args.output if args.output.is_absolute() else ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"FIELD_PRIORITY_PROBE_DONE jobs={len(results)} output={output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
