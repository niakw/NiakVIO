#!/usr/bin/env python3
"""Fast report-only Provider v3 yield census.

Runs one representative real work for every canonical semantic capability of
all providers (movie, TV, anime) through the same Node-compatible Nuvio probe.
It validates returned media endpoints and content identity, but never mutates
activation. This is deliberately much faster than the broad catalogue Lab and
is intended as a pre-Lab regression signal.
"""
from __future__ import annotations

import concurrent.futures
import json
import os
import subprocess
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manifest.json"
CORPUS = ROOT / ".github" / "triggers" / "nuvio-client-lab.json"
PROBE = ROOT / "scripts" / "nuvio_tv_probe_tmdb_ci.cjs"
OUTPUT = ROOT / "provider-v3-quick-yield.json"
WORKERS = max(1, min(int(os.environ.get("NIAKVIO_QUICK_YIELD_WORKERS", "12")), 20))
TIMEOUT = max(20, min(int(os.environ.get("NIAKVIO_QUICK_YIELD_TIMEOUT", "45")), 90))
REPRESENTATIVE = {
    "movie": "interstellar",
    "tv": "breaking-bad-s01e01",
    "anime": "jujutsu-kaisen-s01e01",
}


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(path)
    return value


def semantic_types(row: dict[str, Any]) -> list[str]:
    values = row.get("canonicalSupportedTypes") or row.get("supportedTypes") or []
    out: list[str] = []
    for value in values:
        item = str(value or "").strip().casefold()
        if item in REPRESENTATIVE and item not in out:
            out.append(item)
    return out


def parse_probe(stdout: str) -> dict[str, Any] | None:
    for raw in reversed(stdout.splitlines()):
        raw = raw.strip()
        if not raw.startswith("{"):
            continue
        try:
            value = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict) and "playable_stream_count" in value:
            return value
    return None


def build_tasks() -> tuple[list[dict[str, Any]], int]:
    manifest = load(MANIFEST)
    corpus = load(CORPUS)
    fixture_rows = {
        str(row.get("slug") or ""): row.get("fixture")
        for row in corpus.get("fixtures") or []
        if isinstance(row, dict) and isinstance(row.get("fixture"), dict)
    }
    fixtures: dict[str, dict[str, Any]] = {}
    for media_type, slug in REPRESENTATIVE.items():
        fixture = fixture_rows.get(slug)
        if not isinstance(fixture, dict):
            raise RuntimeError(f"missing representative fixture {slug}")
        fixtures[media_type] = fixture

    tasks: list[dict[str, Any]] = []
    providers = 0
    for row in manifest.get("scrapers") or []:
        if not isinstance(row, dict):
            continue
        provider_id = str(row.get("id") or "").strip().casefold()
        filename = str(row.get("filename") or "").strip()
        if not provider_id or not filename or not (ROOT / filename).is_file():
            continue
        providers += 1
        types = semantic_types(row)
        for media_type in types:
            tasks.append({
                "provider_id": provider_id,
                "provider_name": str(row.get("name") or row.get("id") or provider_id),
                "filename": filename,
                "semantic_type": media_type,
                "fixture": fixtures[media_type],
            })
    return tasks, providers


def run(task: dict[str, Any]) -> dict[str, Any]:
    started = time.monotonic()
    command = [
        "node",
        str(PROBE),
        str(ROOT / task["filename"]),
        json.dumps(task["fixture"], ensure_ascii=False, separators=(",", ":")),
        "{}",
    ]
    base = {
        "provider_id": task["provider_id"],
        "provider_name": task["provider_name"],
        "semantic_type": task["semantic_type"],
        "fixture_title": str(task["fixture"].get("title") or ""),
    }
    try:
        proc = subprocess.run(
            command,
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=TIMEOUT,
            check=False,
            env=os.environ.copy(),
        )
    except subprocess.TimeoutExpired:
        return {**base, "status": "timeout", "raw": 0, "playable": 0, "verified": 0, "duration_ms": round((time.monotonic() - started) * 1000)}
    except Exception as exc:
        return {**base, "status": "audit_error", "raw": 0, "playable": 0, "verified": 0, "duration_ms": round((time.monotonic() - started) * 1000), "error": type(exc).__name__}

    probe = parse_probe(proc.stdout)
    if probe is None:
        marker = "missing_tmdb_credential" if "missing_tmdb_credential" in proc.stderr else "invalid_probe_output"
        return {**base, "status": marker, "raw": 0, "playable": 0, "verified": 0, "duration_ms": round((time.monotonic() - started) * 1000)}

    raw = int(probe.get("raw_stream_count") or 0)
    playable = int(probe.get("playable_stream_count") or 0)
    verified = int(probe.get("content_verified_count") or probe.get("identity_verified_count") or 0)
    contradictions = int(probe.get("identity_contradiction_count") or 0)
    runtime_error = bool(probe.get("runtime_error"))
    if contradictions:
        status = "wrong_content"
    elif runtime_error:
        status = "runtime_error"
    elif playable and verified:
        status = "playable_verified"
    elif playable:
        status = "playable_unverified"
    elif raw:
        status = "returned_unplayable"
    else:
        status = "no_streams"
    return {
        **base,
        "status": status,
        "raw": raw,
        "playable": playable,
        "verified": verified,
        "contradictions": contradictions,
        "duration_ms": int(probe.get("duration_ms") or round((time.monotonic() - started) * 1000)),
    }


def main() -> int:
    if not (str(os.environ.get("TMDB_API_KEY") or "").strip() or str(os.environ.get("TMDB_ACCESS_TOKEN") or "").strip()):
        raise SystemExit("TMDB_API_KEY or TMDB_ACCESS_TOKEN is required for quick yield census")

    tasks, provider_count = build_tasks()
    rows: list[dict[str, Any]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = [pool.submit(run, task) for task in tasks]
        for future in concurrent.futures.as_completed(futures):
            rows.append(future.result())

    by_provider: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_provider[row["provider_id"]].append(row)

    raw_providers = sorted(provider for provider, values in by_provider.items() if any(int(row.get("raw") or 0) > 0 for row in values))
    playable_providers = sorted(provider for provider, values in by_provider.items() if any(int(row.get("playable") or 0) > 0 for row in values))
    verified_providers = sorted(provider for provider, values in by_provider.items() if any(int(row.get("verified") or 0) > 0 for row in values))
    wrong_content = sorted(provider for provider, values in by_provider.items() if any(row.get("status") == "wrong_content" for row in values))
    statuses = Counter(str(row.get("status") or "unknown") for row in rows)

    type_summary: dict[str, dict[str, int]] = {}
    for media_type in REPRESENTATIVE:
        subset = [row for row in rows if row.get("semantic_type") == media_type]
        type_summary[media_type] = {
            "tasks": len(subset),
            "raw": sum(1 for row in subset if int(row.get("raw") or 0) > 0),
            "playable": sum(1 for row in subset if int(row.get("playable") or 0) > 0),
            "verified": sum(1 for row in subset if int(row.get("verified") or 0) > 0),
        }

    report = {
        "schema_version": 1,
        "environment": "node-fast-real-stream-census-with-tmdb-runtime-context",
        "provider_count": provider_count,
        "task_count": len(tasks),
        "raw_provider_count": len(raw_providers),
        "playable_provider_count": len(playable_providers),
        "verified_provider_count": len(verified_providers),
        "wrong_content_provider_count": len(wrong_content),
        "raw_providers": raw_providers,
        "playable_providers": playable_providers,
        "verified_providers": verified_providers,
        "wrong_content_providers": wrong_content,
        "type_summary": type_summary,
        "status_counts": dict(sorted(statuses.items())),
        "rows": sorted(rows, key=lambda row: (row["provider_id"], row["semantic_type"])),
    }
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        "FIELD_PROVIDER_QUICK_YIELD "
        f"providers={provider_count} tasks={len(tasks)} raw={len(raw_providers)} "
        f"playable={len(playable_providers)} verified={len(verified_providers)} wrong_content={len(wrong_content)}"
    )
    print("FIELD_PROVIDER_QUICK_YIELD_PLAYABLE providers=" + ",".join(playable_providers))
    print("FIELD_PROVIDER_QUICK_YIELD_VERIFIED providers=" + ",".join(verified_providers))
    for media_type, summary in type_summary.items():
        print(
            "FIELD_PROVIDER_QUICK_YIELD_TYPE "
            f"type={media_type} tasks={summary['tasks']} raw={summary['raw']} "
            f"playable={summary['playable']} verified={summary['verified']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
