#!/usr/bin/env python3
from __future__ import annotations

import concurrent.futures
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "manifest.json"
HEALTH_CONFIG_PATH = ROOT / "health-config.json"
PATCH_PATH = ROOT / "scripts" / "provider_patches" / "nuvio_tv_direct_media_v2.py"
OUTPUT_PATH = ROOT / "automation" / "nuvio-tv-global-audit.json"
CANDIDATE_PATH = ROOT / "automation" / "nuvio-tv-global-candidates.json"
STAGING = ROOT / "staging" / "nuvio-tv-global-audit"

ANIME_HINT = re.compile(
    r"(?:anime|manga|vost|sama|mugi|sekai|otaku|papa(?:dustream)?|voiranime|french[-_ ]?manga)",
    re.I,
)
LEGACY_MARKERS = (
    "NUVIO_ADAPTIVE_RUNTIME_RECOVERY_",
    "NUVIO_STREAM_OUTPUT_SANITIZER_",
    "NUVIO_TV_DIRECT_MEDIA_V1",
)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_apply(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import patch module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.apply


def first_fixture(config: dict[str, Any], category: str) -> dict[str, Any]:
    rows = config.get("fixtures", {}).get(category, [])
    if not rows:
        raise RuntimeError(f"missing fixture category: {category}")
    fixture = dict(rows[0])
    fixture.setdefault("category", category)
    return fixture


def fixtures_for(row: dict[str, Any], config: dict[str, Any]) -> list[dict[str, Any]]:
    identity = " ".join(
        str(row.get(key) or "") for key in ("id", "name", "displayName", "description")
    )
    supported = {
        str(value).strip().casefold()
        for value in (row.get("supportedTypes") or row.get("types") or [])
        if str(value).strip()
    }
    anime = bool(ANIME_HINT.search(identity))
    fixtures: list[dict[str, Any]] = []

    if anime and ("tv" in supported or not supported):
        fixtures.append(first_fixture(config, "anime"))
    else:
        if "movie" in supported or not supported:
            fixtures.append(first_fixture(config, "movie"))
        if "tv" in supported:
            fixtures.append(first_fixture(config, "tv"))

    if not fixtures:
        fixtures.append(first_fixture(config, "movie"))
    return fixtures[:2]


def parse_probe_stdout(stdout: str) -> dict[str, Any] | None:
    for line in reversed(stdout.splitlines()):
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            value = json.loads(line)
        except Exception:
            continue
        if isinstance(value, dict) and "playable_stream_count" in value:
            return value
    return None


def compact_media(item: dict[str, Any]) -> dict[str, Any]:
    row = item.get("row") if isinstance(item.get("row"), dict) else {}
    media = item.get("media") if isinstance(item.get("media"), dict) else {}
    return {
        "name": str(row.get("name") or row.get("title") or "")[:180],
        "url": str(media.get("url") or row.get("url") or "")[:1000],
        "playable": bool(media.get("playable")),
        "kind": media.get("kind"),
        "status": media.get("status"),
        "content_type": media.get("content_type"),
        "starts_extm3u": bool(media.get("starts_extm3u")),
        "binary_signature": media.get("binary_signature"),
        "error": media.get("error"),
    }


def compact_result(result: dict[str, Any] | None) -> dict[str, Any]:
    if not result:
        return {
            "ok": False,
            "runtime_error": "probe output missing",
            "raw_stream_count": 0,
            "playable_stream_count": 0,
            "duration_ms": None,
            "streams": [],
        }
    return {
        "ok": bool(result.get("ok")),
        "runtime_error": result.get("runtime_error"),
        "raw_stream_count": int(result.get("raw_stream_count") or 0),
        "playable_stream_count": int(result.get("playable_stream_count") or 0),
        "duration_ms": result.get("duration_ms"),
        "streams": [compact_media(item) for item in (result.get("streams") or [])[:6]],
    }


def run_probe(provider_path: Path, fixture: dict[str, Any], timeout_seconds: int = 95) -> dict[str, Any]:
    env = dict(os.environ)
    env["NODE_OPTIONS"] = "--max-old-space-size=768"
    try:
        process = subprocess.run(
            [
                "node",
                "scripts/nuvio_tv_probe_v2.cjs",
                str(provider_path),
                json.dumps(fixture, ensure_ascii=False),
                "{}",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            env=env,
        )
    except subprocess.TimeoutExpired as error:
        return {
            "ok": False,
            "returncode": 124,
            "probe": compact_result(None) | {"runtime_error": f"timeout after {timeout_seconds}s"},
            "stderr_tail": str(error)[-1000:],
        }
    except Exception as error:
        return {
            "ok": False,
            "returncode": 1,
            "probe": compact_result(None) | {"runtime_error": f"{type(error).__name__}: {error}"},
            "stderr_tail": "",
        }

    parsed = parse_probe_stdout(process.stdout)
    compact = compact_result(parsed)
    return {
        "ok": compact["playable_stream_count"] > 0,
        "returncode": process.returncode,
        "probe": compact,
        "stderr_tail": process.stderr[-1200:],
    }


def score_fixture(result: dict[str, Any]) -> tuple[int, int, int]:
    probe = result.get("probe") or {}
    playable = int(probe.get("playable_stream_count") or 0)
    raw = int(probe.get("raw_stream_count") or 0)
    clean = sum(1 for item in probe.get("streams") or [] if item.get("playable") and not item.get("error"))
    return (1 if playable else 0, playable, clean if clean else raw)


def aggregate(results: list[dict[str, Any]]) -> dict[str, Any]:
    playable_fixtures = sum(1 for result in results if (result.get("probe") or {}).get("playable_stream_count"))
    raw_fixtures = sum(1 for result in results if (result.get("probe") or {}).get("raw_stream_count"))
    return {
        "fixture_count": len(results),
        "playable_fixture_count": playable_fixtures,
        "raw_fixture_count": raw_fixtures,
        "playable_stream_count": sum(int((result.get("probe") or {}).get("playable_stream_count") or 0) for result in results),
        "raw_stream_count": sum(int((result.get("probe") or {}).get("raw_stream_count") or 0) for result in results),
        "runtime_error_count": sum(1 for result in results if (result.get("probe") or {}).get("runtime_error")),
    }


def run_variant(path: Path, fixtures: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for fixture in fixtures:
        result = run_probe(path, fixture)
        result["fixture"] = {
            key: fixture.get(key)
            for key in ("label", "tmdbId", "mediaType", "season", "episode", "title", "year", "category")
            if fixture.get(key) is not None
        }
        output.append(result)
    return output


def no_regression(baseline: list[dict[str, Any]], candidate: list[dict[str, Any]]) -> bool:
    for before, after in zip(baseline, candidate):
        if score_fixture(before)[0] > score_fixture(after)[0]:
            return False
    return True


def strictly_better(baseline: list[dict[str, Any]], candidate: list[dict[str, Any]]) -> bool:
    before = aggregate(baseline)
    after = aggregate(candidate)
    return no_regression(baseline, candidate) and (
        after["playable_fixture_count"],
        after["playable_stream_count"],
    ) > (
        before["playable_fixture_count"],
        before["playable_stream_count"],
    )


def classify(baseline: list[dict[str, Any]], best: list[dict[str, Any]] | None, improved: bool) -> str:
    base = aggregate(baseline)
    if base["playable_fixture_count"] == base["fixture_count"] and base["fixture_count"]:
        return "strict_healthy"
    if improved and best:
        return "benefits_from_direct_media_v2"
    if base["raw_stream_count"] > 0 and base["playable_stream_count"] == 0:
        return "returns_non_media_or_blocked_urls"
    if base["runtime_error_count"]:
        return "runtime_error_or_timeout"
    if base["raw_stream_count"] == 0:
        return "no_streams_under_tv_contract"
    return "partially_playable"


def audit_provider(
    row: dict[str, Any],
    config: dict[str, Any],
    apply_patch: Any,
) -> dict[str, Any]:
    provider_id = str(row.get("id") or "").strip()
    filename = str(row.get("filename") or "").strip()
    result: dict[str, Any] = {
        "id": provider_id,
        "name": row.get("name") or provider_id,
        "enabled": bool(row.get("enabled", True)),
        "filename": filename,
        "supported_types": row.get("supportedTypes") or row.get("types") or [],
        "fixtures": [],
        "baseline": [],
        "variants": {},
        "recommended_variant": None,
        "classification": None,
    }

    if not filename or filename.startswith(("http://", "https://", "../")):
        result["classification"] = "external_or_missing_local_bundle"
        return result
    source_path = ROOT / filename
    if not source_path.is_file():
        result["classification"] = "missing_local_bundle"
        return result

    fixtures = fixtures_for(row, config)
    result["fixtures"] = [dict(fixture) for fixture in fixtures]
    source = source_path.read_text(encoding="utf-8", errors="replace")
    source_sha = hashlib.sha256(source.encode("utf-8")).hexdigest()
    result["source_sha256"] = source_sha
    baseline = run_variant(source_path, fixtures)
    result["baseline"] = baseline
    baseline_agg = aggregate(baseline)
    result["baseline_summary"] = baseline_agg

    if baseline_agg["playable_fixture_count"] == baseline_agg["fixture_count"] and baseline_agg["fixture_count"]:
        result["classification"] = "strict_healthy"
        return result

    variants: list[tuple[str, dict[str, Any]]] = [
        (
            "append",
            {
                "provider_name": str(row.get("name") or provider_id),
                "max_candidates": 14,
                "timeout_ms": 14000,
            },
        )
    ]
    if any(marker in source for marker in LEGACY_MARKERS):
        variants.append(
            (
                "strip_legacy_then_append",
                {
                    "provider_name": str(row.get("name") or provider_id),
                    "max_candidates": 14,
                    "timeout_ms": 14000,
                    "strip_unproven_wrappers": True,
                },
            )
        )

    best_name: str | None = None
    best_results: list[dict[str, Any]] | None = None
    best_score = (
        baseline_agg["playable_fixture_count"],
        baseline_agg["playable_stream_count"],
        baseline_agg["raw_stream_count"],
    )

    for variant_name, options in variants:
        patched = apply_patch(source, options)
        sha = hashlib.sha256(patched.encode("utf-8")).hexdigest()
        candidate = STAGING / provider_id / f"{variant_name}--{sha[:16]}.js"
        candidate.parent.mkdir(parents=True, exist_ok=True)
        candidate.write_text(patched, encoding="utf-8")
        variant_results = run_variant(candidate, fixtures)
        summary = aggregate(variant_results)
        variant = {
            "options": options,
            "candidate_sha256": sha,
            "candidate_path": str(candidate.relative_to(ROOT)),
            "results": variant_results,
            "summary": summary,
            "no_regression": no_regression(baseline, variant_results),
            "strictly_better": strictly_better(baseline, variant_results),
        }
        result["variants"][variant_name] = variant
        score = (
            summary["playable_fixture_count"],
            summary["playable_stream_count"],
            summary["raw_stream_count"],
        )
        if variant["no_regression"] and score > best_score:
            best_score = score
            best_name = variant_name
            best_results = variant_results

    improved = bool(best_name and best_results and strictly_better(baseline, best_results))
    if improved:
        result["recommended_variant"] = best_name
    result["classification"] = classify(baseline, best_results, improved)
    return result


def main() -> int:
    manifest = load_json(MANIFEST_PATH)
    config = load_json(HEALTH_CONFIG_PATH)
    apply_patch = load_apply(PATCH_PATH)
    rows = [row for row in manifest.get("scrapers") or [] if isinstance(row, dict) and row.get("id")]
    STAGING.mkdir(parents=True, exist_ok=True)
    workers = max(1, min(int(os.environ.get("NUVIO_GLOBAL_AUDIT_CONCURRENCY", "4")), 8))

    results: list[dict[str, Any]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(audit_provider, row, config, apply_patch): row for row in rows}
        for index, future in enumerate(concurrent.futures.as_completed(futures), start=1):
            row = futures[future]
            provider_id = str(row.get("id") or "unknown")
            try:
                result = future.result()
            except Exception as error:
                result = {
                    "id": provider_id,
                    "name": row.get("name") or provider_id,
                    "enabled": bool(row.get("enabled", True)),
                    "filename": row.get("filename"),
                    "classification": "audit_exception",
                    "error": f"{type(error).__name__}: {error}",
                }
            results.append(result)
            print(f"[{index}/{len(rows)}] {provider_id}: {result.get('classification')}", flush=True)

    results.sort(key=lambda item: str(item.get("id") or "").casefold())
    counts: dict[str, int] = {}
    for item in results:
        key = str(item.get("classification") or "unknown")
        counts[key] = counts.get(key, 0) + 1

    candidates = [
        {
            "id": item["id"],
            "name": item.get("name"),
            "enabled": item.get("enabled"),
            "filename": item.get("filename"),
            "source_sha256": item.get("source_sha256"),
            "recommended_variant": item.get("recommended_variant"),
            "variant": (item.get("variants") or {}).get(item.get("recommended_variant")),
            "baseline_summary": item.get("baseline_summary"),
        }
        for item in results
        if item.get("classification") == "benefits_from_direct_media_v2"
    ]

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "manifest_version": manifest.get("version"),
        "contract": "NuvioTV getStreams(tmdbId, mediaType, season, episode), settings from global SCRAPER_SETTINGS",
        "media_gate": "HLS response starts with #EXTM3U, DASH MPD, or real MP4/Matroska/MPEG-TS signature",
        "provider_count": len(results),
        "enabled_provider_count": sum(1 for item in results if item.get("enabled")),
        "classification_counts": counts,
        "candidate_count": len(candidates),
        "providers": results,
    }
    candidate_report = {
        "generated_at": report["generated_at"],
        "manifest_version": report["manifest_version"],
        "candidate_count": len(candidates),
        "candidates": candidates,
    }
    write_json(OUTPUT_PATH, report)
    write_json(CANDIDATE_PATH, candidate_report)
    print(json.dumps({
        "provider_count": report["provider_count"],
        "classification_counts": counts,
        "candidate_count": len(candidates),
        "candidate_ids": [item["id"] for item in candidates],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
