#!/usr/bin/env python3
"""Rotating upstream-vs-NiakVIO parity for the active Hub-46 campaign.

A title is a catalogue sample, never a provider-health verdict. For each declared
semantic lane this harness rotates through the recent global pool and stops early
as soon as it gets useful positive evidence. Clean zero/zero samples are reported
as catalogue misses and never promoted to repair regressions.

The only certain NiakVIO regression class is ``upstream_ok_niakvio_ko``: the
reference upstream returned streams for the exact same work/lane while the local
provider did not. The diagnostic reserve can span the complete 32-title global
lane, but it remains adaptive: it never consumes the remaining candidates after a
useful positive/negative parity proof has been obtained.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any

import run_provider_upstream_parity as parity
import run_provider_upstream_parity_v2 as parity_v2
from rotating_corpus import default_seed, select_fixtures

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCOPE = ROOT / "automation/evidence/hub-lab-matrix-46.json"
DEFAULT_OUT = ROOT / "automation/provider-upstream-parity-v3.json"
LANES = ("movie", "tv", "anime")
MAX_SAMPLES_PER_LANE = 32


def cid(value: object) -> str:
    return parity.cid(value)


def scope_ids(path: Path) -> set[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    rows = data.get("rows") if isinstance(data.get("rows"), list) else []
    ids = {
        cid(row.get("manifestId") or row.get("provider"))
        for row in rows if isinstance(row, dict)
        if cid(row.get("manifestId") or row.get("provider"))
    }
    expected = int(data.get("hubCount") or data.get("providerCount") or len(ids))
    if not ids or len(ids) != expected:
        raise SystemExit(f"parity scope invalid: ids={len(ids)} expected={expected} path={path}")
    return ids


def canonical_lanes(local_row: dict[str, Any], upstream_row: dict[str, Any]) -> list[str]:
    local = parity.semantic_types(local_row)
    upstream = parity.semantic_types(upstream_row)
    chosen = [lane for lane in LANES if lane in local]
    if not chosen:
        chosen = [lane for lane in LANES if lane in upstream]
    return chosen or ["movie"]


def fixture_payload(row: dict[str, Any], lane: str, *, upstream: bool) -> dict[str, Any]:
    fixture = {
        key: value for key, value in row.items()
        if key not in {"slug", "lane"}
    }
    fixture["mediaType"] = lane
    if lane == "anime":
        fixture["category"] = "anime"
        if upstream:
            fixture["mediaType"] = "tv"
            fixture["type"] = "tv"
            fixture.pop("category", None)
    return fixture


def technical(result: dict[str, Any]) -> bool:
    if result.get("timeout"):
        return True
    if str(result.get("error_class") or "").strip():
        return True
    statuses = [int(value) for value in result.get("http_statuses") or []]
    return bool(statuses) and not any(200 <= status < 400 for status in statuses)


def classify_pair(upstream: dict[str, Any], local: dict[str, Any]) -> str:
    up = int(upstream.get("stream_count") or 0) > 0
    lo = int(local.get("stream_count") or 0) > 0
    if up and lo:
        return "both_ok"
    if up and not lo:
        return "upstream_ok_niakvio_ko"
    if not up and lo:
        return "niakvio_ok_upstream_ko"
    up_technical = technical(upstream)
    lo_technical = technical(local)
    if not up_technical and not lo_technical:
        return "catalog_miss_both"
    if lo_technical and not up_technical:
        return "niakvio_technical_upstream_no_stream"
    if up_technical and not lo_technical:
        return "upstream_technical_niakvio_no_stream"
    return "both_technical"


def run_lane(
    provider_id: str,
    lane: str,
    local_path: Path,
    upstream_path: Path,
    *,
    timeout: int,
    sample_count: int,
    seed: str,
) -> dict[str, Any]:
    samples: list[dict[str, Any]] = []
    candidates = select_fixtures(
        lane,
        count=sample_count,
        seed=seed,
        provider=provider_id,
    )
    for candidate in candidates:
        up_fixture = fixture_payload(candidate, lane, upstream=True)
        local_fixture = fixture_payload(candidate, lane, upstream=False)
        upstream = parity.run_worker(upstream_path, up_fixture, timeout)
        local = parity.run_worker(local_path, local_fixture, timeout)
        classification = classify_pair(upstream, local)
        samples.append({
            "fixture": candidate["slug"],
            "tmdbId": str(candidate.get("tmdbId") or ""),
            "classification": classification,
            "upstream": upstream,
            "niakvio": local,
        })
        if classification in {
            "both_ok",
            "upstream_ok_niakvio_ko",
            "niakvio_ok_upstream_ko",
        }:
            break

    classes = [str(row.get("classification") or "") for row in samples]
    if "upstream_ok_niakvio_ko" in classes:
        status = "REGRESSION"
    elif any(value in {"both_ok", "niakvio_ok_upstream_ko"} for value in classes):
        status = "POSITIVE"
    elif classes and all(value == "catalog_miss_both" for value in classes):
        status = "RESAMPLE"
    else:
        status = "TECHNICAL_UNRESOLVED"
    return {
        "lane": lane,
        "status": status,
        "samples": samples,
        "sampleCount": len(samples),
        "candidateCount": len(candidates),
    }


def one_provider(
    provider_id: str,
    local: dict[str, Any],
    upstream: dict[str, Any],
    upstream_path: Path,
    *,
    timeout: int,
    sample_count: int,
    seed: str,
) -> dict[str, Any]:
    lanes = canonical_lanes(local["entry"], upstream["entry"])
    lane_rows = [
        run_lane(
            provider_id,
            lane,
            local["path"],
            upstream_path,
            timeout=timeout,
            sample_count=sample_count,
            seed=seed,
        )
        for lane in lanes
    ]
    lane_states = [row["status"] for row in lane_rows]
    if "REGRESSION" in lane_states:
        status = "REGRESSION"
    elif lane_states and all(value == "POSITIVE" for value in lane_states):
        status = "FULL"
    elif "POSITIVE" in lane_states:
        unresolved = [value for value in lane_states if value != "POSITIVE"]
        status = "RESAMPLE" if unresolved and all(value == "RESAMPLE" for value in unresolved) else "PARTIAL"
    elif lane_states and all(value == "RESAMPLE" for value in lane_states):
        status = "RESAMPLE"
    else:
        status = "ZERO"
    return {
        "providerId": provider_id,
        "upstreamSource": upstream["source"],
        "status": status,
        "lanes": lane_rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    parser.add_argument("--workers", type=int, default=int(os.environ.get("NIAKVIO_PARITY_WORKERS", "8")))
    parser.add_argument("--timeout", type=int, default=int(os.environ.get("NIAKVIO_PARITY_TIMEOUT", "25")))
    parser.add_argument("--provider", action="append", default=[])
    parser.add_argument("--samples-per-lane", type=int, default=int(os.environ.get("NIAKVIO_PARITY_SAMPLES_PER_LANE", "3")))
    parser.add_argument(
        "--scope-matrix",
        type=Path,
        default=Path(os.environ.get("NIAKVIO_PROVIDER_SCOPE_MATRIX", str(DEFAULT_SCOPE))),
    )
    parser.add_argument("--seed", default=None)
    args = parser.parse_args()

    scope_path = args.scope_matrix
    if not scope_path.is_absolute():
        scope_path = ROOT / scope_path
    scoped = scope_ids(scope_path)
    local_all = parity.local_catalog()
    local = {pid: row for pid, row in local_all.items() if pid in scoped}
    missing_local = sorted(scoped - set(local))
    if missing_local or len(local) != len(scoped):
        raise SystemExit(
            f"Hub-46 parity local scope mismatch local={len(local)} expected={len(scoped)} missing={','.join(missing_local)}"
        )

    upstreams, source_errors = parity_v2.upstream_catalog()
    requested = {cid(value) for value in args.provider if cid(value)}
    provider_ids = [
        pid for pid in sorted(local)
        if pid in upstreams and (not requested or pid in requested)
    ]
    missing_upstream = sorted(
        pid for pid in local
        if pid not in upstreams and (not requested or pid in requested)
    )
    seed = str(args.seed if args.seed is not None else default_seed())
    sample_count = max(1, min(MAX_SAMPLES_PER_LANE, int(args.samples_per_lane)))
    rows: list[dict[str, Any]] = []
    download_errors: list[dict[str, str]] = []

    with tempfile.TemporaryDirectory(prefix="niakvio-upstream-parity-v3-") as tmp_name:
        tmp = Path(tmp_name)
        tasks = []
        for provider_id in provider_ids:
            upstream = upstreams[provider_id]
            try:
                data = parity.get_bytes(upstream["url"])
                path = tmp / f"{provider_id}.js"
                path.write_bytes(data)
            except Exception as exc:
                download_errors.append({
                    "providerId": provider_id,
                    "source": upstream["source"],
                    "error": str(exc)[:240],
                })
                continue
            tasks.append((provider_id, local[provider_id], upstream, path))

        with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, min(16, args.workers))) as pool:
            future_map = {
                pool.submit(
                    one_provider,
                    provider_id,
                    local_row,
                    upstream,
                    path,
                    timeout=max(5, args.timeout),
                    sample_count=sample_count,
                    seed=seed,
                ): provider_id
                for provider_id, local_row, upstream, path in tasks
            }
            for future in concurrent.futures.as_completed(future_map):
                provider_id = future_map[future]
                try:
                    rows.append(future.result())
                except Exception as exc:
                    rows.append({
                        "providerId": provider_id,
                        "status": "HARNESS_ERROR",
                        "error": f"{type(exc).__name__}: {exc}"[:240],
                        "lanes": [],
                    })

    rows.sort(key=lambda row: str(row.get("providerId") or ""))
    counts = Counter(str(row.get("status") or "UNKNOWN") for row in rows)
    regressions = [row["providerId"] for row in rows if row.get("status") == "REGRESSION"]
    resample = [row["providerId"] for row in rows if row.get("status") == "RESAMPLE"]
    payload = {
        "schemaVersion": 3,
        "method": "rotating-hub46-upstream-parity",
        "scopeProviderCount": len(scoped),
        "matchedUpstreamProviders": len(provider_ids),
        "testedProviders": len(rows),
        "samplesPerLane": sample_count,
        "seed": seed,
        "statusCounts": dict(sorted(counts.items())),
        "certainRegressions": regressions,
        "resampleProviders": resample,
        "missingUpstreamProviders": missing_upstream,
        "upstreamManifestErrors": source_errors,
        "providerDownloadErrors": download_errors,
        "providers": rows,
    }
    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = ROOT / out_path
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(
        "PROVIDER_UPSTREAM_PARITY_V3 "
        + " ".join(f"{key}={value}" for key, value in sorted(counts.items()))
    )
    print(
        "PROVIDER_UPSTREAM_PARITY_V3_COVERAGE "
        f"scope={len(scoped)} matched={len(provider_ids)} tested={len(rows)} "
        f"missing_upstream={len(missing_upstream)} downloads_failed={len(download_errors)} samples_per_lane={sample_count}"
    )
    print("PROVIDER_UPSTREAM_PARITY_V3_REGRESSIONS " + (",".join(regressions) if regressions else "none"))
    print("PROVIDER_UPSTREAM_PARITY_V3_RESAMPLE " + (",".join(resample) if resample else "none"))
    return 0 if rows else 2


if __name__ == "__main__":
    raise SystemExit(main())
