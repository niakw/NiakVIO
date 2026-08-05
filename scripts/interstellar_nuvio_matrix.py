#!/usr/bin/env python3
"""Compare Nuvio-like empty-settings invocation with diagnostic profile discovery."""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manifest.json"
WORKER = ROOT / "scripts" / "provider_worker.cjs"
OUTPUT = ROOT / "automation" / "interstellar-nuvio-matrix.json"

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


def run_provider(filename: str, max_profiles: int) -> dict[str, Any]:
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
            timeout=120,
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


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    rows = [
        row
        for row in manifest.get("scrapers") or []
        if isinstance(row, dict)
        and row.get("enabled") is True
        and "movie" in {str(value).casefold() for value in row.get("supportedTypes") or []}
    ]
    results: list[dict[str, Any]] = []
    for index, row in enumerate(rows, 1):
        provider_id = str(row.get("id") or "").casefold()
        filename = str(row.get("filename") or "")
        print(f"[{index}/{len(rows)}] {provider_id}", flush=True)
        strict = run_provider(filename, 1)
        diagnostic = strict if strict.get("stream_count", 0) > 0 else run_provider(filename, 8)
        results.append({
            "id": provider_id,
            "version": row.get("version"),
            "filename": filename,
            "contentLanguage": row.get("contentLanguage") or [],
            "hasSettings": bool(row.get("hasSettings")),
            "nuvio_empty_settings": strict,
            "diagnostic_profiles": diagnostic,
            "classification": (
                "automatic_streams"
                if strict.get("stream_count", 0) > 0
                else "settings_or_profile_gap"
                if diagnostic.get("stream_count", 0) > 0
                else "no_streams"
            ),
        })

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "manifest_version": manifest.get("version"),
        "fixture": FIXTURE,
        "enabled_movie_providers_tested": len(results),
        "automatic_stream_provider_ids": [r["id"] for r in results if r["classification"] == "automatic_streams"],
        "settings_or_profile_gap_ids": [r["id"] for r in results if r["classification"] == "settings_or_profile_gap"],
        "no_stream_ids": [r["id"] for r in results if r["classification"] == "no_streams"],
        "providers": results,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "automatic": report["automatic_stream_provider_ids"],
        "settings_gap": report["settings_or_profile_gap_ids"],
        "no_stream_count": len(report["no_stream_ids"]),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
