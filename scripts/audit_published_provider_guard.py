#!/usr/bin/env python3
"""Sanitized live regression guard for provider bytes currently published by manifest.json.

This deliberately does not materialize, repair or mutate providers. It executes the
exact provider assets referenced by the current public manifest and persists only
bounded verdict/count metadata. Debug fetch URLs, headers, bodies and signed player
values never enter the output.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BASE_PATH = ROOT / "scripts" / "audit_provider_quick_yield.py"
PROVIDER_ID = re.compile(r"^[a-z0-9][a-z0-9-]{0,95}$")
LANES = {"movie", "tv", "anime"}

spec = importlib.util.spec_from_file_location("published_quick_yield", BASE_PATH)
assert spec and spec.loader
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)


def cid(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def safe_provider(value: object) -> str:
    provider = cid(value)
    return provider if PROVIDER_ID.fullmatch(provider) else ""


def sanitize_row(row: dict[str, Any]) -> dict[str, Any]:
    provider = safe_provider(row.get("provider_id"))
    lane = cid(row.get("semantic_type"))
    if not provider or lane not in LANES:
        raise ValueError("invalid published-guard provider/lane")
    return {
        "provider": provider,
        "mediaType": lane,
        "status": str(row.get("status") or "unknown")[:48],
        "debugStage": str(row.get("debug_stage") or "unknown")[:64],
        "raw": max(0, min(int(row.get("raw") or 0), 999)),
        "playable": max(0, min(int(row.get("playable") or 0), 999)),
        "verified": max(0, min(int(row.get("verified") or 0), 999)),
        "contradictions": max(0, min(int(row.get("contradictions") or 0), 999)),
        "durationMs": max(0, min(int(row.get("duration_ms") or 0), 3_600_000)),
    }


def lane_ok(row: dict[str, Any]) -> bool:
    return (
        str(row.get("status") or "") == "playable_verified"
        and int(row.get("playable") or 0) > 0
        and int(row.get("verified") or 0) > 0
        and int(row.get("contradictions") or 0) == 0
    )


def build_summary(requested: list[str], rows: list[dict[str, Any]]) -> dict[str, Any]:
    clean = sorted((sanitize_row(row) for row in rows), key=lambda row: (row["provider"], row["mediaType"]))
    by_provider: dict[str, list[dict[str, Any]]] = {provider: [] for provider in requested}
    for row in clean:
        by_provider.setdefault(row["provider"], []).append(row)
    providers: dict[str, Any] = {}
    for provider in requested:
        provider_rows = by_provider.get(provider) or []
        providers[provider] = {
            "status": "verified" if provider_rows and all(lane_ok(row) for row in provider_rows) else "regression",
            "laneCount": len(provider_rows),
            "verifiedLaneCount": sum(1 for row in provider_rows if lane_ok(row)),
            "lanes": provider_rows,
        }
    summary = {
        "schemaVersion": 1,
        "mode": "published-provider-live-regression-guard",
        "providerCount": len(requested),
        "allRequestedLanesVerified": bool(requested) and all(value.get("status") == "verified" for value in providers.values()),
        "providers": providers,
        "publicationAllowed": False,
    }
    serialized = json.dumps(summary, ensure_ascii=False).casefold()
    for forbidden in ("http://", "https://", "authorization", "cookie", "bearer ", "x-api-key", "signedurl", "requestbody"):
        if forbidden in serialized:
            raise ValueError(f"published guard output contains forbidden secret/network material: {forbidden}")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", action="append", required=True)
    parser.add_argument("--media-type", action="append", choices=sorted(LANES), default=[])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    if not (str(os.environ.get("TMDB_API_KEY") or "").strip() or str(os.environ.get("TMDB_ACCESS_TOKEN") or "").strip()):
        raise SystemExit("TMDB_API_KEY or TMDB_ACCESS_TOKEN is required")

    requested: list[str] = []
    for value in args.provider:
        provider = safe_provider(value)
        if not provider:
            raise SystemExit(f"invalid provider id: {value!r}")
        if provider not in requested:
            requested.append(provider)

    tasks, _ = base.build_tasks()
    catalogue = {cid(task.get("provider_id")) for task in tasks}
    unknown = [provider for provider in requested if provider not in catalogue]
    if unknown:
        raise SystemExit("unknown or taskless providers: " + ",".join(unknown))
    wanted_lanes = {cid(value) for value in args.media_type if cid(value) in LANES}
    selected = [
        task for task in tasks
        if cid(task.get("provider_id")) in requested
        and (not wanted_lanes or cid(task.get("semantic_type")) in wanted_lanes)
    ]
    missing = [provider for provider in requested if not any(cid(task.get("provider_id")) == provider for task in selected)]
    if missing:
        raise SystemExit("requested providers have no selected semantic lane: " + ",".join(missing))

    rows = [base.run(task) for task in selected]
    summary = build_summary(requested, rows)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    for provider, value in summary["providers"].items():
        lane_text = ",".join(
            f"{row['mediaType']}:{row['status']}:{row['playable']}/{row['verified']}/{row['contradictions']}"
            for row in value["lanes"]
        )
        print(f"FIELD_PUBLISHED_PROVIDER_GUARD provider={provider} status={value['status']} lanes={lane_text or 'none'}")
    print(f"FIELD_PUBLISHED_PROVIDER_GUARD_RESULT ok={str(summary['allRequestedLanesVerified']).lower()}")
    return 0 if summary["allRequestedLanesVerified"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
