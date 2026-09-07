#!/usr/bin/env python3
"""Live end-to-end HOTD S3E1 proof for Kehflix and Purstream.

Both currently materialized Provider JS files are executed through NiakVIO's hardened
provider worker with Nuvio's `series` transport alias and canonical `tv` transport.
No stream URL is printed. Kehflix is the required positive control; Purstream is
reported diagnostically because its current route census may legitimately produce
no playable result while we investigate the provider-specific regression.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manifest.json"
OVERRIDES = ROOT / "provider-overrides.json"
WORKER = ROOT / "scripts" / "provider_worker.cjs"
DEFAULT_OUTPUT = ROOT / "automation" / "hotd-s3e1-live.json"
PROVIDERS = ("kehflix", "purstream")

BASE_FIXTURE = {
    "slug": "house-of-the-dragon-s03e01",
    "tmdbId": "94997",
    "title": "House of the Dragon",
    "year": 2022,
    "season": 3,
    "episode": 1,
    "label": "House of the Dragon S03E01",
    "category": "tv",
}


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"{path}: expected JSON object")
    return value


def provider_row(provider_id: str) -> dict[str, Any]:
    manifest = load(MANIFEST)
    rows = [
        row for row in manifest.get("scrapers") or []
        if isinstance(row, dict) and str(row.get("id") or "").casefold() == provider_id
    ]
    if len(rows) != 1:
        raise SystemExit(f"{provider_id}: manifest cardinality={len(rows)}, expected=1")
    row = rows[0]
    filename = ROOT / str(row.get("filename") or "")
    if not filename.is_file():
        raise SystemExit(f"{provider_id}: provider file missing: {filename}")
    return row


def context_for(media_type: str) -> dict[str, Any]:
    metadata = {
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
    }
    return {
        "platform": "macos",
        "locale": "fr-FR",
        "language": "fr",
        "languages": ["fr-FR", "fr", "en-US", "en"],
        "settings": {},
        "storage": {},
        "injectAcceptLanguage": False,
        "fixtureMetadata": metadata,
        "routeProofTrace": True,
        "maxSettingsProfiles": 1,
        "singleProfileZeroStreamPreflight": False,
        "tmdbApiKey": str(os.environ.get("TMDB_API_KEY") or "").strip() or "niakvio-fixture",
        "tmdbAccessToken": str(os.environ.get("TMDB_ACCESS_TOKEN") or "").strip(),
        "networkLimits": {
            "maxFetches": 48,
            "maxResponseBytes": 5 * 1024 * 1024,
            "maxTotalResponseBytes": 24 * 1024 * 1024,
            "maxDistinctHosts": 18,
            "maxRedirects": 6,
        },
        "nuvioTransportType": media_type,
    }


def sanitize_observation(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "stage": row.get("stage"),
        "host": row.get("host"),
        "method": row.get("method"),
        "path_pattern": row.get("path_pattern"),
        "status": row.get("status"),
        "ok": row.get("ok"),
        "error_code": row.get("error_code"),
        "route_proof_trace": bool(row.get("route_proof_trace")),
    }


def run(provider: Path, media_type: str, timeout: int) -> dict[str, Any]:
    fixture = dict(BASE_FIXTURE)
    fixture["mediaType"] = media_type
    command = [
        "node",
        "--max-old-space-size=1024",
        str(WORKER),
        str(provider),
        json.dumps(fixture, ensure_ascii=False, separators=(",", ":")),
        json.dumps(context_for(media_type), ensure_ascii=False, separators=(",", ":")),
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
            "transport": media_type,
            "ok": False,
            "stream_count": 0,
            "worker_exit_code": None,
            "error_code": "timeout",
            "error_message": "provider worker timeout",
            "provider_server_accessible": False,
            "provider_server_successful_response": False,
            "provider_server_hosts": [],
            "provider_server_http_statuses": [],
            "network_observations": [],
        }

    payload: dict[str, Any] | None = None
    for line in completed.stdout.splitlines():
        if not line.startswith("NUVIO_HEALTH_RESULT="):
            continue
        try:
            candidate = json.loads(line.split("=", 1)[1])
        except json.JSONDecodeError:
            continue
        if isinstance(candidate, dict):
            payload = candidate
    if payload is None:
        return {
            "transport": media_type,
            "ok": False,
            "stream_count": 0,
            "worker_exit_code": completed.returncode,
            "error_code": "missing_worker_result",
            "error_message": (completed.stderr or "")[:1000],
            "provider_server_accessible": False,
            "provider_server_successful_response": False,
            "provider_server_hosts": [],
            "provider_server_http_statuses": [],
            "network_observations": [],
        }

    error = payload.get("error_details") if isinstance(payload.get("error_details"), dict) else {}
    observations = [
        sanitize_observation(row)
        for row in payload.get("network_observations") or []
        if isinstance(row, dict) and not row.get("infrastructure")
    ][:120]
    return {
        "transport": media_type,
        "ok": bool(payload.get("ok")),
        "stream_count": int(payload.get("stream_count") or 0),
        "worker_exit_code": completed.returncode,
        "error_code": str(error.get("code") or payload.get("error") or "")[:160] or None,
        "error_message": str(error.get("message") or "")[:500] or None,
        "provider_server_accessible": bool(payload.get("provider_server_accessible")),
        "provider_server_successful_response": bool(payload.get("provider_server_successful_response")),
        "provider_server_hosts": [str(value)[:160] for value in (payload.get("provider_server_hosts") or [])[:30]],
        "provider_server_http_statuses": [
            int(value) for value in (payload.get("provider_server_http_statuses") or [])
            if isinstance(value, int)
        ][:30],
        "network_observations": observations,
    }


def episode_request_seen(result: dict[str, Any], expected_host: str) -> bool:
    for row in result.get("network_observations") or []:
        if not isinstance(row, dict):
            continue
        host = str(row.get("host") or "").casefold()
        path = str(row.get("path_pattern") or "").casefold()
        if expected_host and host != expected_host and not host.endswith("." + expected_host):
            continue
        if "stream" not in path or "episode" not in path:
            continue
        if "season=" in path and "episode=" in path:
            return True
    return False


def failures_for(result: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    label = str(result.get("transport") or "unknown")
    if result.get("worker_exit_code") != 0:
        failures.append(f"{label}:worker_exit={result.get('worker_exit_code')}")
    if int(result.get("stream_count") or 0) <= 0:
        failures.append(f"{label}:stream_count=0")
    if not result.get("provider_server_successful_response"):
        failures.append(f"{label}:no_successful_provider_http")
    if not result.get("episode_request_seen"):
        failures.append(f"{label}:episode_request_not_observed")
    if str(result.get("error_code") or "") in {"wrong_release_year", "release_year_mismatch"}:
        failures.append(f"{label}:episodic_year_rejected")
    return failures


def expected_host_for(provider_id: str, overrides: dict[str, Any]) -> str:
    patch = (overrides.get("provider_patches") or {}).get(provider_id) or {}
    candidates = [
        patch.get("official_api"),
        patch.get("official_site"),
        (patch.get("fixed_endpoint") or {}).get("api") if isinstance(patch.get("fixed_endpoint"), dict) else None,
    ]
    for value in candidates:
        host = (urlparse(str(value or "").strip()).hostname or "").casefold()
        if host:
            return host
    raise SystemExit(f"{provider_id}: expected API/site host missing from authoritative DATA")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--timeout", type=int, default=90)
    args = parser.parse_args()

    overrides = load(OVERRIDES)
    timeout = max(20, min(180, int(args.timeout)))
    provider_reports: dict[str, Any] = {}

    for provider_id in PROVIDERS:
        row = provider_row(provider_id)
        provider = ROOT / str(row["filename"])
        expected_host = expected_host_for(provider_id, overrides)
        series = run(provider, "series", timeout)
        tv = run(provider, "tv", timeout)
        for result in (series, tv):
            result["episode_request_seen"] = episode_request_seen(result, expected_host)
        failures = failures_for(series) + failures_for(tv)
        provider_reports[provider_id] = {
            "providerVersion": row.get("version"),
            "providerFilename": row.get("filename"),
            "expectedApiHost": expected_host,
            "series": series,
            "tv": tv,
            "verdict": "ok" if not failures else "not_ok",
            "failures": failures,
        }
        print(
            "HOTD_S3E1_LIVE "
            f"provider={provider_id} verdict={provider_reports[provider_id]['verdict']} "
            f"series_streams={series.get('stream_count',0)} tv_streams={tv.get('stream_count',0)} "
            f"series_http={str(series.get('provider_server_successful_response')).lower()} "
            f"tv_http={str(tv.get('provider_server_successful_response')).lower()} "
            f"series_episode_route={str(series.get('episode_request_seen')).lower()} "
            f"tv_episode_route={str(tv.get('episode_request_seen')).lower()}"
        )

    kehflix_ok = provider_reports["kehflix"]["verdict"] == "ok"
    purstream_ok = provider_reports["purstream"]["verdict"] == "ok"
    expected_pattern = kehflix_ok and not purstream_ok
    report = {
        "schemaVersion": 2,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "fixture": {
            "tmdbId": "94997",
            "title": "House of the Dragon",
            "tmdbSeriesOriginYear": 2022,
            "season": 3,
            "episode": 1,
        },
        "providers": provider_reports,
        "acceptance": {
            "requiredPositiveProvider": "kehflix",
            "purstreamDiagnosticOnly": True,
            "kehflixOk": kehflix_ok,
            "purstreamOk": purstream_ok,
            "expectedPatternKehflixOkPurstreamNotOk": expected_pattern,
        },
    }
    output = args.output if args.output.is_absolute() else ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(
        "HOTD_S3E1_EXPECTED_PATTERN "
        f"kehflix={'OK' if kehflix_ok else 'NOT_OK'} "
        f"purstream={'OK' if purstream_ok else 'NOT_OK'} "
        f"matched={str(expected_pattern).lower()}"
    )
    if not kehflix_ok:
        raise SystemExit(
            "HOTD S3E1 required Kehflix proof failed: "
            + ", ".join(provider_reports["kehflix"]["failures"])
        )
    print("HOTD_S3E1_LIVE_ACCEPTED required_provider=kehflix transports=series,tv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
