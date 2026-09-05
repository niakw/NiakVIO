#!/usr/bin/env python3
"""Fail publication unless every active manifest provider is live-qualified.

An active provider cannot be compensated by a disabled provider. A provider proven
blocked/unreachable may be advanced by the sequential discovery loop for audit
purposes, but it does not satisfy publication while it remains enabled=true.
Qualification means 100% of the provider's declared semantic types have live route
proof (or verified direct output per declared type); internal request-shape coverage
is not a publication criterion.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "manifest.json"
DEFAULT_REPORT = ROOT / "provider-v3-live-route-validation.json"


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: object required")
    return value


def cid(value: object) -> str:
    return str(value or "").strip().casefold()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    manifest = load(args.manifest.resolve())
    report = load(args.report.resolve())
    rows = [row for row in manifest.get("scrapers") or [] if isinstance(row, dict)]
    active = {cid(row.get("id")) for row in rows if row.get("enabled") is not False and cid(row.get("id"))}
    reports = {
        cid(row.get("providerId")): row
        for row in report.get("providers") or []
        if isinstance(row, dict) and cid(row.get("providerId"))
    }

    qualified: set[str] = set()
    failures: list[str] = []
    for provider_id in sorted(active):
        row = reports.get(provider_id)
        if not isinstance(row, dict):
            failures.append(f"{provider_id}: active provider has no sequential live report")
            continue
        state = str(row.get("completionState") or "").strip()
        live_routes = int(row.get("liveValidatedRouteCount") or 0)
        playable = bool(row.get("playableVerified"))
        type_coverage = float(row.get("declaredTypeCoverageRatio") or row.get("effectiveCoverageRatio") or 0.0)
        type_complete = row.get("typeComplete") is True
        required_types = [cid(value) for value in row.get("requiredTypes") or [] if cid(value)]
        validated_types = [cid(value) for value in row.get("validatedTypes") or [] if cid(value)]
        missing_types = [cid(value) for value in row.get("missingTypes") or [] if cid(value)]
        advanced = row.get("advancedToNextProvider") is True

        route_qualified = (
            state == "declared-types-qualified"
            and type_complete
            and type_coverage >= 1.0
            and not missing_types
            and live_routes > 0
        )
        direct_qualified = (
            state == "direct-output-verified"
            and type_complete
            and type_coverage >= 1.0
            and not missing_types
            and playable
        )
        if advanced and (route_qualified or direct_qualified):
            qualified.add(provider_id)
            continue
        failures.append(
            f"{provider_id}: active but not declared-type live-qualified "
            f"state={state or 'missing'} liveRoutes={live_routes} "
            f"types={','.join(validated_types) or 'none'}/{','.join(required_types) or 'none'} "
            f"missing={','.join(missing_types) or 'none'} coverage={type_coverage:.3f}/1.000 playable={playable}"
        )

    print(
        "FIELD_ACTIVE_PROVIDER_LIVE_COVERAGE "
        f"catalogue={len(rows)} active={len(active)} qualified={len(qualified)} "
        f"missing={len(active - qualified)} declared_type_gate=1.000"
    )
    if failures:
        raise AssertionError(
            "active provider declared-type live coverage gate failed: "
            f"qualified={len(qualified)}/{len(active)}\n" + "\n".join(failures)
        )
    if len(qualified) != len(active):
        raise AssertionError(f"active provider coverage mismatch: {len(qualified)}/{len(active)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
