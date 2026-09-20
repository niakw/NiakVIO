#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def norm(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def safe_text(value: object, limit: int = 220) -> str:
    text = str(value or "")
    text = re.sub(r"https?://\S+", "<url>", text)
    text = re.sub(
        r"(?i)(token|authorization|cookie|secret|password|api[_-]?key)\s*[:=]\s*\S+",
        r"\1=<redacted>",
        text,
    )
    return " ".join(text.split())[:limit]


def error_fingerprint(row: dict[str, Any]) -> tuple[str, str, str]:
    candidates: list[dict[str, Any]] = []
    details = row.get("error_details")
    if isinstance(details, dict):
        candidates.append(details)
    for test in row.get("tests") or []:
        if isinstance(test, dict) and isinstance(test.get("error_details"), dict):
            candidates.append(test["error_details"])
    if not candidates:
        return ("", "", "")
    first = candidates[0]
    return (
        safe_text(first.get("name"), 100),
        safe_text(first.get("code"), 100),
        safe_text(first.get("message"), 220),
    )


def validate(
    catalog: dict[str, Any],
    stage: dict[str, Any],
    health: dict[str, Any],
    *,
    collapse_ratio: float = 0.90,
    minimum_scope: int = 5,
) -> dict[str, Any]:
    current = {
        norm(row.get("canonicalId"))
        for row in catalog.get("providers") or []
        if isinstance(row, dict) and norm(row.get("canonicalId"))
    }
    if not current:
        raise ValueError("provider catalog contains no current providers")

    candidate_by_key: dict[str, str] = {}
    for row in stage.get("candidates") or []:
        if not isinstance(row, dict):
            continue
        key = str(row.get("key") or "").strip()
        provider = norm(row.get("canonical_id") or row.get("upstream_id"))
        if key and provider:
            candidate_by_key[key] = provider

    current_rows: list[tuple[str, dict[str, Any]]] = []
    for row in health.get("results") or []:
        if not isinstance(row, dict):
            continue
        provider = candidate_by_key.get(str(row.get("key") or "").strip())
        if provider in current:
            current_rows.append((provider, row))

    observed = {provider for provider, _row in current_rows}
    missing = sorted(current - observed)
    status_counts = Counter(str(row.get("status") or "unknown") for _provider, row in current_rows)
    runtime_rows = [(provider, row) for provider, row in current_rows if str(row.get("status") or "") == "runtime_error"]
    runtime_providers = {provider for provider, _row in runtime_rows}
    ratio = len(runtime_providers) / max(1, len(observed))

    fingerprints = Counter(
        error_fingerprint(row)
        for _provider, row in runtime_rows
        if any(error_fingerprint(row))
    )
    dominant_error, dominant_count = (fingerprints.most_common(1)[0] if fingerprints else (("", "", ""), 0))
    catastrophic = (
        len(observed) >= max(1, int(minimum_scope))
        and ratio >= float(collapse_ratio)
        and len(runtime_providers) >= max(1, int(minimum_scope))
    )

    return {
        "schemaVersion": 1,
        "target": "learning_common_runtime_baseline",
        "currentProviderCount": len(current),
        "observedCurrentProviderCount": len(observed),
        "missingCurrentProviders": missing,
        "statusCounts": dict(sorted(status_counts.items())),
        "runtimeErrorProviderCount": len(runtime_providers),
        "runtimeErrorRatio": round(ratio, 6),
        "collapseRatio": float(collapse_ratio),
        "minimumScope": int(minimum_scope),
        "catastrophicCommonRuntimeCollapse": catastrophic,
        "dominantRuntimeError": {
            "name": dominant_error[0],
            "code": dominant_error[1],
            "message": dominant_error[2],
            "providerCount": dominant_count,
        },
        "runtimeErrorProviders": sorted(runtime_providers),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--stage", type=Path, required=True)
    parser.add_argument("--health", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--collapse-ratio", type=float, default=0.90)
    parser.add_argument("--minimum-scope", type=int, default=5)
    args = parser.parse_args()

    summary = validate(
        load(args.catalog),
        load(args.stage),
        load(args.health),
        collapse_ratio=args.collapse_ratio,
        minimum_scope=args.minimum_scope,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    dominant = summary["dominantRuntimeError"]
    print(
        "FIELD_LEARNING_RUNTIME_BASELINE "
        f"observed={summary['observedCurrentProviderCount']} "
        f"runtime_errors={summary['runtimeErrorProviderCount']} "
        f"ratio={summary['runtimeErrorRatio']:.6f} "
        f"catastrophic={str(summary['catastrophicCommonRuntimeCollapse']).lower()} "
        f"dominant={dominant['name'] or 'none'} "
        f"dominant_count={dominant['providerCount']}"
    )
    if summary["catastrophicCommonRuntimeCollapse"]:
        detail = dominant["message"] or dominant["code"] or dominant["name"] or "unknown shared runtime error"
        raise SystemExit(
            "Learning common runtime baseline collapsed; provider-specific learning is invalid until Core/stage is fixed: "
            + detail
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
