#!/usr/bin/env python3
"""Validate a disabled-provider recovery result before lifecycle reactivation.

This script grants no publication authority by itself.  It turns exact recovery
artifacts into a fail-closed reactivation approval only when the currently
disabled bytes are unchanged and every required media lane has at least one
playable, payload-verified, identity-matched stream with no contradiction.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def canon(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(path)
    return value


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def candidate_for(stage: dict[str, Any], provider: str) -> dict[str, Any]:
    rows = [
        row for row in stage.get("candidates") or []
        if isinstance(row, dict) and canon(row.get("canonical_id") or row.get("upstream_id")) == provider
    ]
    if len(rows) != 1:
        raise ValueError(f"{provider}: expected exactly one recovery-stage candidate, got {len(rows)}")
    return rows[0]


def health_for(health: dict[str, Any], provider: str) -> dict[str, Any]:
    rows = [
        row for row in health.get("results") or []
        if isinstance(row, dict) and canon(row.get("canonical_id") or row.get("upstream_id")) == provider
    ]
    if len(rows) != 1:
        raise ValueError(f"{provider}: expected exactly one health result, got {len(rows)}")
    return rows[0]


def required_lanes(result: dict[str, Any]) -> set[str]:
    profile = result.get("candidate_profile") if isinstance(result.get("candidate_profile"), dict) else {}
    evidence = result.get("evidence") if isinstance(result.get("evidence"), dict) else {}
    values = (
        evidence.get("required_fixture_categories")
        or profile.get("required_fixture_categories")
        or profile.get("supported_types")
        or []
    )
    return {str(value).strip().lower() for value in values if str(value).strip()}


def identity_verified_lanes(result: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    proven: dict[str, list[dict[str, Any]]] = {}
    for test in result.get("tests") or []:
        if not isinstance(test, dict):
            continue
        fixture = test.get("fixture") if isinstance(test.get("fixture"), dict) else {}
        lane = str(fixture.get("category") or fixture.get("mediaType") or "").strip().lower()
        if not lane:
            continue
        verified_hosts = []
        for host in test.get("host_results") or []:
            if not isinstance(host, dict):
                continue
            if (
                host.get("playback_verified") is True
                and host.get("payload_verified") is True
                and str(host.get("content_identity_status") or "") == "match"
                and host.get("duration_identity_mismatch") is not True
            ):
                verified_hosts.append({
                    "host": host.get("host"),
                    "kind": host.get("kind"),
                    "reason": host.get("content_identity_reason"),
                })
        if verified_hosts:
            proven.setdefault(lane, []).append({
                "fixture": fixture.get("label") or fixture.get("title") or fixture.get("tmdbId"),
                "tmdbId": str(fixture.get("tmdbId") or ""),
                "hosts": verified_hosts,
            })
    return proven


def validate(
    *,
    provider: str,
    stage: dict[str, Any],
    health: dict[str, Any],
    disposition: dict[str, Any],
    current_asset: Path,
) -> dict[str, Any]:
    provider = canon(provider)
    candidate = candidate_for(stage, provider)
    result = health_for(health, provider)

    stage_sha = str(candidate.get("sha256") or "").strip().casefold()
    health_sha = str(result.get("sha256") or "").strip().casefold()
    current_sha = digest(current_asset)
    if len(stage_sha) != 64 or stage_sha != health_sha or stage_sha != current_sha:
        raise ValueError(
            f"{provider}: exact-byte proof mismatch stage={stage_sha} health={health_sha} current={current_sha}"
        )

    metadata = candidate.get("metadata") if isinstance(candidate.get("metadata"), dict) else {}
    if metadata.get("enabled") is not False:
        raise ValueError(f"{provider}: recovery candidate is not disabled")
    if candidate.get("disabled_recovery_exact_bytes") is not True:
        raise ValueError(f"{provider}: stage is not exact disabled-byte recovery")
    if candidate.get("publication_allowed") is not False:
        raise ValueError(f"{provider}: recovery stage unexpectedly had publication authority")

    if canon(disposition.get("provider")) != provider:
        raise ValueError(f"{provider}: Brain disposition provider mismatch")
    if disposition.get("brainAbstained") is not True:
        raise ValueError(f"{provider}: no-repair reactivation requires explicit Brain abstention")
    if disposition.get("currentDisabledHealthHealthy") is not True:
        raise ValueError(f"{provider}: Brain did not classify current disabled bytes healthy")
    if disposition.get("repairRequired") is not False:
        raise ValueError(f"{provider}: Brain still requires repair")
    if disposition.get("nextAction") != "exact_playback_identity_replay":
        raise ValueError(f"{provider}: unsupported Brain nextAction={disposition.get('nextAction')!r}")
    if disposition.get("publicationAuthority") is not False or disposition.get("directMutationAuthority") is not False:
        raise ValueError(f"{provider}: recovery lab authority contract was violated")

    evidence = result.get("evidence") if isinstance(result.get("evidence"), dict) else {}
    if result.get("status") != "healthy" or result.get("ci_classification") != "conclusive_success":
        raise ValueError(f"{provider}: current disabled health is not conclusive healthy")
    for field in (
        "identity_contradiction_count",
        "duration_identity_mismatch_count",
        "playable_identity_contradiction_count",
        "playable_duration_identity_mismatch_count",
        "disallowed_streams",
    ):
        if int(evidence.get(field) or 0) != 0:
            raise ValueError(f"{provider}: health evidence has {field}={evidence.get(field)!r}")

    required = required_lanes(result)
    if not required:
        raise ValueError(f"{provider}: no required media lanes in recovery evidence")
    verified = identity_verified_lanes(result)
    missing = sorted(required - set(verified))
    if missing:
        raise ValueError(f"{provider}: missing identity-verified playable proof for lanes {missing}")

    return {
        "schemaVersion": 1,
        "authority": "disabled-provider-reactivation-proof-v1",
        "provider": provider,
        "providerSha256": current_sha,
        "requiredLanes": sorted(required),
        "identityVerifiedLanes": sorted(verified),
        "laneEvidence": verified,
        "brainDisposition": {
            "brainAbstained": True,
            "repairRequired": False,
            "nextAction": "exact_playback_identity_replay",
        },
        "health": {
            "status": result.get("status"),
            "ciClassification": result.get("ci_classification"),
            "streamsPlayable": int(evidence.get("streams_playable") or 0),
            "payloadVerifiedStreams": int(evidence.get("payload_verified_streams") or 0),
            "identityVerifiedStreams": int(evidence.get("identity_verified_streams") or 0),
        },
        "reactivationEligible": True,
        "publicationAuthority": False,
        "nextAction": "provider-lifecycle-reactivation",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--provider", required=True)
    ap.add_argument("--stage", type=Path, required=True)
    ap.add_argument("--health", type=Path, required=True)
    ap.add_argument("--disposition", type=Path, required=True)
    ap.add_argument("--current-asset", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    approval = validate(
        provider=args.provider,
        stage=load(args.stage),
        health=load(args.health),
        disposition=load(args.disposition),
        current_asset=args.current_asset,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(approval, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        "DISABLED_PROVIDER_REACTIVATION_PROOF_OK",
        f"provider={approval['provider']}",
        f"lanes={','.join(approval['identityVerifiedLanes'])}",
        f"sha256={approval['providerSha256']}",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
