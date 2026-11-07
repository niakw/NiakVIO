#!/usr/bin/env python3
"""Fail closed when a requested representative FORCE never selects its profile.

This proves plan selection only, NOT provider mutation or media playback.
"""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path
from typing import Any


def verify(report: dict[str, Any], *, provider: str, profile: str, run_id: str = "", source_sha: str = "") -> int:
    provider = provider.strip().casefold().replace("_", "-")
    profile = profile.strip().casefold()
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", provider):
        raise ValueError("invalid representative provider")
    if not re.fullmatch(r"[a-z][a-z0-9_]*_v[0-9]+", profile):
        raise ValueError("invalid preferred FORCE strategy")
    if report.get("schemaVersion") != 1:
        raise ValueError("invalid Brain report schema")
    # A persistent "latest" report from an older FORCE against the same
    # provider/profile is not evidence of this run. Bind provenance to the
    # workflow's own immutable run id and source commit when provided.
    if run_id:
        if not re.fullmatch(r"[0-9]{8,20}", run_id):
            raise ValueError("invalid GitHub FORCE run identifier")
        expected = run_id + "-pre-repair"
        if report.get("sourceCensusRunId") != expected or (
            (report.get("experienceMemory") or {}).get("sourceRunId") != expected
        ):
            raise ValueError("stale Brain report: source run does not match requested FORCE")
    if source_sha:
        if not re.fullmatch(r"[a-f0-9]{40}", source_sha):
            raise ValueError("invalid FORCE source SHA")
        if (report.get("experienceMemory") or {}).get("sourceSha") != source_sha:
            raise ValueError("stale Brain report: tested source SHA differs")
    processed = [
        str(value).strip().casefold().replace("_", "-")
        for value in report.get("processedProviders") or []
    ]
    if processed != [provider]:
        raise ValueError("report is not the exact isolated representative")
    matched = 0
    examined = 0
    for wave in report.get("waves") or []:
        if not isinstance(wave, dict):
            continue
        for batch in wave.get("batches") or []:
            if not isinstance(batch, dict):
                continue
            plans = (batch.get("brain") or {}).get("plans") or {}
            if not isinstance(plans, dict):
                continue
            for plan in plans.values():
                if not isinstance(plan, dict):
                    continue
                if str(plan.get("providerId") or "").casefold().replace("_", "-") != provider:
                    continue
                examined += 1
                if (
                    plan.get("forcePreferredSelected") is True
                    and plan.get("postExhaustionStrategyProfile") == profile
                    and plan.get("allowedProfiles") == [profile]
                    and plan.get("action") == "probe-targeted-repair"
                ):
                    matched += 1
    if not matched:
        raise ValueError(
            f"requested FORCE strategy not selected for {provider}: "
            f"profile={profile} examined={examined}"
        )
    return matched


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--provider", required=True)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--run-id", default="")
    parser.add_argument("--source-sha", default="")
    args = parser.parse_args()
    try:
        report = json.loads(args.report.read_text(encoding="utf-8"))
        matched = verify(report, provider=args.provider, profile=args.profile, run_id=args.run_id, source_sha=args.source_sha)
    except (OSError, UnicodeError, ValueError, TypeError):
        print("FIELD_BRAIN_FORCE_REPRESENTATIVE_SELECTION verified=false")
        return 2
    print(f"FIELD_BRAIN_FORCE_REPRESENTATIVE_SELECTION verified=true matched_plans={matched} "
          "terminal_media_proof=false publication_authority=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
