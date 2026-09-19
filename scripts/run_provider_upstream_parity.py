#!/usr/bin/env python3
"""Run upstream-vs-NiakVIO provider parity through the hardened provider worker.

The report is intentionally stream-URL-free. Upstream code is downloaded to a
throw-away directory and executed only by scripts/provider_worker.cjs, which
applies NiakVIO's module restrictions, guarded fetch and response budgets.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import subprocess
import tempfile
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
WORKER = ROOT / "scripts/provider_worker.cjs"
DEFAULT_OUT = ROOT / "automation/provider-upstream-parity.json"

FIXTURES = {
    "movie": {
        "tmdbId": "157336",
        "mediaType": "movie",
        "title": "Interstellar",
        "year": 2014,
    },
    "tv": {
        "tmdbId": "1396",
        "mediaType": "tv",
        "title": "Breaking Bad",
        "year": 2008,
        "season": 1,
        "episode": 1,
    },
    "anime": {
        "tmdbId": "95479",
        "mediaType": "anime",
        "category": "anime",
        "title": "Jujutsu Kaisen",
        "year": 2020,
        "season": 1,
        "episode": 1,
    },
}


def cid(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def get_json(url: str, timeout: int = 30) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"User-Agent": "NiakVIO-Parity/1"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = response.read(8 * 1024 * 1024)
    value = json.loads(payload.decode("utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {url}")
    return value


def get_bytes(url: str, timeout: int = 30) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "NiakVIO-Parity/1"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read(12 * 1024 * 1024)


def upstream_catalog() -> tuple[dict[str, dict[str, Any]], list[dict[str, str]]]:
    sources = json.loads((ROOT / "sources.json").read_text(encoding="utf-8"))
    catalog: dict[str, dict[str, Any]] = {}
    errors: list[dict[str, str]] = []
    for source_id, cfg in (sources.get("upstreams") or {}).items():
        urls = cfg.get("manifest_urls") if isinstance(cfg, dict) else []
        manifest = None
        selected_url = None
        last_error = None
        for manifest_url in urls if isinstance(urls, list) else []:
            try:
                manifest = get_json(str(manifest_url))
                selected_url = str(manifest_url)
                break
            except Exception as exc:  # network evidence, not a fatal global error
                last_error = str(exc)[:240]
        if not manifest or not selected_url:
            errors.append({"source": str(source_id), "error": last_error or "manifest unavailable"})
            continue
        for row in manifest.get("scrapers") or []:
            if not isinstance(row, dict):
                continue
            provider_id = cid(row.get("id"))
            filename = str(row.get("filename") or "").strip()
            if not provider_id or not filename or provider_id in catalog:
                continue
            catalog[provider_id] = {
                "source": str(source_id),
                "entry": row,
                "url": urllib.parse.urljoin(selected_url, filename),
            }
    return catalog, errors


def local_catalog() -> dict[str, dict[str, Any]]:
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    out = {}
    for row in manifest.get("scrapers") or []:
        if not isinstance(row, dict):
            continue
        provider_id = cid(row.get("id"))
        filename = str(row.get("filename") or "").strip()
        if provider_id and filename:
            out[provider_id] = {"entry": row, "path": ROOT / filename}
    return out


def semantic_types(row: dict[str, Any]) -> list[str]:
    values = row.get("canonicalSupportedTypes") or row.get("supportedTypes") or []
    out = []
    for raw in values if isinstance(values, list) else []:
        value = str(raw or "").strip().casefold()
        if value == "series":
            value = "tv"
        if value in FIXTURES and value not in out:
            out.append(value)
    return out


def selected_fixtures(local_row: dict[str, Any], upstream_row: dict[str, Any]) -> list[str]:
    local_types = semantic_types(local_row)
    upstream_types = semantic_types(upstream_row)
    selected = []
    # Test every local semantic capability, but avoid inventing a movie path.
    for value in ("movie", "tv", "anime"):
        if value in local_types and value not in selected:
            selected.append(value)
    if not selected:
        for value in ("movie", "tv"):
            if value in upstream_types and value not in selected:
                selected.append(value)
    return selected or ["movie"]


def worker_fixture(kind: str, *, upstream: bool) -> dict[str, Any]:
    fixture = dict(FIXTURES[kind])
    # Upstreams generally publish anime under Nuvio's historical `tv` transport.
    # NiakVIO keeps semantic anime explicit and aliases only at the provider edge.
    if upstream and kind == "anime":
        fixture["mediaType"] = "tv"
        fixture["type"] = "tv"
        fixture.pop("category", None)
    return fixture


def context_for(fixture: dict[str, Any]) -> dict[str, Any]:
    metadata = {
        "id": int(fixture["tmdbId"]),
        "title": fixture.get("title"),
        "name": fixture.get("title"),
        "original_title": fixture.get("title"),
        "original_name": fixture.get("title"),
        "release_date": f"{fixture.get('year')}-01-01" if fixture.get("year") else "",
        "first_air_date": f"{fixture.get('year')}-01-01" if fixture.get("year") else "",
        "year": fixture.get("year"),
        "aliases": [fixture.get("title")],
    }
    if fixture.get("category") == "anime" or fixture.get("mediaType") == "anime":
        metadata.update({"original_language": "ja", "origin_country": ["JP"], "genres": [{"id": 16, "name": "Animation"}], "anime": True})
    return {
        "platform": "android",
        "locale": "fr-FR",
        "languages": ["fr-FR", "fr", "en-US", "en"],
        "fixtureMetadata": metadata,
        "maxSettingsProfiles": 3,
        "singleProfileZeroStreamPreflight": True,
        "networkLimits": {
            "maxFetches": 30,
            "maxDistinctHosts": 12,
            "maxResponseBytes": 4 * 1024 * 1024,
            "maxTotalResponseBytes": 16 * 1024 * 1024,
            "maxRedirects": 5,
        },
    }


def run_worker(path: Path, fixture: dict[str, Any], timeout: int) -> dict[str, Any]:
    cmd = [
        "node",
        str(WORKER),
        str(path),
        json.dumps(fixture, separators=(",", ":")),
        json.dumps(context_for(fixture), separators=(",", ":")),
    ]
    try:
        completed = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=timeout, check=False)
    except subprocess.TimeoutExpired:
        return {"ok": False, "stream_count": 0, "timeout": True, "error_class": "timeout"}
    result = None
    for line in completed.stdout.splitlines():
        if line.startswith("NUVIO_HEALTH_RESULT="):
            try:
                result = json.loads(line.split("=", 1)[1])
            except json.JSONDecodeError:
                pass
    if not isinstance(result, dict):
        return {"ok": False, "stream_count": 0, "timeout": False, "error_class": "worker_no_result"}
    return {
        "ok": bool(result.get("ok")),
        "stream_count": int(result.get("stream_count") or 0),
        "raw_stream_count": int(result.get("raw_stream_count") or 0),
        "timeout": False,
        "server_accessible": bool(result.get("provider_server_accessible")),
        "server_success": bool(result.get("provider_server_successful_response")),
        "http_statuses": [int(v) for v in result.get("provider_server_http_statuses") or [] if isinstance(v, int)][:12],
        "error_class": str((result.get("error_details") or {}).get("code") or (result.get("error_details") or {}).get("name") or "")[:120] or None,
    }


def classify(upstream: dict[str, Any], local: dict[str, Any]) -> str:
    up = int(upstream.get("stream_count") or 0) > 0
    lo = int(local.get("stream_count") or 0) > 0
    if up and lo:
        return "both_ok"
    if up and not lo:
        return "upstream_ok_niakvio_ko"
    if not up and lo:
        return "niakvio_ok_upstream_ko"
    if upstream.get("timeout") or local.get("timeout"):
        return "inconclusive_timeout"
    return "both_zero"


def one_provider(provider_id: str, local: dict[str, Any], upstream: dict[str, Any], upstream_path: Path, timeout: int) -> dict[str, Any]:
    fixtures = []
    classes = []
    for kind in selected_fixtures(local["entry"], upstream["entry"]):
        up_fixture = worker_fixture(kind, upstream=True)
        local_fixture = worker_fixture(kind, upstream=False)
        up_result = run_worker(upstream_path, up_fixture, timeout)
        local_result = run_worker(local["path"], local_fixture, timeout)
        state = classify(up_result, local_result)
        classes.append(state)
        fixtures.append({"fixture": kind, "upstream": up_result, "niakvio": local_result, "classification": state})
    if "upstream_ok_niakvio_ko" in classes:
        state = "upstream_ok_niakvio_ko"
    elif "both_ok" in classes:
        state = "both_ok"
    elif "niakvio_ok_upstream_ko" in classes:
        state = "niakvio_ok_upstream_ko"
    elif "inconclusive_timeout" in classes:
        state = "inconclusive_timeout"
    else:
        state = "both_zero"
    return {
        "providerId": provider_id,
        "upstreamSource": upstream["source"],
        "classification": state,
        "fixtures": fixtures,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    parser.add_argument("--workers", type=int, default=int(os.environ.get("NIAKVIO_PARITY_WORKERS", "8")))
    parser.add_argument("--timeout", type=int, default=int(os.environ.get("NIAKVIO_PARITY_TIMEOUT", "30")))
    parser.add_argument("--provider", action="append", default=[])
    args = parser.parse_args()

    local = local_catalog()
    upstreams, source_errors = upstream_catalog()
    requested = {cid(v) for v in args.provider if cid(v)}
    provider_ids = [pid for pid in local if pid in upstreams and (not requested or pid in requested)]
    missing_upstream = sorted(pid for pid in local if pid not in upstreams and (not requested or pid in requested))
    rows: list[dict[str, Any]] = []
    download_errors: list[dict[str, str]] = []

    with tempfile.TemporaryDirectory(prefix="niakvio-upstream-parity-") as tmp_name:
        tmp = Path(tmp_name)
        tasks = []
        for provider_id in provider_ids:
            upstream = upstreams[provider_id]
            try:
                data = get_bytes(upstream["url"])
                path = tmp / f"{provider_id}.js"
                path.write_bytes(data)
            except Exception as exc:
                download_errors.append({"providerId": provider_id, "source": upstream["source"], "error": str(exc)[:240]})
                continue
            tasks.append((provider_id, local[provider_id], upstream, path))

        with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, min(16, args.workers))) as pool:
            future_map = {
                pool.submit(one_provider, provider_id, local_row, upstream, path, max(5, args.timeout)): provider_id
                for provider_id, local_row, upstream, path in tasks
            }
            for future in concurrent.futures.as_completed(future_map):
                provider_id = future_map[future]
                try:
                    rows.append(future.result())
                except Exception as exc:
                    rows.append({"providerId": provider_id, "classification": "harness_error", "error": type(exc).__name__})

    rows.sort(key=lambda row: str(row.get("providerId")))
    counts = Counter(str(row.get("classification") or "unknown") for row in rows)
    payload = {
        "schemaVersion": 1,
        "providerCount": len(local),
        "matchedUpstreamProviders": len(provider_ids),
        "testedProviders": len(rows),
        "classificationCounts": dict(sorted(counts.items())),
        "missingUpstreamProviders": missing_upstream,
        "upstreamManifestErrors": source_errors,
        "providerDownloadErrors": download_errors,
        "fixtures": {key: {k: v for k, v in value.items() if k not in {"category"}} for key, value in FIXTURES.items()},
        "providers": rows,
    }
    out = Path(args.out)
    if not out.is_absolute():
        out = ROOT / out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("PROVIDER_UPSTREAM_PARITY " + " ".join(f"{key}={value}" for key, value in sorted(counts.items())))
    print(f"PROVIDER_UPSTREAM_PARITY_COVERAGE local={len(local)} matched={len(provider_ids)} tested={len(rows)} missing={len(missing_upstream)} downloads_failed={len(download_errors)}")
    regressions = [row["providerId"] for row in rows if row.get("classification") == "upstream_ok_niakvio_ko"]
    print("PROVIDER_UPSTREAM_PARITY_REGRESSIONS " + (",".join(regressions) if regressions else "none"))
    return 0 if rows else 2


if __name__ == "__main__":
    raise SystemExit(main())
