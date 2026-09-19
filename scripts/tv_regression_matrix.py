#!/usr/bin/env python3
from __future__ import annotations

import concurrent.futures
import json
import os
import re
import subprocess
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manifest.json"
PROBE = ROOT / "scripts" / "nuvio_tv_probe_v2.cjs"
OUTPUT = Path(os.environ.get("NUVIO_TV_MATRIX_OUTPUT", ROOT / "automation" / "tv-regression-matrix.json"))
WORKERS = max(1, min(int(os.environ.get("NUVIO_TV_MATRIX_WORKERS", "6")), 8))
TIMEOUT = max(30, min(int(os.environ.get("NUVIO_TV_MATRIX_TIMEOUT", "85")), 120))
PROVIDER_FILTER = {
    value.strip().casefold()
    for value in os.environ.get("NUVIO_TV_MATRIX_PROVIDERS", "").split(",")
    if value.strip()
}
FIXTURE_FILTER = {
    value.strip()
    for value in os.environ.get("NUVIO_TV_MATRIX_FIXTURES", "").split(",")
    if value.strip()
}

FIXTURES: dict[str, dict[str, Any]] = {
    "revenant_s01e01": {
        "label": "Revenant S01E01",
        "tmdbId": "210702",
        "mediaType": "tv",
        "season": 1,
        "episode": 1,
        "title": "Revenant",
        "year": 2023,
    },
    "breaking_bad_s01e01": {
        "label": "Breaking Bad S01E01",
        "tmdbId": "1396",
        "mediaType": "tv",
        "season": 1,
        "episode": 1,
        "title": "Breaking Bad",
        "year": 2008,
    },
    "mushoku_tensei_s01e01": {
        "label": "Mushoku Tensei: Jobless Reincarnation S01E01",
        "tmdbId": "94664",
        "mediaType": "tv",
        "season": 1,
        "episode": 1,
        "title": "Mushoku Tensei: Jobless Reincarnation",
        "year": 2021,
        "category": "anime",
    },
    "interstellar": {
        "label": "Interstellar",
        "tmdbId": "157336",
        "mediaType": "movie",
        "title": "Interstellar",
        "year": 2014,
    },
}

VF_RE = re.compile(r"(?:\bvf\b|vff|vfq|french|fran[cç]ais|multi|dual[- ]?audio|vostfr)", re.I)
URL_RE = re.compile(r"(?:https?|magnet|acestream|torrent):[^\s\"']+", re.I)


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(path)
    return value


def canonical_types(row: dict[str, Any]) -> set[str]:
    values = row.get("supportedTypes") or row.get("types") or []
    if isinstance(values, str):
        values = [values]
    return {str(v).strip().casefold() for v in values if str(v).strip()}


def sanitize(value: Any, limit: int = 600) -> str | None:
    if value is None:
        return None
    text = URL_RE.sub("[endpoint]", str(value)).replace("\r", " ").replace("\n", " ").strip()
    return text[:limit] or None


def parse_probe(stdout: str) -> dict[str, Any] | None:
    for raw in reversed(stdout.splitlines()):
        raw = raw.strip()
        if not raw.startswith("{"):
            continue
        try:
            value = json.loads(raw)
        except Exception:
            continue
        if isinstance(value, dict) and "playable_stream_count" in value:
            return value
    return None


def compact_stream(item: dict[str, Any], index: int) -> dict[str, Any]:
    row = item.get("row") if isinstance(item.get("row"), dict) else {}
    media = item.get("media") if isinstance(item.get("media"), dict) else {}
    raw_url = str(media.get("url") or row.get("url") or "")
    try:
        host = urlsplit(raw_url).hostname or ""
    except Exception:
        host = ""
    metadata = " ".join(str(row.get(k) or "") for k in ("name", "title", "language", "quality"))
    return {
        "index": index,
        "name": sanitize(row.get("name"), 180),
        "title": sanitize(row.get("title"), 220),
        "language": sanitize(row.get("language"), 80),
        "quality": sanitize(row.get("quality"), 80),
        "host": host,
        "playable": bool(media.get("playable")),
        "status": media.get("status"),
        "kind": media.get("kind"),
        "content_type": sanitize(media.get("content_type"), 120),
        "error": sanitize(media.get("error"), 240),
        "hls_master": bool(media.get("hls_master")),
        "hls_audio_group_count": int(media.get("hls_audio_group_count") or 0),
        "hls_external_audio_count": int(media.get("hls_external_audio_count") or 0),
        "hls_external_audio_playable": media.get("hls_external_audio_playable"),
        "vf_hint": bool(VF_RE.search(metadata)),
    }


def run_task(task: dict[str, Any]) -> dict[str, Any]:
    started = time.monotonic()
    cmd = [
        "node",
        str(PROBE),
        str(ROOT / task["filename"]),
        json.dumps(task["fixture"], ensure_ascii=False, separators=(",", ":")),
        "{}",
    ]
    try:
        proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=TIMEOUT, check=False)
        probe = parse_probe(proc.stdout)
        if probe is None:
            return {**task["identity"], "fixture": task["fixture_name"], "status": "probe_output_invalid", "duration_ms": round((time.monotonic()-started)*1000), "raw": 0, "playable": 0, "runtime_error": sanitize(proc.stderr or proc.stdout), "streams": []}
        streams = [compact_stream(item, i) for i, item in enumerate(probe.get("streams") or []) if isinstance(item, dict)]
        playable_indexes = [s["index"] for s in streams if s["playable"]]
        first_playable_index = min(playable_indexes) if playable_indexes else None
        dead_before_playable = 0
        if first_playable_index is not None:
            dead_before_playable = sum(1 for s in streams if s["index"] < first_playable_index and not s["playable"])
        raw_count = int(probe.get("raw_stream_count") or 0)
        playable_count = int(probe.get("playable_stream_count") or 0)
        status = "playable" if playable_count else ("returned_unplayable" if raw_count else "no_streams")
        if probe.get("runtime_error"):
            status = "runtime_error"
        return {
            **task["identity"],
            "fixture": task["fixture_name"],
            "status": status,
            "duration_ms": int(probe.get("duration_ms") or round((time.monotonic()-started)*1000)),
            "raw": raw_count,
            "playable": playable_count,
            "runtime_error": sanitize(probe.get("runtime_error")),
            "first_playable_index": first_playable_index,
            "dead_before_playable": dead_before_playable,
            "vf_playable": sum(1 for s in streams if s["playable"] and s["vf_hint"]),
            "streams": streams,
        }
    except subprocess.TimeoutExpired:
        return {**task["identity"], "fixture": task["fixture_name"], "status": "timeout", "duration_ms": TIMEOUT*1000, "raw": 0, "playable": 0, "runtime_error": f"timeout after {TIMEOUT}s", "streams": []}
    except Exception as exc:
        return {**task["identity"], "fixture": task["fixture_name"], "status": "audit_error", "duration_ms": round((time.monotonic()-started)*1000), "raw": 0, "playable": 0, "runtime_error": sanitize(exc), "streams": []}


def build_tasks() -> list[dict[str, Any]]:
    manifest = load_json(MANIFEST)
    tasks: list[dict[str, Any]] = []
    for row in manifest.get("scrapers") or []:
        if not isinstance(row, dict):
            continue
        provider_id = str(row.get("id") or "").strip()
        provider_key = provider_id.casefold()
        filename = str(row.get("filename") or "").strip()
        if not provider_id or not filename or not (ROOT / filename).is_file():
            continue
        if PROVIDER_FILTER and provider_key not in PROVIDER_FILTER:
            continue
        types = canonical_types(row)
        identity = {
            "provider_id": provider_key,
            "provider_name": str(row.get("name") or provider_id),
            "enabled": bool(row.get("enabled")),
            "disabled_platforms": row.get("disabledPlatforms") or [],
            "supported_types": sorted(types),
            "filename": filename,
        }
        for name, fixture in FIXTURES.items():
            if FIXTURE_FILTER and name not in FIXTURE_FILTER:
                continue
            if fixture["mediaType"] == "movie":
                if "movie" not in types:
                    continue
            else:
                if "tv" not in types and not (name == "mushoku_tensei_s01e01" and "anime" in types):
                    continue
            tasks.append({"identity": identity, "filename": filename, "fixture_name": name, "fixture": fixture})
    return tasks


def main() -> int:
    tasks = build_tasks()
    if not tasks:
        raise SystemExit("TV matrix selected zero tasks")
    rows: list[dict[str, Any]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as pool:
        future_map = {pool.submit(run_task, task): task for task in tasks}
        for index, future in enumerate(concurrent.futures.as_completed(future_map), 1):
            row = future.result()
            rows.append(row)
            print(f"[{index}/{len(tasks)}] {row['provider_id']} {row['fixture']}: {row['status']} raw={row['raw']} playable={row['playable']} vf={row.get('vf_playable',0)} dead_before={row.get('dead_before_playable',0)}", flush=True)

    rows.sort(key=lambda x: (x["fixture"], x["provider_id"]))
    by_fixture: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_fixture[row["fixture"]].append(row)

    fixture_summary: dict[str, Any] = {}
    for fixture, items in by_fixture.items():
        fixture_summary[fixture] = {
            "providers_tested": len(items),
            "providers_with_raw": sum(1 for r in items if r["raw"] > 0),
            "providers_playable": sum(1 for r in items if r["playable"] > 0),
            "providers_vf_playable": sum(1 for r in items if r.get("vf_playable", 0) > 0),
            "enabled_playable": sum(1 for r in items if r["enabled"] and r["playable"] > 0),
            "disabled_but_playable": sorted(r["provider_id"] for r in items if not r["enabled"] and r["playable"] > 0),
            "dead_first_but_later_playable": sorted(r["provider_id"] for r in items if int(r.get("dead_before_playable") or 0) > 0),
            "runtime_errors": sorted(r["provider_id"] for r in items if r["status"] in {"runtime_error", "audit_error", "probe_output_invalid"}),
            "timeouts": sorted(r["provider_id"] for r in items if r["status"] == "timeout"),
        }

    report = {
        "schema_version": 2,
        "generated_at_epoch": int(time.time()),
        "platform": "Nuvio TV / Android TV runtime contract",
        "provider_filter": sorted(PROVIDER_FILTER),
        "fixture_filter": sorted(FIXTURE_FILTER),
        "fixtures": FIXTURES,
        "tasks": len(rows),
        "providers": len({r["provider_id"] for r in rows}),
        "summary": fixture_summary,
        "error_counts": dict(Counter(r["status"] for r in rows)),
        "rows": rows,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"summary": fixture_summary, "tasks": len(rows)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
