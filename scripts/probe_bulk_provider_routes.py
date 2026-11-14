#!/usr/bin/env python3
"""Probe bulk-onboarding candidates for sanitized executable route DATA.

The probe is read-only. It never promotes a provider and never treats GitHub
network failure as provider failure. A caller may route traffic through the
repository's authorized residential exit; the report records that transport.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, quote, urlencode, urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REQUEST = ROOT / ".github/provider-onboarding/batch.json"
DEFAULT_OUTPUT = ROOT / "automation/provider-bulk-route-discovery-shard.json"
PROBE = ROOT / "scripts/probe_provider_site_structure.py"

sys.path.insert(0, str((ROOT / "scripts").resolve()))
from provider_base_store import provider_model_route_kind

SENSITIVE_KEYS = {"k","key","token","sig","signature","auth","authorization","expires","expiry","exp"}
SEARCH_KEYS = {"s","q","query","keyword","search","story"}
TMDB_KEYS = {"tmdb","tmdbid","tmdb_id","tmdb-id"}
IMDB_KEYS = {"imdb","imdbid","imdb_id","imdb-id"}
MEDIA_KEYS = {"media","media_type","mediatype","type"}
SEASON_KEYS = {"season"}
EPISODE_KEYS = {"episode","ep"}

FIXTURES = {
    "movie": {"title": "Interstellar", "tmdbId": "157336", "mediaType": "movie"},
    "tv": {"title": "Breaking Bad", "tmdbId": "1396", "mediaType": "tv", "season": 1, "episode": 1},
    "anime": {"title": "Jujutsu Kaisen", "tmdbId": "95479", "mediaType": "anime", "season": 1, "episode": 1},
}


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def norm(value: Any) -> str:
    return re.sub(r"[^a-z0-9._-]+", "-", str(value or "").strip().casefold()).strip("-")


def fixture_for(row: dict[str, Any]) -> dict[str, Any]:
    types = [str(x).strip().casefold() for x in row.get("types") or row.get("supportedTypes") or []]
    for lane in ("movie", "tv", "anime"):
        if lane in types:
            return dict(FIXTURES[lane])
    return dict(FIXTURES["movie"])


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(value or "").casefold()).strip("-")


def _template_query(query: str, fixture: dict[str, Any]) -> str | None:
    if not query:
        return ""
    out: list[tuple[str, str]] = []
    for key, value in parse_qsl(query, keep_blank_values=True):
        k = key.strip()
        lk = k.casefold()
        if lk in SENSITIVE_KEYS:
            return None
        raw = str(value or "")
        if lk in SEARCH_KEYS:
            value = "{query}"
        elif lk in TMDB_KEYS:
            value = "{tmdbId}"
        elif lk in IMDB_KEYS:
            value = "{imdbId}"
        elif lk in MEDIA_KEYS and raw.casefold() not in {"search","find","lookup","play","stream"}:
            value = "{media}"
        elif lk in SEASON_KEYS:
            value = "{season}"
        elif lk in EPISODE_KEYS:
            value = "{episode}"
        elif raw == str(fixture.get("tmdbId") or ""):
            value = "{tmdbId}"
        elif raw and len(raw) > 80:
            return None
        out.append((k, value))
    # urlencode would escape our placeholders; build a conservative query by hand.
    return "&".join(
        quote(k, safe="._-") + "=" + quote(v, safe="{}._-")
        for k, v in out
    )


def route_pattern(raw: Any, fixture: dict[str, Any]) -> str:
    value = str(raw or "").strip()
    if not value:
        return ""
    try:
        parsed = urlsplit(value)
    except ValueError:
        return ""
    absolute = bool(parsed.scheme and parsed.netloc)
    path = parsed.path or ("/" if absolute else "")
    query = parsed.query
    tmdb_id = str(fixture.get("tmdbId") or "")
    title_slug = slug(str(fixture.get("title") or ""))
    if tmdb_id:
        path = re.sub(rf"(?<!\d){re.escape(tmdb_id)}(?!\d)", "{{tmdbId}}", path)
    if title_slug and title_slug in path.casefold():
        path = re.sub(re.escape(title_slug), "{slug}", path, flags=re.I)
    templated_query = _template_query(query, fixture)
    if templated_query is None:
        return ""
    if absolute:
        value = urlunsplit((parsed.scheme, parsed.netloc, path, templated_query, ""))
    else:
        value = path + (("?" + templated_query) if templated_query else "")
    # Empty search query literals are common in site JS. Turn them into Core title input.
    value = re.sub(r"([?&](?:s|q|query|keyword|search|story)=)(?=&|$)", r"\1{query}", value, flags=re.I)
    return value[:420] if provider_model_route_kind(value) != "ignore" else ""


def observed_candidates(report: dict[str, Any]) -> list[Any]:
    values: list[Any] = []
    for row in report.get("route_hints") or []:
        if isinstance(row, dict):
            values.append(row.get("value"))
    for row in report.get("next_chunks") or []:
        if isinstance(row, dict):
            values.extend(row.get("route_hints") or [])
    for row in report.get("runtime_routes") or []:
        if not isinstance(row, dict):
            continue
        values.extend(row.get("route_hints") or [])
        values.extend(row.get("runtime_chunk_route_hints") or [])
        values.extend(row.get("runtime_api_patterns") or [])
        for chunk in row.get("runtime_chunks") or []:
            if isinstance(chunk, dict):
                values.extend(chunk.get("route_hints") or [])
                values.extend(chunk.get("runtime_api_patterns") or [])
    return values


def provider_rows(request: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for section in ("providers", "deferredProviders"):
        for row in request.get(section) or []:
            if not isinstance(row, dict):
                continue
            pid = norm(row.get("id") or row.get("provider"))
            if not pid or pid in seen:
                continue
            seen.add(pid)
            rows.append(row)
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--request", type=Path, default=DEFAULT_REQUEST)
    ap.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    ap.add_argument("--shard-count", type=int, default=1)
    ap.add_argument("--shard-index", type=int, default=0)
    ap.add_argument("--timeout", type=int, default=8)
    ap.add_argument("--max-chunks", type=int, default=10)
    ap.add_argument("--max-runtime-chunks", type=int, default=10)
    ap.add_argument("--provider-timeout", type=int, default=150)
    args = ap.parse_args()

    request = load(args.request)
    if not isinstance(request, dict):
        raise SystemExit("bulk route discovery request must be an object")
    rows = provider_rows(request)
    selected = [row for index, row in enumerate(rows) if index % args.shard_count == args.shard_index]
    transport = "residential-exit" if os.environ.get("NIAKVIO_BULK_ROUTE_DISCOVERY_RESIDENTIAL") == "1" else "github-hosted"
    results: list[dict[str, Any]] = []

    for row in selected:
        pid = norm(row.get("id") or row.get("provider"))
        direct = str(row.get("direct") or row.get("direct_url") or "").strip()
        fixture = fixture_for(row)
        existing = [route_pattern(v, fixture) for v in row.get("routes") or []]
        existing = list(dict.fromkeys(v for v in existing if v))
        if existing:
            results.append({
                "provider": pid,
                "scope": str(row.get("scope") or "global"),
                "transport": "request-existing",
                "probeAttempted": False,
                "probeReachedSite": True,
                "routePatterns": existing,
                "routeCount": len(existing),
                "qualified": True,
                "reason": "existing_executable_route_plan",
            })
            continue
        if not re.match(r"^https?://[^/\s]+", direct):
            results.append({
                "provider": pid, "scope": str(row.get("scope") or "global"),
                "transport": transport, "probeAttempted": False, "probeReachedSite": False,
                "routePatterns": [], "routeCount": 0, "qualified": False,
                "reason": "direct_origin_missing",
            })
            continue

        with tempfile.TemporaryDirectory(prefix=f"niakvio-route-{pid}-") as td:
            td_path = Path(td)
            current = td_path / "current.json"
            report_path = td_path / "site-structure.json"
            current.write_text(json.dumps({
                "id": pid,
                "direct": direct,
                "site": direct,
                "fixture": fixture,
            }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            cmd = [
                sys.executable, str(PROBE),
                "--current", str(current),
                "--output", str(report_path),
                "--timeout", str(args.timeout),
                "--max-chunks", str(args.max_chunks),
                "--max-runtime-chunks", str(args.max_runtime_chunks),
            ]
            try:
                proc = subprocess.run(
                    cmd, cwd=ROOT, text=True, capture_output=True,
                    timeout=max(30, args.provider_timeout), check=False,
                )
                report = load(report_path) if report_path.is_file() else {}
            except subprocess.TimeoutExpired:
                proc = None
                report = {}

        pages = [x for x in report.get("pages") or [] if isinstance(x, dict)]
        reached = any(x.get("ok") is True and int(x.get("status") or 0) < 500 for x in pages)
        patterns: list[str] = []
        for raw in observed_candidates(report):
            pattern = route_pattern(raw, fixture)
            if pattern and pattern not in patterns:
                patterns.append(pattern)
            if len(patterns) >= 24:
                break
        reason = "observed_executable_routes" if patterns else ("reachable_no_executable_route_observed" if reached else "network_or_site_unreached")
        results.append({
            "provider": pid,
            "scope": str(row.get("scope") or "global"),
            "direct": direct,
            "transport": transport,
            "probeAttempted": True,
            "probeReachedSite": reached,
            "probeReturnCode": None if proc is None else proc.returncode,
            "routePatterns": patterns,
            "routeCount": len(patterns),
            "qualified": bool(patterns),
            "reason": reason,
        })

    payload = {
        "schemaVersion": 1,
        "requestVersion": request.get("requestVersion"),
        "source": request.get("source"),
        "shardIndex": args.shard_index,
        "shardCount": args.shard_count,
        "transport": transport,
        "providerCount": len(selected),
        "qualifiedCount": sum(1 for row in results if row.get("qualified") is True),
        "providers": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"PROVIDER_BULK_ROUTE_DISCOVERY shard={args.shard_index}/{args.shard_count} "
        f"providers={len(selected)} qualified={payload['qualifiedCount']} transport={transport}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
