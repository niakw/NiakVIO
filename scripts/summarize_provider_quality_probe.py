#!/usr/bin/env python3
"""Sanitize current-provider quality Deep evidence; never publish raw network/media data."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

SHA = re.compile(r"^[0-9a-f]{40}$")
HEIGHTS = {240, 360, 480, 576, 720, 1080, 1440, 2160, 4320}
ALLOWED_STATUSES = {"healthy", "degraded", "no_streams", "blocked",
                    "unavailable", "provider_unreachable", "runtime_error", "reachable"}


def number(value: Any) -> int:
    if type(value) not in {str, int, float}:
        return 0
    try:
        parsed = int(value)
    except (ValueError, OverflowError, TypeError):
        return 0
    return max(0, min(parsed, 10000))


def maximum_heights(values: Any) -> int:
    if not isinstance(values, list):
        return 0
    return max([0] + [int(v) for v in values
                      if type(v) in (int, float) and int(v) in HEIGHTS])


def summarize(report: dict[str, Any], *, provider: str, sha: str) -> dict[str, Any]:
    if not SHA.fullmatch(sha):
        raise ValueError("exact source SHA required")
    if not re.fullmatch(r"[a-z0-9-]{2,64}", provider):
        raise ValueError("canonical provider ID required")
    if report.get("mode") != "deep":
        raise ValueError("only Deep quality evidence is valid")
    records = report.get("results")
    if not isinstance(records, list) or len(records) != 1:
        raise ValueError("expected exactly one filtered provider result")
    row = records[0]
    if not isinstance(row, dict) or row.get("canonical_id") != provider:
        raise ValueError("provider identity mismatch")
    tests = row.get("tests")
    if not isinstance(tests, list) or not tests or not all(isinstance(x, dict) for x in tests):
        raise ValueError("Deep fixture evidence missing")
    if not re.fullmatch(r"[0-9a-f]{64}", str(row.get("sha256") or "")):
        raise ValueError("executed provider byte digest missing")
    cleaned = []
    for case in tests:
        fixture = case.get("fixture") if isinstance(case.get("fixture"), dict) else {}
        cat = str(fixture.get("category") or fixture.get("mediaType") or "")
        if cat not in {"movie", "tv", "anime"}:
            raise ValueError("fixture media category is missing or invalid")
        announced = maximum_heights(case.get("announced_quality_heights"))
        returned = maximum_heights(case.get("returned_quality_heights"))
        verified = number(case.get("verified_max_height"))
        if verified not in HEIGHTS:
            verified = 0
        playable = number(case.get("streams_playable"))
        identity = number(case.get("identity_verified_streams"))
        returned_count = number(case.get("streams_returned"))
        probed = number(case.get("streams_probed"))
        candidates = number(case.get("announced_variant_candidates"))
        explored = number(case.get("explored_player_requests"))
        status = str(case.get("status") or "")
        status = status if status in ALLOWED_STATUSES else "unknown"
        cleaned.append({
            "category": cat,
            "status": status,
            "announcedMaxHeight": announced,
            "returnedMaxHeight": returned,
            "verifiedMaxHeight": verified,
            "announcedVariants": candidates,
            "exploredPlayers": explored,
            "streamsReturned": returned_count,
            "streamsProbed": probed,
            "playableStreams": playable,
            "identityMatchedPlayable": min(playable, identity),
            "fanoutCandidateLoss": bool(candidates > returned_count and explored >= 2),
            "advertisedQualityAboveReturned": bool(announced > returned),
            "declared4kButUnverified": bool(max(announced, returned) >= 2160
                                             and not (verified >= 2160 and playable > 0)),
            "identityVerified1080Plus": bool(verified >= 1080 and identity > 0 and playable > 0),
            "identityVerified4k": bool(verified >= 2160 and identity > 0 and playable > 0),
        })
    return {
        "schemaVersion": 1,
        "sourceSha": sha,
        "provider": provider,
        "providerSha256": row["sha256"],
        "mode": "deep",
        "status": str(row.get("status") or "unknown")[:36],
        "fixtureCount": len(cleaned),
        "fixtures": cleaned,
        "observedQualityGap": any(x["advertisedQualityAboveReturned"] for x in cleaned),
        "identityVerified1080Plus": any(x["identityVerified1080Plus"] for x in cleaned),
        "identityVerified4k": any(x["identityVerified4k"] for x in cleaned),
        "evidenceAuthority": "current-run-only",
        "sourceAndEpisodeIdentityRequired": True,
        "publicationAuthority": False,
        "mutationsAllowed": False,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--provider", required=True)
    ap.add_argument("--source-sha", required=True)
    args = ap.parse_args()
    result = summarize(json.loads(args.input.read_text(encoding="utf-8")),
                       provider=args.provider, sha=args.source_sha)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    totals = result["fixtures"]
    print("FIELD_PROVIDER_QUALITY_DEEP provider=" + result["provider"] +
          " tested=" + str(len(totals)) +
          " declared_4k_unverified=" + str(sum(x["declared4kButUnverified"] for x in totals)) +
          " identity_1080=" + str(sum(x["identityVerified1080Plus"] for x in totals)) +
          " identity_4k=" + str(sum(x["identityVerified4k"] for x in totals)) +
          " publication=false", flush=True)


if __name__ == "__main__":
    main()
