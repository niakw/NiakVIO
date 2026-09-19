#!/usr/bin/env python3
"""Fingerprint successful upstream stream outputs without persisting ephemeral URLs.

Route recovery already proves that an upstream provider returns streams, but its
report intentionally keeps only counts. For resolver debugging we need to know
which player/output family produced those streams. This audit executes the same
exact upstream/LKG source through provider_worker.cjs and stores only reusable
shape evidence: host, normalized path, query-key names and playback-header names.
No stream URL, token, cookie or query value is persisted.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import tempfile
import urllib.parse
from pathlib import Path
from typing import Any

import recover_provider_routes_from_upstreams as recovery

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "automation" / "provider-upstream-stream-fingerprints-v1.json"


def cid(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def normalize_segment(value: str) -> str:
    raw = urllib.parse.unquote(value or "")
    if not raw:
        return raw
    if raw.isdigit():
        return "{n}"
    if len(raw) >= 12 and re.fullmatch(r"[A-Za-z0-9._~-]+", raw):
        suffix = ""
        match = re.search(r"(\.[A-Za-z0-9]{2,6})$", raw)
        if match:
            suffix = match.group(1).lower()
        return "{id}" + suffix
    return raw[:80]


def fingerprint_stream(stream: dict[str, Any]) -> dict[str, Any] | None:
    raw = str(stream.get("url") or "").strip()
    if not raw:
        return None
    try:
        parsed = urllib.parse.urlsplit(raw)
    except ValueError:
        return None
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return None
    segments = [normalize_segment(part) for part in parsed.path.split("/") if part][:8]
    path_shape = "/" + "/".join(segments)
    query_keys = sorted({urllib.parse.unquote_plus(part.split("=", 1)[0]) for part in parsed.query.split("&") if part})
    headers = stream.get("headers") if isinstance(stream.get("headers"), dict) else {}
    return {
        "host": parsed.hostname.lower(),
        "pathShape": path_shape or "/",
        "queryKeys": query_keys[:24],
        "headerNames": sorted(str(key).lower() for key in headers)[:24],
        "scheme": parsed.scheme,
    }


def run_worker_full(path: Path, fixture: dict[str, Any], *, upstream: bool, timeout: int) -> dict[str, Any]:
    actual_fixture = recovery.worker_fixture(fixture, upstream)
    cmd = [
        "node",
        str(recovery.WORKER),
        str(path),
        json.dumps(actual_fixture, ensure_ascii=False, separators=(",", ":")),
        json.dumps(recovery.context_for(fixture), ensure_ascii=False, separators=(",", ":")),
    ]
    try:
        proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=timeout, check=False)
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "timeout", "streams": []}
    result: dict[str, Any] | None = None
    for line in proc.stdout.splitlines():
        if line.startswith("NUVIO_HEALTH_RESULT="):
            try:
                value = json.loads(line.split("=", 1)[1])
            except json.JSONDecodeError:
                continue
            if isinstance(value, dict):
                result = value
    return result or {"ok": False, "error": "worker_no_result", "streams": []}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", action="append", required=True)
    parser.add_argument("--timeout", type=int, default=55)
    parser.add_argument("--output", type=Path, default=OUT.relative_to(ROOT))
    args = parser.parse_args()

    requested = []
    for raw in args.provider:
        value = cid(raw)
        if value and value not in requested:
            requested.append(value)

    local = recovery.manifest_catalog()
    unknown = [provider for provider in requested if provider not in local]
    if unknown:
        raise SystemExit("unknown providers: " + ",".join(unknown))

    parity = recovery.load(recovery.PARITY)
    source_map = {
        cid(row.get("providerId")): str(row.get("upstreamSource") or "") or None
        for row in parity.get("providers") or []
        if isinstance(row, dict)
    }
    lkg = recovery.lkg_rows()
    current = recovery.current_upstream_catalog(recovery.source_config())
    rows: list[dict[str, Any]] = []

    with tempfile.TemporaryDirectory(prefix="niakvio-stream-fingerprint-") as tmp_name:
        tmp = Path(tmp_name)
        for provider in requested:
            source_id = source_map.get(provider)
            try:
                source_path, source_meta = recovery.source_for_provider(
                    provider,
                    source_id,
                    lkg,
                    current,
                    {provider: local[provider]},
                    tmp,
                )
            except Exception as exc:
                rows.append({"providerId": provider, "status": "source-unavailable", "error": type(exc).__name__, "tasks": []})
                continue

            tasks = []
            for semantic_type in recovery.semantic_types(local[provider]["entry"]):
                for fixture in recovery.FIXTURES[semantic_type]:
                    result = run_worker_full(source_path, fixture, upstream=bool(source_id), timeout=max(15, min(int(args.timeout), 120)))
                    fingerprints = []
                    seen = set()
                    for stream in result.get("streams") or []:
                        if not isinstance(stream, dict):
                            continue
                        fp = fingerprint_stream(stream)
                        if not fp:
                            continue
                        key = json.dumps(fp, sort_keys=True, separators=(",", ":"))
                        if key in seen:
                            continue
                        seen.add(key)
                        fingerprints.append(fp)
                    tasks.append({
                        "fixture": fixture["slug"],
                        "semanticType": semantic_type,
                        "rawStreamCount": int(result.get("raw_stream_count") or 0),
                        "streamCount": int(result.get("stream_count") or 0),
                        "fingerprints": fingerprints[:40],
                    })
                    hosts = sorted({fp["host"] for fp in fingerprints})
                    print(
                        "FIELD_UPSTREAM_STREAM_FINGERPRINT "
                        f"provider={provider} type={semantic_type} fixture={fixture['slug']} "
                        f"streams={int(result.get('stream_count') or 0)} hosts={','.join(hosts) or '-'}",
                        flush=True,
                    )
            rows.append({
                "providerId": provider,
                "sourceId": source_id,
                "sourceSha256": source_meta.get("sha256"),
                "status": "ok",
                "tasks": tasks,
            })

    report = {
        "schemaVersion": 1,
        "privacyModel": "host-path-shape-query-key-names-only",
        "providers": rows,
    }
    out = args.output if args.output.is_absolute() else ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"UPSTREAM_STREAM_FINGERPRINT_V1_OK providers={len(rows)} output={out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
