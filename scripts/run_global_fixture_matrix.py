#!/usr/bin/env python3
from __future__ import annotations

import argparse
import concurrent.futures
import json
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manifest.json"
PROBE = ROOT / "scripts" / "run_exact_provider_fixture_probe.py"


def active_global_ids(media_type: str) -> list[str]:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    out: list[str] = []
    for row in data.get("scrapers") or []:
        if not isinstance(row, dict) or row.get("enabled") is False:
            continue
        supported = row.get("canonicalSupportedTypes") or row.get("supportedTypes") or []
        if media_type not in {str(v) for v in supported}:
            continue
        pid = str(row.get("id") or "").strip()
        if pid:
            out.append(pid)
    return out


def run_one(provider: str, fixture: dict[str, Any], work: Path, timeout: int) -> dict[str, Any]:
    output = work / (provider.replace("/", "_") + ".json")
    started = time.monotonic()
    try:
        proc = subprocess.run(
            [
                "python3",
                str(PROBE),
                "--provider",
                provider,
                "--fixture-json",
                json.dumps(fixture, separators=(",", ":")),
                "--output",
                str(output),
                "--platform",
                "macos",
            ],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {
            "provider": provider,
            "ok": False,
            "timeout": True,
            "elapsed_seconds": round(time.monotonic() - started, 3),
            "stream_count": 0,
            "provider_server_accessible": False,
            "statuses": [],
            "hosts": [],
            "observations": [],
        }

    report: dict[str, Any] = {}
    if output.is_file():
        try:
            raw = json.loads(output.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                report = raw
        except Exception:
            report = {}

    return {
        "provider": provider,
        "ok": bool(report.get("ok")) and proc.returncode == 0,
        "timeout": False,
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "stream_count": int(report.get("stream_count") or 0),
        "provider_server_accessible": bool(report.get("provider_server_accessible")),
        "provider_server_successful_response": bool(report.get("provider_server_successful_response")),
        "statuses": report.get("provider_server_http_statuses") or [],
        "hosts": report.get("provider_server_hosts") or [],
        "streams": report.get("streams") or [],
        "observations": report.get("network_observations") or [],
        "error_code": report.get("error_code"),
        "stderr_tail": (proc.stderr or "")[-500:],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture-json", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--timeout", type=int, default=90)
    args = parser.parse_args()

    fixture = json.loads(args.fixture_json)
    if not isinstance(fixture, dict):
        raise SystemExit("fixture must be an object")
    media_type = str(fixture.get("mediaType") or "")
    if media_type not in {"movie", "tv"}:
        raise SystemExit("fixture mediaType must be movie or tv")

    providers = active_global_ids(media_type)
    workers = max(1, min(int(args.workers), 8))
    rows: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="niakvio-matrix-") as tmp:
        work = Path(tmp)
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {
                pool.submit(run_one, provider, fixture, work, int(args.timeout)): provider
                for provider in providers
            }
            for future in concurrent.futures.as_completed(futures):
                rows.append(future.result())

    rows.sort(key=lambda row: (
        -int(row.get("stream_count") or 0),
        -int(bool(row.get("provider_server_successful_response"))),
        -int(bool(row.get("provider_server_accessible"))),
        str(row.get("provider") or ""),
    ))

    summary = {
        "schema_version": 1,
        "fixture": fixture,
        "active_global_candidates": len(providers),
        "tested": len(rows),
        "providers_with_streams": sum(1 for row in rows if int(row.get("stream_count") or 0) > 0),
        "providers_with_successful_server_response": sum(1 for row in rows if row.get("provider_server_successful_response")),
        "providers_with_server_access": sum(1 for row in rows if row.get("provider_server_accessible")),
        "timeouts": sum(1 for row in rows if row.get("timeout")),
        "rows": rows,
    }

    out = Path(args.output)
    if not out.is_absolute():
        out = ROOT / out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    compact = {
        "fixture": fixture,
        "active_global_candidates": summary["active_global_candidates"],
        "tested": summary["tested"],
        "providers_with_streams": summary["providers_with_streams"],
        "providers_with_successful_server_response": summary["providers_with_successful_server_response"],
        "providers_with_server_access": summary["providers_with_server_access"],
        "timeouts": summary["timeouts"],
        "rows": [
            {
                "provider": row.get("provider"),
                "stream_count": row.get("stream_count"),
                "provider_server_accessible": row.get("provider_server_accessible"),
                "provider_server_successful_response": row.get("provider_server_successful_response"),
                "statuses": row.get("statuses"),
                "hosts": row.get("hosts"),
                "error_code": row.get("error_code"),
                "timeout": row.get("timeout"),
                "observations": [
                    {
                        "stage": obs.get("stage"),
                        "host": obs.get("host"),
                        "status": obs.get("status"),
                        "ok": obs.get("ok"),
                        "error_code": obs.get("error_code"),
                    }
                    for obs in (row.get("observations") or [])[:12]
                    if isinstance(obs, dict)
                ],
            }
            for row in rows
        ],
    }
    print("GLOBAL_FIXTURE_MATRIX " + json.dumps(compact, ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
