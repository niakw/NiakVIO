#!/usr/bin/env python3
"""Bootstrap Provider v3 route DATA from an otherwise empty provider definition.

The source Provider JS is an observation instrument only.  No static route string is
promoted.  The worker executes it with representative fixtures, provider_route_proof
abstracts only values proven by fixture identity or prior provider responses, and
only successful HTTP calls become executable route DATA.

This is the canonical path for onboarding a new provider with no pre-existing
NiakVIO routes, and the fallback path for difficult SPA/React/Next-like providers.
"""
from __future__ import annotations

import argparse
import copy
import json
import os
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from provider_route_proof import derive_task_routes, route_role, unique  # noqa: E402

WORKER = ROOT / "scripts" / "provider_worker.cjs"
PROOF_VERSION = 5

DEFAULT_FIXTURES = {
    "movie": [
        {"slug": "interstellar", "tmdbId": "157336", "mediaType": "movie", "title": "Interstellar", "year": 2014},
    ],
    "tv": [
        {"slug": "breaking-bad-s01e01", "tmdbId": "1396", "mediaType": "tv", "title": "Breaking Bad", "year": 2008, "season": 1, "episode": 1},
        {"slug": "house-of-the-dragon-s03e01", "tmdbId": "94997", "mediaType": "tv", "title": "House of the Dragon", "year": 2022, "season": 3, "episode": 1},
    ],
    "anime": [
        {"slug": "jujutsu-kaisen-s01e01", "tmdbId": "95479", "mediaType": "anime", "category": "anime", "title": "Jujutsu Kaisen", "year": 2020, "season": 1, "episode": 1},
    ],
}


def context_for(fixture: dict[str, Any]) -> dict[str, Any]:
    anime = fixture.get("mediaType") == "anime" or fixture.get("category") == "anime"
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
        "original_language": "ja" if anime else "en",
        "origin_country": ["JP"] if anime else ["US"],
        "genres": [{"id": 16, "name": "Animation"}] if anime else [],
        "anime": bool(anime),
    }
    return {
        "platform": "android",
        "locale": "fr-FR",
        "languages": ["fr-FR", "fr", "en-US", "en"],
        "fixtureMetadata": metadata,
        "routeProofTrace": True,
        "maxSettingsProfiles": 8,
        "singleProfileZeroStreamPreflight": False,
        "networkLimits": {
            "maxFetches": 48,
            "maxDistinctHosts": 18,
            "maxResponseBytes": 4 * 1024 * 1024,
            "maxTotalResponseBytes": 24 * 1024 * 1024,
            "maxRedirects": 6,
        },
    }


def read_source(value: str, destination: Path) -> Path:
    text = str(value or "").strip()
    if not text:
        raise ValueError("--source is required")
    local = Path(text)
    if local.is_file():
        destination.write_bytes(local.read_bytes())
        return destination
    if text.startswith("https://"):
        req = urllib.request.Request(text, headers={"User-Agent": "NiakVIO-New-Provider-Bootstrap/5"})
        with urllib.request.urlopen(req, timeout=30) as response:
            data = response.read(16 * 1024 * 1024 + 1)
        if len(data) > 16 * 1024 * 1024:
            raise ValueError("provider source exceeds 16 MiB")
        destination.write_bytes(data)
        return destination
    raise FileNotFoundError(text)


def run_worker(source: Path, fixture: dict[str, Any], timeout: int) -> dict[str, Any]:
    cmd = [
        "node", str(WORKER), str(source),
        json.dumps(fixture, ensure_ascii=False, separators=(",", ":")),
        json.dumps(context_for(fixture), ensure_ascii=False, separators=(",", ":")),
    ]
    try:
        proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=timeout, check=False, env=os.environ.copy())
    except subprocess.TimeoutExpired:
        return {"ok": False, "timeout": True, "network_observations": [], "stream_count": 0, "error": "timeout"}
    result = None
    for line in proc.stdout.splitlines():
        if line.startswith("NUVIO_HEALTH_RESULT="):
            try:
                result = json.loads(line.split("=", 1)[1])
            except json.JSONDecodeError:
                pass
    if not isinstance(result, dict):
        return {"ok": False, "timeout": False, "network_observations": [], "stream_count": 0, "error": "worker_no_result"}
    return result


def observation_fetch(row: dict[str, Any]) -> dict[str, Any] | None:
    if row.get("infrastructure") or row.get("route_proof_trace") is not True:
        return None
    url = str(row.get("proof_url") or "").strip()
    if not url:
        return None
    return {
        "url": url,
        "final_url": url,
        "method": str(row.get("method") or "GET").upper(),
        "status": int(row.get("status") or 0),
        "error": row.get("error") or row.get("error_code"),
        "content_type": row.get("content_type"),
        "proof_headers": copy.deepcopy(row.get("proof_headers") or {}),
        "header_names": sorted((row.get("proof_headers") or {}).keys()),
        "body_kind": row.get("proof_body_kind"),
        "body_fields": list(row.get("proof_body_fields") or []),
        "body_values": copy.deepcopy(row.get("proof_body_values") or {}),
        "response_value_hints": copy.deepcopy(row.get("response_value_hints") or []),
        "duration_ms": int(row.get("duration_ms") or 0),
    }


def successful(fetch: dict[str, Any]) -> bool:
    return not fetch.get("error") and 200 <= int(fetch.get("status") or 0) < 400


def collect(provider_id: str, source: Path, types: list[str], timeout: int) -> dict[str, Any]:
    route_data: list[dict[str, Any]] = []
    tasks: list[dict[str, Any]] = []
    for semantic_type in types:
        for fixture in DEFAULT_FIXTURES[semantic_type]:
            result = run_worker(source, copy.deepcopy(fixture), timeout)
            fetches = [value for raw in result.get("network_observations") or [] if isinstance(raw, dict) and (value := observation_fetch(raw))]
            task = {
                "provider_id": provider_id,
                "semantic_type": semantic_type,
                "fixture_slug": fixture["slug"],
                "fixture": copy.deepcopy(fixture),
                "fetches": fetches,
            }
            proven = 0
            for item in derive_task_routes(task):
                route = str(item.get("route") or "").strip()
                fetch = item.get("fetch") if isinstance(item.get("fetch"), dict) else {}
                meta = item.get("derivation") if isinstance(item.get("derivation"), dict) else {}
                if not route or not successful(fetch):
                    continue
                route_data.append({
                    "route": route,
                    "origin": meta.get("origin"),
                    "role": route_role(route),
                    "method": str(fetch.get("method") or "GET").upper(),
                    "semanticType": semantic_type,
                    "fixture": fixture["slug"],
                    "providerValueCorrelation": bool(meta.get("providerValueCorrelation")),
                    "headers": copy.deepcopy(fetch.get("proof_headers") or {}),
                    "bodyKind": fetch.get("body_kind") or "none",
                    "bodyFields": list(fetch.get("body_fields") or []),
                    "bodyValues": copy.deepcopy(fetch.get("body_values") or {}),
                    "status": int(fetch.get("status") or 0),
                    "contentType": fetch.get("content_type"),
                    "proofModelVersion": PROOF_VERSION,
                    "validationState": "live-validated",
                    "executedEvidence": True,
                    "httpUsed": True,
                })
                proven += 1
            tasks.append({
                "fixture": fixture["slug"],
                "semanticType": semantic_type,
                "workerOk": bool(result.get("ok")),
                "streamCount": int(result.get("stream_count") or 0),
                "providerRequestCount": len(fetches),
                "provenRouteCount": proven,
                "error": (result.get("error_details") or {}).get("code") or result.get("error"),
            })

    deduped = []
    seen = set()
    for row in route_data:
        fp = (row["origin"], row["route"], row["method"], row["semanticType"], row["fixture"])
        if fp in seen:
            continue
        seen.add(fp)
        deduped.append(row)
    routes = unique([row["route"] for row in deduped], 256)
    return {
        "providerId": provider_id,
        "schemaVersion": PROOF_VERSION,
        "routeProofVersion": PROOF_VERSION,
        "sourceProviderJavaScriptExecuted": True,
        "staticCandidatesExecutable": False,
        "routes": routes,
        "routeData": deduped,
        "tasks": tasks,
        "bootstrapStatus": "routes-proven" if routes else "no-proven-route",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Bootstrap route DATA for a new/empty Provider v3")
    parser.add_argument("--provider-id", required=True)
    parser.add_argument("--source", required=True, help="local Provider JS path or HTTPS raw URL")
    parser.add_argument("--type", action="append", dest="types", default=[])
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    provider_id = str(args.provider_id).strip().casefold().replace("_", "-")
    types = []
    for raw in args.types or ["movie"]:
        value = str(raw).strip().casefold()
        if value == "series":
            value = "tv"
        if value not in DEFAULT_FIXTURES:
            raise SystemExit(f"unsupported semantic type: {raw}")
        if value not in types:
            types.append(value)
    with tempfile.TemporaryDirectory(prefix=f"niakvio-bootstrap-{provider_id}-") as tmp:
        source = read_source(args.source, Path(tmp) / f"{provider_id}.js")
        payload = collect(provider_id, source, types, max(15, min(120, int(args.timeout))))
    out = args.output or (ROOT / "staging" / "route-bootstrap" / f"{provider_id}.json")
    if not out.is_absolute():
        out = ROOT / out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        "PROVIDER_V3_EMPTY_BOOTSTRAP "
        f"provider={provider_id} types={','.join(types)} routes={len(payload['routes'])} "
        f"status={payload['bootstrapStatus']} proof_version={PROOF_VERSION}"
    )
    return 0 if payload["routes"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
