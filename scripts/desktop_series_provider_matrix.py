#!/usr/bin/env python3
"""Run a Nuvio Desktop-like series/anime fixture across compatible public providers."""
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


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--id", required=True, help="Client-facing IMDb/TMDB/Kitsu identifier")
    p.add_argument("--title", required=True)
    p.add_argument("--season", type=int, required=True)
    p.add_argument("--episode", type=int, required=True)
    p.add_argument("--category", default="anime")
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--workers", type=int, default=10)
    p.add_argument("--timeout", type=int, default=35)
    return p.parse_args()


def main() -> int:
    args = parse_args()
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    fixture = {
        "tmdbId": args.id,
        "mediaType": "series",
        "season": args.season,
        "episode": args.episode,
        "title": args.title,
        "label": f"{args.title} S{args.season:02d}E{args.episode:02d}",
        "category": args.category,
    }
    context = {
        "locale": "fr-FR",
        "language": "fr",
        "languages": ["fr-FR", "fr", "en"],
        "platform": "desktop",
        "settings": {},
        "storage": {},
        "injectAcceptLanguage": True,
        "networkLimits": {
            "maxFetches": 30,
            "maxResponseBytes": 5_242_880,
            "maxTotalResponseBytes": 20_971_520,
            "maxDistinctHosts": 20,
            "maxRedirects": 5,
        },
        "maxSettingsProfiles": 1,
    }

    candidates: list[dict[str, Any]] = []
    for row in manifest.get("scrapers") or []:
        if not isinstance(row, dict) or row.get("enabled") is not True:
            continue
        semantic = {
            str(x).casefold()
            for x in (row.get("canonicalSupportedTypes") or row.get("supportedTypes") or [])
        }
        transport = {str(x).casefold() for x in (row.get("supportedTypes") or [])}
        if "anime" in semantic or {"tv", "series"} & transport:
            candidates.append(row)

    timeout = max(10, min(180, args.timeout))

    def probe(row: dict[str, Any]) -> dict[str, Any]:
        command = [
            "node",
            "--max-old-space-size=1024",
            str(WORKER),
            str(ROOT / str(row["filename"])),
            json.dumps(fixture, ensure_ascii=False),
            json.dumps(context, ensure_ascii=False),
        ]
        try:
            cp = subprocess.run(
                command,
                cwd=ROOT,
                text=True,
                capture_output=True,
                timeout=timeout,
                check=False,
                env=os.environ.copy(),
            )
        except subprocess.TimeoutExpired:
            return {"id": str(row["id"]).casefold(), "count": 0, "ok": False, "error": "timeout"}

        payload: dict[str, Any] | None = None
        for line in cp.stdout.splitlines():
            if line.startswith("NUVIO_HEALTH_RESULT="):
                try:
                    payload = json.loads(line.split("=", 1)[1])
                except json.JSONDecodeError:
                    pass
        if not payload:
            return {
                "id": str(row["id"]).casefold(),
                "count": 0,
                "ok": False,
                "error": "missing_worker_payload",
                "stderr": cp.stderr[-500:],
            }
        return {
            "id": str(row["id"]).casefold(),
            "count": int(payload.get("stream_count") or 0),
            "ok": bool(payload.get("ok")),
            "error": payload.get("error") or (payload.get("error_details") or {}).get("message"),
            "hosts": payload.get("provider_server_hosts") or [],
            "statuses": payload.get("provider_server_http_statuses") or [],
            "successful_response": bool(payload.get("provider_server_successful_response")),
            "invocation_diagnostics": payload.get("invocation_diagnostics") or [],
        }

    results: list[dict[str, Any]] = []
    workers = max(1, min(12, args.workers))
    with ThreadPoolExecutor(max_workers=min(workers, max(1, len(candidates)))) as executor:
        futures = {executor.submit(probe, row): row for row in candidates}
        for index, future in enumerate(as_completed(futures), 1):
            row = futures[future]
            try:
                result = future.result()
            except Exception as exc:
                result = {
                    "id": str(row.get("id") or "").casefold(),
                    "count": 0,
                    "ok": False,
                    "error": f"probe_exception:{type(exc).__name__}:{exc}",
                }
            results.append(result)
            print(
                f"[{index}/{len(candidates)}] {result['id']} streams={result['count']} error={result.get('error')}",
                flush=True,
            )

    results.sort(key=lambda row: row["id"])
    positive = [row["id"] for row in results if row["count"] > 0]
    network_reached = [row["id"] for row in results if row.get("hosts")]
    successful_http = [row["id"] for row in results if row.get("successful_response")]
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "manifest_version": manifest.get("version"),
        "fixture": fixture,
        "providers_tested": len(results),
        "positive_count": len(positive),
        "positive_ids": positive,
        "network_reached_count": len(network_reached),
        "network_reached_ids": network_reached,
        "successful_http_count": len(successful_http),
        "successful_http_ids": successful_http,
        "providers": results,
    }
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "tested": len(results),
        "positive_count": len(positive),
        "positive_ids": positive,
        "network_reached_count": len(network_reached),
        "successful_http_count": len(successful_http),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
