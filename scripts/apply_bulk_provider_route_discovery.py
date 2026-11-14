#!/usr/bin/env python3
"""Merge sanitized bulk route-discovery shards into the next activation wave."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REQUEST = ROOT / ".github/provider-onboarding/batch.json"
DEFAULT_EVIDENCE = ROOT / "automation/provider-bulk-route-discovery-latest.json"


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def norm(value: Any) -> str:
    return re.sub(r"[^a-z0-9._-]+", "-", str(value or "").strip().casefold()).strip("-")


def write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def current_active_counts() -> tuple[int, int]:
    global_manifest = load(ROOT / "manifest.json")
    france_manifest = load(ROOT / "vf/manifest.json")
    g = sum(1 for row in global_manifest.get("scrapers") or [] if isinstance(row, dict) and row.get("enabled") is not False)
    f = sum(1 for row in france_manifest.get("scrapers") or [] if isinstance(row, dict) and row.get("enabled") is not False)
    return g, f


def source_rows(request: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for section in ("providers", "deferredProviders"):
        for row in request.get(section) or []:
            if not isinstance(row, dict):
                continue
            pid = norm(row.get("id") or row.get("provider"))
            if not pid or pid in seen:
                continue
            seen.add(pid)
            out.append(dict(row))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("shards", nargs="+", type=Path)
    ap.add_argument("--request", type=Path, default=DEFAULT_REQUEST)
    ap.add_argument("--evidence", type=Path, default=DEFAULT_EVIDENCE)
    ap.add_argument("--output-request", type=Path, default=DEFAULT_REQUEST)
    args = ap.parse_args()

    request = load(args.request)
    if not isinstance(request, dict):
        raise SystemExit("bulk route discovery request must be an object")
    version = request.get("requestVersion")
    rows = source_rows(request)
    by_id = {norm(row.get("id") or row.get("provider")): row for row in rows}

    merged: dict[str, dict[str, Any]] = {}
    transports: set[str] = set()
    for path in args.shards:
        payload = load(path)
        if payload.get("requestVersion") != version:
            raise SystemExit(f"route discovery shard requestVersion mismatch: {path}")
        transports.add(str(payload.get("transport") or "unknown"))
        for result in payload.get("providers") or []:
            if not isinstance(result, dict):
                continue
            pid = norm(result.get("provider"))
            if not pid or pid not in by_id:
                continue
            if pid in merged:
                raise SystemExit(f"duplicate route-discovery provider result: {pid}")
            merged[pid] = result

    qualified: list[dict[str, Any]] = []
    deferred: list[dict[str, Any]] = []
    evidence_rows: list[dict[str, Any]] = []
    for row in rows:
        pid = norm(row.get("id") or row.get("provider"))
        result = merged.get(pid)
        if result is None:
            # Active rows are intentionally omitted by the probe; do not put them
            # back into an onboarding wave.
            continue
        patterns = [
            str(value).strip()
            for value in result.get("routePatterns") or []
            if str(value).strip()
        ]
        patterns = list(dict.fromkeys(patterns))[:24]
        evidence_rows.append(result)
        if result.get("qualified") is True and patterns:
            updated = dict(row)
            updated["routes"] = patterns
            updated["routeDiscoveryEvidence"] = {
                "transport": result.get("transport"),
                "reason": result.get("reason"),
                "routeCount": len(patterns),
            }
            qualified.append(updated)
        else:
            deferred_row = dict(row)
            deferred_row["routeDiscoveryLastReason"] = str(result.get("reason") or "unqualified")
            deferred.append(deferred_row)

    global_add = sum(1 for row in qualified if str(row.get("scope") or "global").casefold() == "global")
    france_add = sum(1 for row in qualified if str(row.get("scope") or "global").casefold() == "france")
    current_global, current_france = current_active_counts()

    evidence = {
        "schemaVersion": 1,
        "requestVersion": version,
        "source": request.get("source"),
        "transportProfiles": sorted(transports),
        "candidateCount": len(evidence_rows),
        "qualifiedCount": len(qualified),
        "deferredCount": len(deferred),
        "qualifiedScopes": {"global": global_add, "france": france_add},
        "currentActiveBeforeWave": {"global": current_global, "france": current_france},
        "providers": evidence_rows,
    }
    write(args.evidence, evidence)

    if not qualified:
        print(
            f"PROVIDER_BULK_ROUTE_DISCOVERY_MERGE qualified=0 deferred={len(deferred)} "
            f"requestVersion={version}; batch_not_changed=true"
        )
        return 0

    next_request = dict(request)
    next_request["requestVersion"] = int(version or 0) + 1
    next_request["providers"] = qualified
    next_request["deferredProviders"] = deferred
    next_request["targetActive"] = {
        "global": current_global + global_add,
        "france": current_france + france_add,
    }
    next_request["routeDiscoveryWave"] = {
        "sourceRequestVersion": version,
        "qualified": len(qualified),
        "deferred": len(deferred),
        "transports": sorted(transports),
        "activationRequiresExecutablePlan": True,
    }
    write(args.output_request, next_request)
    print(
        f"PROVIDER_BULK_ROUTE_DISCOVERY_MERGE qualified={len(qualified)} deferred={len(deferred)} "
        f"global_target={next_request['targetActive']['global']} "
        f"france_target={next_request['targetActive']['france']} "
        f"next_request_version={next_request['requestVersion']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
