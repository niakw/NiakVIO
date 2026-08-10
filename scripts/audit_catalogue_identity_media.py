#!/usr/bin/env python3
"""Finite cross-provider NuvioTV media/identity audit.

The audit is intentionally report-only: it never flips provider activation.
It exercises every published provider relevant to the requested media type and
records only sanitized counts/diagnostics; raw stream endpoints are discarded.

Coverage:
- every TV-capable provider: a South-Korean series fixture (Squid Game S01E01),
- every movie-capable provider: an impossible TMDb id to detect false matches,
- every VF movie provider: Interstellar,
- every VF anime provider: Jujutsu Kaisen S01E01,
- named HLS regression providers receive all compatible representative fixtures.
"""
from __future__ import annotations

import concurrent.futures
import json
import os
import re
import subprocess
import time
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manifest.json"
VF_MANIFEST = ROOT / "vf" / "manifest.json"
PROBE = ROOT / "scripts" / "nuvio_tv_probe_v2.cjs"
OUTPUT = Path(os.environ.get("NUVIO_CATALOGUE_AUDIT_OUTPUT", ROOT / "audit-output" / "catalogue-media-audit.json"))
WORKERS = max(1, min(int(os.environ.get("NUVIO_CATALOGUE_AUDIT_WORKERS", "5")), 8))
TIMEOUT = max(25, min(int(os.environ.get("NUVIO_CATALOGUE_AUDIT_TIMEOUT", "85")), 120))

SUSPECTS = {
    "papadustream",
    "streamzo",
    "coflix",
    "hdghartv",
    "hdhub4u",
    "4khdhub",
    "4khdhubnew",
}

FIXTURES: dict[str, dict[str, Any]] = {
    "kdrama_squid_game_s01e01": {
        "label": "Squid Game S01E01",
        "tmdbId": "93405",
        "mediaType": "tv",
        "season": 1,
        "episode": 1,
        "title": "Squid Game",
        "year": 2021,
    },
    "impossible_movie": {
        "label": "Impossible identity sentinel",
        "tmdbId": "999999999",
        "mediaType": "movie",
        "title": "Nuvio Impossible Fixture QZXV",
        "year": 2099,
    },
    "vf_interstellar": {
        "label": "Interstellar",
        "tmdbId": "157336",
        "mediaType": "movie",
        "title": "Interstellar",
        "year": 2014,
    },
    "vf_jjk_s01e01": {
        "label": "Jujutsu Kaisen S01E01",
        "tmdbId": "95479",
        "mediaType": "tv",
        "season": 1,
        "episode": 1,
        "title": "Jujutsu Kaisen",
        "year": 2020,
    },
}

URL_RE = re.compile(r"(?:https?|magnet|acestream|torrent):[^\s\"']+", re.I)


def sanitize(value: Any, limit: int = 900) -> str | None:
    if value is None:
        return None
    text = URL_RE.sub("[endpoint]", str(value)).replace("\r", " ").replace("\n", " ").strip()
    return text[:limit] or None


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"invalid JSON object: {path}")
    return value


def canonical_types(row: dict[str, Any]) -> set[str]:
    values = row.get("supportedTypes") or []
    if isinstance(values, str):
        values = [values]
    return {str(value).strip().casefold() for value in values if str(value).strip()}


def parse_probe(stdout: str) -> dict[str, Any] | None:
    for raw in reversed(stdout.splitlines()):
        line = raw.strip()
        if not line.startswith("{"):
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict) and "playable_stream_count" in value:
            return value
    return None


def summarize_media(probe: dict[str, Any]) -> dict[str, Any]:
    rows = probe.get("streams") if isinstance(probe.get("streams"), list) else []
    kind_counts: Counter[str] = Counter()
    errors: Counter[str] = Counter()
    hls_masters = 0
    hls_audio_groups = 0
    hls_external_audio = 0
    hls_external_audio_playable = 0
    hls_variant_failures = 0
    hls_audio_failures = 0
    for item in rows:
        if not isinstance(item, dict) or not isinstance(item.get("media"), dict):
            continue
        media = item["media"]
        kind = str(media.get("kind") or "unknown")
        kind_counts[kind] += 1
        if media.get("error"):
            error = sanitize(media.get("error"), 220) or "unknown"
            errors[error] += 1
            if str(error).startswith("hls_variant_"):
                hls_variant_failures += 1
            if str(error).startswith("hls_audio_"):
                hls_audio_failures += 1
        if media.get("hls_master"):
            hls_masters += 1
        hls_audio_groups += int(media.get("hls_audio_group_count") or 0)
        hls_external_audio += int(media.get("hls_external_audio_count") or 0)
        if media.get("hls_external_audio_playable") is True:
            hls_external_audio_playable += 1
    return {
        "media_kinds": dict(sorted(kind_counts.items())),
        "media_errors": dict(errors.most_common(8)),
        "hls_masters": hls_masters,
        "hls_audio_groups": hls_audio_groups,
        "hls_external_audio": hls_external_audio,
        "hls_external_audio_playable": hls_external_audio_playable,
        "hls_variant_failures": hls_variant_failures,
        "hls_audio_failures": hls_audio_failures,
    }


def run_probe(task: dict[str, Any]) -> dict[str, Any]:
    started = time.monotonic()
    command = [
        "node",
        str(PROBE),
        str(ROOT / task["filename"]),
        json.dumps(task["fixture"], ensure_ascii=False, separators=(",", ":")),
        "{}",
    ]
    try:
        proc = subprocess.run(
            command,
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=TIMEOUT,
            check=False,
        )
        probe = parse_probe(proc.stdout)
        if probe is None:
            return {
                **task["identity"],
                "fixture": task["fixture_name"],
                "status": "probe_output_invalid",
                "exit_code": proc.returncode,
                "duration_ms": round((time.monotonic() - started) * 1000),
                "raw_stream_count": 0,
                "playable_stream_count": 0,
                "runtime_error": sanitize(proc.stderr or proc.stdout),
            }
        raw_count = int(probe.get("raw_stream_count") or 0)
        playable_count = int(probe.get("playable_stream_count") or 0)
        summary = summarize_media(probe)
        status = "playable" if playable_count > 0 else ("returned_unplayable" if raw_count > 0 else "no_streams")
        if probe.get("runtime_error"):
            status = "runtime_error"
        row = {
            **task["identity"],
            "fixture": task["fixture_name"],
            "status": status,
            "exit_code": proc.returncode,
            "duration_ms": int(probe.get("duration_ms") or round((time.monotonic() - started) * 1000)),
            "raw_stream_count": raw_count,
            "playable_stream_count": playable_count,
            "runtime_error": sanitize(probe.get("runtime_error")),
            **summary,
        }
        if task["fixture_name"] == "impossible_movie":
            # Some generic embed providers can mechanically construct a URL for
            # any numeric TMDb id. That is suspicious and remains visible in the
            # report, but only a *playable* result proves an actual wrong-content
            # mapping. Do not fail the audit on an embed that correctly resolves
            # to no media.
            row["identity_candidate_for_unknown_id"] = raw_count > 0
            row["playable_identity_false_positive"] = playable_count > 0
        return row
    except subprocess.TimeoutExpired:
        return {
            **task["identity"],
            "fixture": task["fixture_name"],
            "status": "timeout",
            "exit_code": None,
            "duration_ms": round((time.monotonic() - started) * 1000),
            "raw_stream_count": 0,
            "playable_stream_count": 0,
            "runtime_error": f"probe timeout after {TIMEOUT}s",
        }
    except Exception as exc:  # defensive: one provider must never abort the global audit
        return {
            **task["identity"],
            "fixture": task["fixture_name"],
            "status": "audit_error",
            "exit_code": None,
            "duration_ms": round((time.monotonic() - started) * 1000),
            "raw_stream_count": 0,
            "playable_stream_count": 0,
            "runtime_error": sanitize(exc),
        }


def build_tasks() -> tuple[list[dict[str, Any]], set[str]]:
    manifest = load_json(MANIFEST)
    vf = load_json(VF_MANIFEST)
    vf_ids = {
        str(row.get("id") or "").strip().casefold()
        for row in vf.get("scrapers", [])
        if isinstance(row, dict) and str(row.get("id") or "").strip()
    }
    tasks: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for row in manifest.get("scrapers", []):
        if not isinstance(row, dict):
            continue
        provider_id = str(row.get("id") or "").strip().casefold()
        filename = str(row.get("filename") or "").strip()
        if not provider_id or not filename or not (ROOT / filename).is_file():
            continue
        types = canonical_types(row)
        is_vf = provider_id in vf_ids
        fixture_names: list[str] = []
        if "tv" in types:
            fixture_names.append("kdrama_squid_game_s01e01")
        if "movie" in types:
            fixture_names.append("impossible_movie")
        if is_vf and "movie" in types:
            fixture_names.append("vf_interstellar")
        if is_vf and ("anime" in types or "tv" in types):
            fixture_names.append("vf_jjk_s01e01")
        if provider_id in SUSPECTS:
            if "movie" in types:
                fixture_names.append("vf_interstellar")
            if "tv" in types:
                fixture_names.append("kdrama_squid_game_s01e01")
        identity = {
            "provider_id": provider_id,
            "provider_name": str(row.get("name") or row.get("id") or provider_id),
            "vf": is_vf,
            "enabled": bool(row.get("enabled")),
            "suspect": provider_id in SUSPECTS,
        }
        for fixture_name in fixture_names:
            key = (provider_id, fixture_name)
            if key in seen:
                continue
            seen.add(key)
            tasks.append({
                "identity": identity,
                "filename": filename,
                "fixture_name": fixture_name,
                "fixture": FIXTURES[fixture_name],
            })
    return tasks, vf_ids


def main() -> int:
    tasks, vf_ids = build_tasks()
    rows: list[dict[str, Any]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as executor:
        future_map = {executor.submit(run_probe, task): task for task in tasks}
        for index, future in enumerate(concurrent.futures.as_completed(future_map), 1):
            row = future.result()
            rows.append(row)
            print(
                f"[{index}/{len(tasks)}] {row['provider_id']} {row['fixture']}: "
                f"{row['status']} raw={row.get('raw_stream_count', 0)} playable={row.get('playable_stream_count', 0)}"
            )

    rows.sort(key=lambda row: (row["provider_id"], row["fixture"]))
    unknown_candidates = [row for row in rows if row.get("identity_candidate_for_unknown_id")]
    playable_false_positive = [row for row in rows if row.get("playable_identity_false_positive")]
    hls_failures = [row for row in rows if int(row.get("hls_variant_failures") or 0) or int(row.get("hls_audio_failures") or 0)]
    suspect_rows = [row for row in rows if row.get("suspect")]
    valid_rows = [row for row in rows if row["fixture"] != "impossible_movie"]
    vf_valid = [row for row in valid_rows if row.get("vf")]
    kdrama = [row for row in rows if row["fixture"] == "kdrama_squid_game_s01e01"]

    report = {
        "schema_version": 2,
        "generated_at_epoch": int(time.time()),
        "providers_total": len({row["provider_id"] for row in rows}),
        "vf_providers_total": len(vf_ids),
        "probe_tasks": len(rows),
        "policy": {
            "zero_valid_streams": "coverage_gap_not_disable_signal",
            "impossible_fixture_raw_return": "diagnostic_only_generic_embed_may_construct_url",
            "impossible_fixture_playable_return": "proven_identity_false_positive",
            "hls_child_or_external_audio_failure": "broken_media_graph",
            "raw_endpoints_persisted": False,
        },
        "summary": {
            "valid_fixture_playable_rows": sum(1 for row in valid_rows if int(row.get("playable_stream_count") or 0) > 0),
            "vf_valid_fixture_playable_rows": sum(1 for row in vf_valid if int(row.get("playable_stream_count") or 0) > 0),
            "kdrama_playable_providers": sum(1 for row in kdrama if int(row.get("playable_stream_count") or 0) > 0),
            "unknown_id_candidate_providers": sorted({row["provider_id"] for row in unknown_candidates}),
            "playable_identity_false_positive_providers": sorted({row["provider_id"] for row in playable_false_positive}),
            "hls_graph_failure_providers": sorted({row["provider_id"] for row in hls_failures}),
        },
        "suspects": suspect_rows,
        "rows": rows,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        "catalogue/media audit complete: "
        f"providers={report['providers_total']} tasks={len(rows)} "
        f"playable_identity_false_positive={len(report['summary']['playable_identity_false_positive_providers'])} "
        f"hls_graph_failures={len(report['summary']['hls_graph_failure_providers'])}"
    )
    # Only conclusive failures stop the finite audit. A provider returning no
    # stream is a coverage gap to repair, not a reason to disable it.
    return 1 if playable_false_positive or hls_failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
