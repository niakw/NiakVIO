#!/usr/bin/env python3
"""Terminal-qualify explicitly selected disabled NiakVIO provider artifacts.

This is a report-only recovery harness. It never activates a provider and never
persists media URLs. Each declared semantic lane is tested against a rotating
current corpus and is positive only when the existing terminal verifier proves
actual media.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import json
from pathlib import Path
from typing import Any

import run_provider_upstream_parity_v3 as parity3
from rotating_corpus import default_seed, select_fixtures

ROOT = Path(__file__).resolve().parents[1]
MANIFESTS = (ROOT / "manifest.json", ROOT / "vf" / "manifest.json")
LANES = ("movie", "tv", "anime")


def cid(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def canonical_types(row: dict[str, Any]) -> list[str]:
    raw = row.get("canonicalSupportedTypes") or row.get("supportedTypes") or []
    if isinstance(raw, str):
        raw = [raw]
    values = {cid(v) for v in raw}
    return [lane for lane in LANES if lane in values]


def disabled_rows(requested: set[str]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for manifest_path in MANIFESTS:
        if not manifest_path.is_file():
            continue
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        for raw in data.get("scrapers") or []:
            if not isinstance(raw, dict) or raw.get("enabled") is not False:
                continue
            provider = cid(raw.get("id"))
            if not provider or (requested and provider not in requested):
                continue
            filename = str(raw.get("filename") or "").strip()
            if not filename:
                continue
            path = (manifest_path.parent / filename).resolve()
            if ROOT != path and ROOT not in path.parents:
                raise RuntimeError(f"{provider}: provider path escapes repository")
            if not path.is_file():
                continue
            row = dict(raw)
            row["_path"] = str(path)
            # Prefer a Global row when the same disabled identity is projected
            # into France too; both point to the same retained content bytes.
            if provider not in out or manifest_path == ROOT / "manifest.json":
                out[provider] = row
    missing = sorted(requested - set(out))
    if missing:
        raise SystemExit("disabled provider rows missing: " + ",".join(missing))
    return out


def compact(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "stream_count": int(result.get("stream_count") or 0),
        "candidate_stream_count": int(result.get("candidate_stream_count") or 0),
        "raw_stream_count": int(result.get("raw_stream_count") or 0),
        "terminal_verified": bool(result.get("terminal_verified")),
        "terminal_reasons": list(result.get("terminal_reasons") or [])[:8],
        "http_statuses": list(result.get("http_statuses") or [])[:12],
        "timeout": bool(result.get("timeout")),
        "error_class": result.get("error_class"),
    }


def run_lane(provider: str, row: dict[str, Any], lane: str, samples: int, timeout: int) -> dict[str, Any]:
    fixtures = select_fixtures(
        lane,
        count=max(1, min(samples, 6)),
        seed=default_seed(),
        provider=provider,
    )
    results: list[dict[str, Any]] = []
    positive = None
    for fixture in fixtures:
        payload = parity3.fixture_payload(fixture, lane, upstream=False)
        try:
            result = compact(parity3._run_verified(Path(row["_path"]), payload, timeout))
        except Exception as exc:
            result = {
                "stream_count": 0,
                "candidate_stream_count": 0,
                "raw_stream_count": 0,
                "terminal_verified": False,
                "terminal_reasons": [],
                "http_statuses": [],
                "timeout": False,
                "error_class": type(exc).__name__,
            }
        item = {
            "slug": str(fixture.get("slug") or ""),
            "tmdbId": str(fixture.get("tmdbId") or ""),
            **result,
        }
        results.append(item)
        if item["stream_count"] > 0 and item["terminal_verified"]:
            positive = item
            break
    return {
        "provider": provider,
        "lane": lane,
        "positive": positive is not None,
        "sample_count": len(results),
        "samples": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--providers", required=True, help="Comma-separated disabled provider ids")
    parser.add_argument("--samples-per-lane", type=int, default=3)
    parser.add_argument("--timeout", type=int, default=35)
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--output", default="automation/disabled-candidate-terminal-matrix.json")
    args = parser.parse_args()

    requested = {cid(v) for v in args.providers.split(",") if cid(v)}
    if not requested:
        raise SystemExit("no providers selected")
    rows = disabled_rows(requested)

    tasks: list[tuple[str, dict[str, Any], str]] = []
    for provider, row in sorted(rows.items()):
        lanes = canonical_types(row)
        if not lanes:
            continue
        for lane in lanes:
            tasks.append((provider, row, lane))

    lane_results: list[dict[str, Any]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, min(args.workers, 10))) as pool:
        futures = [
            pool.submit(
                run_lane,
                provider,
                row,
                lane,
                max(1, args.samples_per_lane),
                max(5, min(args.timeout, 90)),
            )
            for provider, row, lane in tasks
        ]
        for future in concurrent.futures.as_completed(futures):
            lane_results.append(future.result())

    provider_summary: dict[str, Any] = {}
    for provider, row in sorted(rows.items()):
        lanes = [r for r in lane_results if r["provider"] == provider]
        positives = sorted(r["lane"] for r in lanes if r["positive"])
        declared = sorted(r["lane"] for r in lanes)
        provider_summary[provider] = {
            "declared_lanes": declared,
            "terminal_positive_lanes": positives,
            "full_terminal": bool(declared) and positives == declared,
            "partial_terminal": bool(positives) and positives != declared,
        }

    payload = {
        "schema_version": 1,
        "authority": "disabled-retained-bytes-terminal-recovery-v1",
        "providers": sorted(rows),
        "provider_summary": provider_summary,
        "lane_results": sorted(lane_results, key=lambda r: (r["provider"], r["lane"])),
    }
    out = Path(args.output)
    if not out.is_absolute():
        out = ROOT / out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    for provider, summary in sorted(provider_summary.items()):
        print(
            "DISABLED_CANDIDATE "
            f"provider={provider} full={str(summary['full_terminal']).lower()} "
            f"positive={','.join(summary['terminal_positive_lanes']) or '-'} "
            f"declared={','.join(summary['declared_lanes']) or '-'}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
