#!/usr/bin/env python3
"""Durable exact-source LKG for live-positive Provider route proof.

The route proof engine is intentionally allowed to produce different successful
request traces for the same immutable upstream Provider JS. A targeted retry must
not erase previously proven evidence merely because a semantic lane was not
successfully exercised by the upstream on this invocation.

This registry stores only sanitized proof-v5+ rows that belonged to a task which
returned at least one upstream stream. Evidence is reusable only while the exact
Provider source identity (kind/source id/current SHA/provider URL) is unchanged.
A source change resets that provider's route evidence.

Fresh-positive semantic lanes are authoritative for active reconstruction. Older
same-source LKG rows may fill only semantic lanes that did not produce a fresh
positive task in the current targeted run. This prevents an obsolete correlated
step from being reintroduced into a current successful request chain while still
preserving historical proof memory for transiently unproven lanes.

The registry is proof memory, not publication authority: normal reconstruction,
identity/content guards, targeted yield gates and the full 96-provider gate still
run on every candidate.
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = ROOT / "automation" / "provider-route-proof-lkg.json"
DEFAULT_REPORT = ROOT / "automation" / "provider-repair-fast-targeted.json"
SCHEMA_VERSION = 1
PROOF_MIN_VERSION = 5
SEMANTIC_TYPES = {"movie", "tv", "anime"}


def cid(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def load(path: Path, *, missing_ok: bool = False) -> dict[str, Any]:
    if missing_ok and not path.exists():
        return {"schemaVersion": SCHEMA_VERSION, "providers": {}}
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(path)
    return value


def write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def source_identity(source: object) -> tuple[str, str, str, str] | None:
    if not isinstance(source, dict):
        return None
    kind = str(source.get("kind") or "").strip().casefold()
    source_id = cid(source.get("sourceId") or source.get("id"))
    current = str(source.get("currentSha256") or source.get("sha256") or "").strip().casefold()
    wanted = str(source.get("wantedSha256") or current).strip().casefold()
    provider_url = str(source.get("providerUrl") or source.get("url") or "").strip()
    if not kind or not source_id or not current:
        return None
    if wanted and current != wanted:
        return None
    if provider_url:
        try:
            parsed = urlparse(provider_url)
            if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                return None
        except Exception:
            return None
    return kind, source_id, current, provider_url


def _positive_route_row(row: object, provider_source: tuple[str, str, str, str]) -> bool:
    if not isinstance(row, dict):
        return False
    if int(row.get("proofModelVersion") or 0) < PROOF_MIN_VERSION:
        return False
    if row.get("requestSpecReusable") is not True:
        return False
    status = int(row.get("status") or 0)
    if status < 200 or status >= 400:
        return False
    semantic = str(row.get("semanticType") or "").strip().casefold()
    if semantic not in SEMANTIC_TYPES:
        return False
    if int(row.get("taskStreamCount") or 0) <= 0 and int(row.get("taskRawStreamCount") or 0) <= 0:
        return False
    route = str(row.get("route") or "").strip()
    origin = str(row.get("origin") or "").strip()
    if not route or not origin:
        return False
    try:
        parsed = urlparse(origin)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            return False
    except Exception:
        return False
    row_source = source_identity(row.get("source"))
    if row_source != provider_source:
        return False
    low = route.casefold()
    if ("{id}" in low or "{slug}" in low) and row.get("providerValueCorrelation") is not True:
        return False
    return True


def _row_fingerprint(row: dict[str, Any]) -> str:
    material = {
        "route": row.get("route"),
        "origin": row.get("origin"),
        "role": row.get("role"),
        "method": row.get("method"),
        "semanticType": row.get("semanticType"),
        "fixture": row.get("fixture"),
        "providerValueCorrelation": row.get("providerValueCorrelation"),
        "externalIdentityCorrelation": row.get("externalIdentityCorrelation"),
        "requestSpec": row.get("requestSpec"),
    }
    return json.dumps(material, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _dedupe_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in rows:
        fp = _row_fingerprint(row)
        if fp in seen:
            continue
        seen.add(fp)
        out.append(copy.deepcopy(row))
    return out


def positive_rows(provider_row: dict[str, Any]) -> list[dict[str, Any]]:
    identity = source_identity(provider_row.get("source"))
    if identity is None:
        return []
    rows = [copy.deepcopy(row) for row in provider_row.get("routeData") or [] if _positive_route_row(row, identity)]
    return _dedupe_rows(rows)


def fresh_positive_lanes(provider_row: dict[str, Any]) -> set[str]:
    """Return semantic lanes that produced streams in this exact targeted run.

    Prefer task-level evidence because a successful provider may return a stream
    after HTTP calls that are not themselves reusable route rows. Fall back to
    routeData task counters for report variants that omit tasks.
    """
    lanes: set[str] = set()
    for task in provider_row.get("tasks") or []:
        if not isinstance(task, dict):
            continue
        semantic = str(task.get("semanticType") or task.get("semantic_type") or "").strip().casefold()
        if semantic not in SEMANTIC_TYPES:
            continue
        if int(task.get("streamCount") or task.get("stream_count") or 0) > 0 or int(task.get("rawStreamCount") or task.get("raw_stream_count") or 0) > 0:
            lanes.add(semantic)
    for row in provider_row.get("routeData") or []:
        if not isinstance(row, dict):
            continue
        semantic = str(row.get("semanticType") or "").strip().casefold()
        if semantic not in SEMANTIC_TYPES:
            continue
        if int(row.get("taskStreamCount") or 0) > 0 or int(row.get("taskRawStreamCount") or 0) > 0:
            lanes.add(semantic)
    return lanes


def normalize_registry(value: dict[str, Any]) -> dict[str, Any]:
    providers = value.get("providers") if isinstance(value.get("providers"), dict) else {}
    return {
        "schemaVersion": SCHEMA_VERSION,
        "policy": "exact-source live-positive route proof LKG; fresh-positive lanes are authoritative for active reconstruction, LKG fills only currently unproven lanes, source changes reset provider evidence",
        "providers": {
            cid(key): copy.deepcopy(row)
            for key, row in sorted(providers.items())
            if cid(key) and isinstance(row, dict)
        },
    }


def merge_report_into_registry(registry: dict[str, Any], report: dict[str, Any]) -> tuple[dict[str, Any], dict[str, int]]:
    out = normalize_registry(registry)
    providers = out["providers"]
    updated = reset = retained = 0
    for current in report.get("providers") or []:
        if not isinstance(current, dict):
            continue
        provider = cid(current.get("providerId") or current.get("id") or current.get("provider"))
        identity = source_identity(current.get("source"))
        current_rows = positive_rows(current)
        if not provider or identity is None or not current_rows:
            continue
        previous = providers.get(provider) if isinstance(providers.get(provider), dict) else None
        previous_identity = source_identity(previous.get("source")) if previous else None
        if previous and previous_identity == identity:
            previous_rows = [row for row in previous.get("routeData") or [] if isinstance(row, dict)]
            rows = _dedupe_rows([*current_rows, *previous_rows])
            retained += max(0, len(rows) - len(current_rows))
        else:
            rows = _dedupe_rows(current_rows)
            if previous:
                reset += 1
        routes = list(dict.fromkeys(str(row.get("route") or "").strip() for row in rows if str(row.get("route") or "").strip()))
        providers[provider] = {
            "source": copy.deepcopy(current.get("source")),
            "routeData": rows,
            "routes": routes,
        }
        updated += 1
    out["providers"] = dict(sorted(providers.items()))
    return out, {"updatedProviders": updated, "sourceResets": reset, "retainedRows": retained}


def augment_provider_row(current: dict[str, Any], registry_entry: object) -> tuple[dict[str, Any], int]:
    out = copy.deepcopy(current)
    if not isinstance(registry_entry, dict):
        return out, 0
    current_identity = source_identity(out.get("source"))
    registry_identity = source_identity(registry_entry.get("source"))
    if current_identity is None or registry_identity != current_identity:
        return out, 0
    current_rows = [copy.deepcopy(row) for row in out.get("routeData") or [] if isinstance(row, dict)]
    positive_lanes = fresh_positive_lanes(out)
    lkg_rows = [
        copy.deepcopy(row)
        for row in registry_entry.get("routeData") or []
        if isinstance(row, dict)
        and str(row.get("semanticType") or "").strip().casefold() not in positive_lanes
    ]
    merged_rows = _dedupe_rows([*current_rows, *lkg_rows])
    retained = max(0, len(merged_rows) - len(_dedupe_rows(current_rows)))
    if retained <= 0:
        return out, 0
    out["routeData"] = merged_rows
    current_routes = [str(route).strip() for route in out.get("routes") or [] if str(route).strip()]
    retained_routes = [str(row.get("route") or "").strip() for row in lkg_rows if str(row.get("route") or "").strip()]
    out["routes"] = list(dict.fromkeys([*current_routes, *retained_routes]))
    out["routeCount"] = len(out["routes"])
    out["routeProofLkgRetainedRows"] = retained
    out["routeProofFreshPositiveLanes"] = sorted(positive_lanes)
    return out, retained


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT.relative_to(ROOT))
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY.relative_to(ROOT))
    args = parser.parse_args()
    report_path = args.report if args.report.is_absolute() else ROOT / args.report
    registry_path = args.registry if args.registry.is_absolute() else ROOT / args.registry
    report = load(report_path)
    registry = load(registry_path, missing_ok=True)
    merged, stats = merge_report_into_registry(registry, report)
    write(registry_path, merged)
    print(
        "PROVIDER_ROUTE_PROOF_LKG_OK "
        f"updated={stats['updatedProviders']} source_resets={stats['sourceResets']} "
        f"retained_rows={stats['retainedRows']} providers={len(merged['providers'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
