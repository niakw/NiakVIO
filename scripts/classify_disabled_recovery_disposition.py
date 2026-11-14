#!/usr/bin/env python3
"""Classify disabled-provider recovery evidence without granting publication authority."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def canon(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def load(path: Path) -> dict[str, Any]:
    value=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value,dict):
        raise ValueError(path)
    return value


def matching_health_rows(health: dict[str, Any], provider: str) -> list[dict[str, Any]]:
    rows=health.get("providers") or health.get("results") or []
    return [
        row for row in rows
        if isinstance(row,dict)
        and canon(row.get("provider") or row.get("canonical_id") or row.get("upstream_id") or row.get("id"))==provider
    ]


def declared_lanes(rows: list[dict[str, Any]]) -> set[str]:
    lanes:set[str]=set()
    for row in rows:
        profile=row.get("candidate_profile") if isinstance(row.get("candidate_profile"),dict) else {}
        raw=profile.get("required_fixture_categories") or []
        for value in raw:
            lane=canon(value)
            if lane:
                lanes.add(lane)
    return lanes


def identity_verified_lanes(rows: list[dict[str, Any]]) -> set[str]:
    lanes:set[str]=set()
    for row in rows:
        for test in row.get("tests") or []:
            if not isinstance(test,dict):
                continue
            fixture=test.get("fixture") if isinstance(test.get("fixture"),dict) else {}
            lane=canon(fixture.get("category") or fixture.get("mediaType"))
            if not lane:
                continue
            for host in test.get("host_results") or []:
                if not isinstance(host,dict):
                    continue
                if (
                    host.get("playback_verified") is True
                    and host.get("payload_verified") is True
                    and str(host.get("content_identity_status") or "")=="match"
                    and host.get("duration_identity_mismatch") is not True
                ):
                    lanes.add(lane)
                    break
    return lanes


def classify(
    health: dict[str, Any],
    guidance: dict[str, Any],
    provider: str,
    *,
    residential_transport_active: bool,
) -> dict[str, Any]:
    provider=canon(provider)
    rows=matching_health_rows(health,provider)
    if not rows:
        raise RuntimeError(f"{provider}: disabled recovery health row missing")
    guidance_rows=[
        row for row in guidance.get("rows") or []
        if isinstance(row,dict) and canon(row.get("providerId"))==provider
    ]
    if guidance.get("publicationAuthority") is not False or guidance.get("directMutationAuthority") is not False:
        raise RuntimeError("Brain guidance unexpectedly grants publication/direct mutation authority")

    statuses={str(row.get("status") or "").strip().casefold() for row in rows}
    if not guidance_rows and "runtime_error" in statuses:
        raise RuntimeError(f"Brain LLM abstained despite deterministic runtime error for {provider}")

    aggregate_healthy=any(status=="healthy" for status in statuses)
    declared=declared_lanes(rows)
    verified=identity_verified_lanes(rows)
    missing=sorted(declared-verified)
    terminal_identity_complete=bool(declared) and aggregate_healthy and not missing

    if guidance_rows:
        next_action="bounded_learning_repair"
    elif terminal_identity_complete:
        next_action="exact_playback_identity_replay"
    elif aggregate_healthy:
        next_action="identity_inconclusive_replay"
    else:
        next_action="transport_inconclusive_replay"

    return {
        "schemaVersion":2,
        "provider":provider,
        "brainGuidanceRows":len(guidance_rows),
        "brainAbstained":not bool(guidance_rows),
        "aggregateHealthHealthy":aggregate_healthy,
        "currentDisabledHealthHealthy":terminal_identity_complete,
        "declaredLanes":sorted(declared),
        "identityVerifiedLanes":sorted(verified & declared),
        "missingIdentityVerifiedLanes":missing,
        "observedStatuses":sorted(statuses),
        "residentialTransportActive":bool(residential_transport_active),
        "repairRequired":bool(guidance_rows),
        "publicationAuthority":False,
        "directMutationAuthority":False,
        "nextAction":next_action,
    }


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--health",type=Path,required=True)
    ap.add_argument("--guidance",type=Path,required=True)
    ap.add_argument("--provider",required=True)
    ap.add_argument("--residential-active",action="store_true")
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    result=classify(load(args.health),load(args.guidance),args.provider,residential_transport_active=args.residential_active)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(
        "FIELD_DISABLED_RECOVERY_DISPOSITION",
        f"provider={result['provider']}",
        f"aggregate_healthy={str(result['aggregateHealthHealthy']).lower()}",
        f"terminal_identity_complete={str(result['currentDisabledHealthHealthy']).lower()}",
        f"missing={','.join(result['missingIdentityVerifiedLanes']) or 'none'}",
        f"action={result['nextAction']}",
    )
    return 0


if __name__=="__main__":
    raise SystemExit(main())
