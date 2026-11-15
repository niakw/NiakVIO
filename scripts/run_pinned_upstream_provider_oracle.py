#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
WORKER = ROOT / "scripts" / "provider_worker.cjs"
SHA_RE = re.compile(r"^[0-9a-f]{40}$", re.I)
REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
PATH_RE = re.compile(r"^[A-Za-z0-9_./-]+$")

def parse_worker(stdout: str) -> dict[str, Any]:
    payload = None
    for line in stdout.splitlines():
        if line.startswith("NUVIO_HEALTH_RESULT="):
            value = json.loads(line.split("=", 1)[1])
            if isinstance(value, dict):
                payload = value
    if payload is None:
        raise RuntimeError("provider worker result marker missing")
    return payload

def safe_observations(payload: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    for row in payload.get("network_observations") or []:
        if not isinstance(row, dict) or row.get("infrastructure"):
            continue
        out.append({
            "stage": row.get("stage"), "host": row.get("host"), "method": row.get("method"),
            "path_pattern": row.get("path_pattern"), "status": row.get("status"),
            "ok": row.get("ok"), "error_code": row.get("error_code"),
        })
    return out[:160]

def safe_streams(payload: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    for row in payload.get("streams") or []:
        if not isinstance(row, dict):
            continue
        raw = str(row.get("url") or "")
        host = None
        if raw.startswith(("http://", "https://")):
            try:
                host = urllib.parse.urlparse(raw).hostname
            except ValueError:
                pass
        out.append({
            "host": host, "quality": row.get("quality"), "language": row.get("language"),
            "size": row.get("size"),
            "subtitle_count": len(row.get("subtitles") or []) if isinstance(row.get("subtitles"), list) else 0,
            "has_headers": bool(row.get("headers")) if isinstance(row.get("headers"), dict) else False,
        })
    return out[:30]

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repository", required=True)
    ap.add_argument("--ref", required=True)
    ap.add_argument("--path", required=True)
    ap.add_argument("--fixture-json", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--timeout", type=int, default=90)
    args = ap.parse_args()

    if not REPO_RE.fullmatch(args.repository):
        raise SystemExit("repository must be owner/name")
    if not SHA_RE.fullmatch(args.ref):
        raise SystemExit("ref must be immutable 40-hex commit SHA")
    rel = args.path.strip().lstrip("/")
    if ".." in Path(rel).parts or not PATH_RE.fullmatch(rel) or not rel.endswith(".js"):
        raise SystemExit("path must be safe repository-relative JavaScript")

    fixture = json.loads(args.fixture_json)
    if not isinstance(fixture, dict) or not fixture.get("tmdbId") or not fixture.get("mediaType"):
        raise SystemExit("fixture requires tmdbId and mediaType")

    owner, repo = args.repository.split("/", 1)
    raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{args.ref}/{rel}"
    request = urllib.request.Request(
        raw_url,
        headers={"User-Agent": "NiakVIO-pinned-upstream-oracle/1.0", "Accept": "text/plain"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        source = response.read(4 * 1024 * 1024 + 1)
    if len(source) > 4 * 1024 * 1024:
        raise SystemExit("upstream provider exceeds 4 MiB")
    if b"getStreams" not in source:
        raise SystemExit("upstream source does not expose recognizable provider entrypoint")

    context = {
        "fixtureMetadata": fixture,
        "locale": "fr-FR",
        "languages": ["fr-FR", "fr", "en-US", "en"],
        "platform": "macos",
        "userAgent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/151 Safari/537.36",
        "injectAcceptLanguage": True,
        "maxSettingsProfiles": 1,
        "networkLimits": {
            "maxFetches": 40, "maxResponseBytes": 5 * 1024 * 1024,
            "maxTotalResponseBytes": 24 * 1024 * 1024, "maxDistinctHosts": 18, "maxRedirects": 5,
        },
    }
    with tempfile.TemporaryDirectory(prefix="niakvio-upstream-oracle-") as tmp:
        provider_path = Path(tmp) / "provider.js"
        provider_path.write_bytes(source)
        proc = subprocess.run(
            ["node", str(WORKER), str(provider_path), json.dumps(fixture, separators=(",", ":")),
             json.dumps(context, separators=(",", ":"))],
            cwd=ROOT, text=True, capture_output=True,
            timeout=max(20, min(args.timeout, 120)), check=False,
        )

    payload = parse_worker(proc.stdout)
    error = payload.get("error_details") if isinstance(payload.get("error_details"), dict) else {}
    report = {
        "schema_version": 1, "oracle": "pinned-upstream-provider",
        "repository": args.repository, "ref": args.ref, "path": rel, "fixture": fixture,
        "worker_exit_code": proc.returncode, "ok": bool(payload.get("ok")),
        "stream_count": int(payload.get("stream_count") or 0),
        "raw_stream_count": int(payload.get("raw_stream_count") or 0),
        "provider_server_accessible": bool(payload.get("provider_server_accessible")),
        "provider_server_successful_response": bool(payload.get("provider_server_successful_response")),
        "provider_server_hosts": payload.get("provider_server_hosts") or [],
        "provider_server_http_statuses": payload.get("provider_server_http_statuses") or [],
        "error_code": str(error.get("code") or "") or None,
        "streams": safe_streams(payload), "network_observations": safe_observations(payload),
    }
    out = Path(args.output)
    if not out.is_absolute():
        out = ROOT / out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        "PINNED_UPSTREAM_PROVIDER_ORACLE "
        f"repo={args.repository} ref={args.ref[:12]} path={rel} "
        f"streams={report['stream_count']} accessible={str(report['provider_server_accessible']).lower()} "
        f"statuses={','.join(str(x) for x in report['provider_server_http_statuses']) or '-'}"
    )
    return 0 if report["ok"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
