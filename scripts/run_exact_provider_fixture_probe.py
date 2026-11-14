#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
WORKER = ROOT / "scripts" / "provider_worker.cjs"
CATALOG = ROOT / "provider_catalog.json"
MANIFESTS = (ROOT / "manifest.json", ROOT / "vf" / "manifest.json")


def load_catalog_provider(provider_id: str) -> tuple[dict[str, Any], Path]:
    """Resolve the exact bytes clients currently load.

    Targeted materialization updates manifest projections before publication.
    The canonical catalog can intentionally lag that worktree projection, so
    manifest bytes are authoritative for a physical replay. Falling back to the
    catalog is only for providers absent from both production projections.
    """
    target = provider_id.strip().casefold()
    for manifest_path in MANIFESTS:
        if not manifest_path.is_file():
            continue
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        for scraper in data.get("scrapers") or []:
            if not isinstance(scraper, dict):
                continue
            cid = str(scraper.get("id") or "").strip().casefold()
            if cid != target:
                continue
            filename = str(scraper.get("filename") or "").strip()
            if not filename:
                continue
            path = (manifest_path.parent / filename).resolve()
            if ROOT != path and ROOT not in path.parents:
                raise SystemExit(f"{provider_id}: manifest provider path escapes repository")
            if not path.is_file():
                raise SystemExit(f"{provider_id}: manifest bytes missing at {filename}")
            return {"canonicalId": cid, "scraper": scraper, "sourceManifest": str(manifest_path.relative_to(ROOT))}, path

    data = json.loads(CATALOG.read_text(encoding="utf-8"))
    for record in data.get("providers") or []:
        if not isinstance(record, dict):
            continue
        scraper = record.get("scraper")
        if not isinstance(scraper, dict):
            continue
        cid = str(record.get("canonicalId") or scraper.get("id") or "").strip().casefold()
        if cid != target:
            continue
        filename = str(scraper.get("filename") or "").strip()
        if not filename:
            raise SystemExit(f"{provider_id}: catalog filename missing")
        path = (ROOT / filename).resolve()
        if ROOT != path and ROOT not in path.parents:
            raise SystemExit(f"{provider_id}: provider path escapes repository")
        if not path.is_file():
            raise SystemExit(f"{provider_id}: provider bytes missing at {path.relative_to(ROOT)}")
        return record, path
    raise SystemExit(f"{provider_id}: provider row missing from manifests and catalog")


def parse_worker(stdout: str) -> dict[str, Any]:
    payload = None
    for line in stdout.splitlines():
        if not line.startswith("NUVIO_HEALTH_RESULT="):
            continue
        candidate = json.loads(line.split("=", 1)[1])
        if isinstance(candidate, dict):
            payload = candidate
    if payload is None:
        raise SystemExit("provider worker result marker missing")
    return payload


def safe_stream_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    for row in payload.get("streams") or []:
        if not isinstance(row, dict):
            continue
        raw = str(row.get("url") or "")
        host = None
        if raw.startswith(("http://", "https://")):
            try:
                from urllib.parse import urlparse
                host = urlparse(raw).hostname
            except Exception:
                host = None
        out.append({
            "host": host,
            "quality": row.get("quality"),
            "language": row.get("language"),
            "size": row.get("size"),
            "subtitle_count": len(row.get("subtitles") or []) if isinstance(row.get("subtitles"), list) else 0,
            "audio_track_count": len(row.get("audioTracks") or []) if isinstance(row.get("audioTracks"), list) else 0,
            "has_headers": isinstance(row.get("headers"), dict) and bool(row.get("headers")),
        })
    return out[:20]


def safe_observations(payload: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    for row in payload.get("network_observations") or []:
        if not isinstance(row, dict) or row.get("infrastructure"):
            continue
        out.append({
            "stage": row.get("stage"),
            "host": row.get("host"),
            "method": row.get("method"),
            "path_pattern": row.get("path_pattern"),
            "status": row.get("status"),
            "ok": row.get("ok"),
            "error_code": row.get("error_code"),
        })
    return out[:80]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", required=True)
    parser.add_argument("--fixture-json", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--platform", default="macos")
    args = parser.parse_args()

    fixture = json.loads(args.fixture_json)
    if not isinstance(fixture, dict):
        raise SystemExit("fixture must be a JSON object")
    required = {"tmdbId", "mediaType"}
    if not required <= set(fixture):
        raise SystemExit("fixture requires tmdbId and mediaType")

    record, provider_path = load_catalog_provider(args.provider)
    context = {
        "fixtureMetadata": fixture,
        "locale": "fr-FR",
        "languages": ["fr-FR", "fr", "en-US", "en"],
        "platform": args.platform,
        "userAgent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/151 Safari/537.36",
        "injectAcceptLanguage": True,
        "tmdbApiKey": "niakvio-fixture",
        "maxSettingsProfiles": 1,
        "networkLimits": {
            "maxFetches": 30,
            "maxResponseBytes": 5 * 1024 * 1024,
            "maxTotalResponseBytes": 20 * 1024 * 1024,
            "maxDistinctHosts": 16,
            "maxRedirects": 5,
        },
    }
    proc = subprocess.run(
        [
            "node",
            str(WORKER),
            str(provider_path),
            json.dumps(fixture, separators=(",", ":")),
            json.dumps(context, separators=(",", ":")),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=75,
        check=False,
    )
    payload = parse_worker(proc.stdout)
    error = payload.get("error_details") if isinstance(payload.get("error_details"), dict) else {}
    report = {
        "schema_version": 1,
        "provider": str(args.provider).casefold(),
        "provider_path": str(provider_path.relative_to(ROOT)),
        "catalog_enabled": bool((record.get("scraper") or {}).get("enabled")),
        "fixture": {
            "tmdbId": str(fixture.get("tmdbId") or ""),
            "mediaType": str(fixture.get("mediaType") or ""),
            "title": str(fixture.get("title") or ""),
            "season": fixture.get("season"),
            "episode": fixture.get("episode"),
        },
        "worker_exit_code": proc.returncode,
        "ok": bool(payload.get("ok")),
        "stream_count": int(payload.get("stream_count") or 0),
        "raw_stream_count": int(payload.get("raw_stream_count") or 0),
        "provider_server_accessible": bool(payload.get("provider_server_accessible")),
        "provider_server_successful_response": bool(payload.get("provider_server_successful_response")),
        "provider_server_hosts": payload.get("provider_server_hosts") or [],
        "provider_server_http_statuses": payload.get("provider_server_http_statuses") or [],
        "error_code": str(error.get("code") or "") or None,
        "streams": safe_stream_rows(payload),
        "invocation_diagnostics": [
            {
                "profile": str(profile.get("name") or ""),
                "stream_count": int(profile.get("stream_count") or 0),
                "attempts": [
                    {
                        "name": str(attempt.get("name") or ""),
                        "inferred_mode": str(attempt.get("inferred_mode") or ""),
                        "result": str(attempt.get("result") or ""),
                        "stream_count": int(attempt.get("stream_count") or 0),
                        "provider_observations": int(attempt.get("provider_observations") or 0),
                        "error_code": str(((attempt.get("error") or {}).get("code")) or "") or None,
                    }
                    for attempt in (profile.get("invocation_diagnostics") or [])
                    if isinstance(attempt, dict)
                ],
            }
            for profile in (payload.get("settings_diagnostics") or [])
            if isinstance(profile, dict)
        ],
        "network_observations": safe_observations(payload),
    }
    out = Path(args.output)
    if not out.is_absolute():
        out = ROOT / out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        "EXACT_PROVIDER_FIXTURE_PROBE "
        f"provider={report['provider']} ok={str(report['ok']).lower()} "
        f"streams={report['stream_count']} accessible={str(report['provider_server_accessible']).lower()} "
        f"statuses={','.join(str(v) for v in report['provider_server_http_statuses']) or '-'}"
    )
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
