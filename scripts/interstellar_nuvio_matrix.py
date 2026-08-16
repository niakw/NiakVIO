#!/usr/bin/env python3
"""Measure every active movie provider with Nuvio-like Interstellar invocation."""
from __future__ import annotations

import argparse
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manifest.json"
WORKER = ROOT / "scripts" / "provider_worker.cjs"
DEFAULT_OUTPUT = ROOT / "automation" / "interstellar-nuvio-matrix.json"

FIXTURE = {
    "tmdbId": "157336",
    "mediaType": "movie",
    "title": "Interstellar",
    "year": 2014,
    "label": "Interstellar (2014)",
    "category": "movie",
}

BASE_CONTEXT = {
    "locale": "fr-FR",
    "language": "fr",
    "languages": ["fr-FR", "fr", "en"],
    "platform": "android",
    "settings": {},
    "storage": {},
    "injectAcceptLanguage": True,
    "networkLimits": {
        "maxFetches": 30,
        "maxResponseBytes": 5242880,
        "maxTotalResponseBytes": 20971520,
        "maxDistinctHosts": 20,
        "maxRedirects": 5,
    },
}


def run_provider(filename: str, max_profiles: int, timeout: int) -> dict[str, Any]:
    context = {**BASE_CONTEXT, "maxSettingsProfiles": max_profiles}
    command = [
        "node",
        "--max-old-space-size=1024",
        str(WORKER),
        str(ROOT / filename),
        json.dumps(FIXTURE, ensure_ascii=False),
        json.dumps(context, ensure_ascii=False),
    ]
    try:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {
            "ok": False,
            "stream_count": 0,
            "error": "timeout",
            "selected_settings_profile": None,
            "provider_hosts": [],
            "http_statuses": [],
        }

    payload: dict[str, Any] = {}
    for line in completed.stdout.splitlines():
        if line.startswith("NUVIO_HEALTH_RESULT="):
            try:
                payload = json.loads(line.split("=", 1)[1])
            except json.JSONDecodeError:
                pass
    if not payload:
        return {
            "ok": False,
            "stream_count": 0,
            "error": "missing_worker_payload",
            "selected_settings_profile": None,
            "provider_hosts": [],
            "http_statuses": [],
        }

    environment = payload.get("environment_context") or {}
    return {
        "ok": bool(payload.get("ok")),
        "stream_count": int(payload.get("stream_count") or 0),
        "error": payload.get("error") or (payload.get("error_details") or {}).get("message"),
        "selected_settings_profile": environment.get("selected_settings_profile"),
        "selected_setting_keys": environment.get("selected_setting_keys") or [],
        "provider_hosts": payload.get("provider_server_hosts") or [],
        "http_statuses": payload.get("provider_server_http_statuses") or [],
        "provider_server_successful_response": bool(payload.get("provider_server_successful_response")),
        "invocation_diagnostics": payload.get("invocation_diagnostics") or [],
    }


def probe_row(row: dict[str, Any], timeout: int) -> dict[str, Any]:
    provider_id = str(row.get("id") or "").casefold()
    filename = str(row.get("filename") or "")
    strict = run_provider(filename, 1, timeout)
    diagnostic = strict if strict.get("stream_count", 0) > 0 else run_provider(filename, 8, timeout)
    classification = (
        "automatic_streams"
        if strict.get("stream_count", 0) > 0
        else "settings_or_profile_gap"
        if diagnostic.get("stream_count", 0) > 0
        else "no_streams"
    )
    return {
        "id": provider_id,
        "version": row.get("version"),
        "filename": filename,
        "contentLanguage": row.get("contentLanguage") or [],
        "hasSettings": bool(row.get("hasSettings")),
        "nuvio_empty_settings": strict,
        "diagnostic_profiles": diagnostic,
        "classification": classification,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--timeout", type=int, default=90)
    parser.add_argument("--minimum-automatic", type=int, default=0)
    args = parser.parse_args()

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    rows = [
        row
        for row in manifest.get("scrapers") or []
        if isinstance(row, dict)
        and row.get("enabled") is True
        and "movie" in {str(value).casefold() for value in row.get("supportedTypes") or []}
    ]
    rows.sort(key=lambda row: str(row.get("id") or "").casefold())
    workers = max(1, min(12, int(args.workers)))
    timeout = max(10, min(180, int(args.timeout)))

    results: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(probe_row, row, timeout): row for row in rows}
        completed = 0
        for future in as_completed(futures):
            completed += 1
            row = futures[future]
            provider_id = str(row.get("id") or "").casefold()
            try:
                result = future.result()
            except Exception as exc:
                result = {
                    "id": provider_id,
                    "version": row.get("version"),
                    "filename": row.get("filename"),
                    "contentLanguage": row.get("contentLanguage") or [],
                    "hasSettings": bool(row.get("hasSettings")),
                    "nuvio_empty_settings": {"ok": False, "stream_count": 0, "error": f"probe_exception:{type(exc).__name__}:{exc}"},
                    "diagnostic_profiles": {"ok": False, "stream_count": 0, "error": f"probe_exception:{type(exc).__name__}:{exc}"},
                    "classification": "no_streams",
                }
            results.append(result)
            print(f"[{completed}/{len(rows)}] {provider_id}: {result['classification']}", flush=True)
    results.sort(key=lambda row: row["id"])

    automatic = [r["id"] for r in results if r["classification"] == "automatic_streams"]
    settings_gap = [r["id"] for r in results if r["classification"] == "settings_or_profile_gap"]
    no_stream = [r["id"] for r in results if r["classification"] == "no_streams"]
    automatic_vf = [
        r["id"]
        for r in results
        if r["classification"] == "automatic_streams"
        and "fr" in {str(value).casefold() for value in r.get("contentLanguage") or []}
    ]

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "manifest_version": manifest.get("version"),
        "fixture": FIXTURE,
        "enabled_movie_providers_tested": len(results),
        "automatic_stream_provider_count": len(automatic),
        "automatic_stream_provider_ids": automatic,
        "automatic_vf_provider_count": len(automatic_vf),
        "automatic_vf_provider_ids": automatic_vf,
        "settings_or_profile_gap_ids": settings_gap,
        "no_stream_ids": no_stream,
        "providers": results,
    }
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps({
        "tested": len(results),
        "automatic_count": len(automatic),
        "automatic": automatic,
        "automatic_vf_count": len(automatic_vf),
        "automatic_vf": automatic_vf,
        "settings_gap": settings_gap,
        "no_stream_count": len(no_stream),
    }, ensure_ascii=False, indent=2))

    minimum = max(0, int(args.minimum_automatic))
    if len(automatic) < minimum:
        raise SystemExit(
            f"Interstellar coverage regression: automatic={len(automatic)} minimum={minimum}; "
            f"tested={len(results)}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
