#!/usr/bin/env python3
"""Run the existing Quick Brain in daily learning mode with cross-day negative memory.

The production repair engine is not forked. This wrapper only suppresses a
provider/signature/profile combination after repeated sandbox failures recorded
by the previous sanitized learning state. Production publication remains outside
this process.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import run_adaptive_quick_repair as quick  # noqa: E402


def _load_state() -> dict[str, Any]:
    raw = str(os.environ.get("NUVIO_BRAIN_LEARNING_STATE") or "").strip()
    if not raw:
        return {}
    path = Path(raw).resolve()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _negative_entries(state: dict[str, Any]) -> list[dict[str, Any]]:
    memory = state.get("experimentMemory") if isinstance(state.get("experimentMemory"), dict) else {}
    rows = memory.get("entries") if isinstance(memory.get("entries"), list) else []
    return [row for row in rows if isinstance(row, dict)]


def _norm(value: Any) -> str:
    return str(value or "").strip().casefold()


def _version(candidate: dict[str, Any]) -> str:
    metadata = candidate.get("metadata") if isinstance(candidate.get("metadata"), dict) else {}
    return str(metadata.get("version") or candidate.get("version") or "*").strip() or "*"


def _matches(row: dict[str, Any], *, provider_id: str, provider_version: str, signature: str, profile: str) -> bool:
    row_provider = _norm(row.get("providerId"))
    if row_provider != provider_id:
        return False
    row_version = str(row.get("providerVersion") or "*").strip() or "*"
    if row_version not in {"*", provider_version}:
        return False
    if str(row.get("signature") or "") != signature:
        return False
    if str(row.get("profile") or "") != profile:
        return False
    return int(row.get("successes") or 0) == 0


def main() -> int:
    state = _load_state()
    negative = _negative_entries(state)
    policy = quick.brain.policy()
    lab = policy.get("learningLab") if isinstance(policy.get("learningLab"), dict) else {}
    threshold = max(1, int(lab.get("maxRepeatedFailedProfile") or 2))
    original = quick._brain_matching_profiles

    def learning_matching(candidate: dict[str, Any], result: dict[str, Any], source_text: str, config: dict[str, Any] | None = None) -> list[str]:
        profiles = list(original(candidate, result, source_text, config))
        if not profiles or not negative:
            return profiles
        key = str(candidate.get("key") or "")
        parent_key = str((candidate.get("runtime_repair") or {}).get("parent_key") or "")
        plan_key = parent_key or key
        plan = quick.brain.PLANS.get(plan_key) or {}
        provider_id = _norm(plan.get("providerId") or candidate.get("canonical_id") or candidate.get("upstream_id"))
        provider_version = _version(candidate)
        signature = str(plan.get("signature") or plan.get("failureClass") or "unknown_failure")
        kept: list[str] = []
        suppressed: list[str] = []
        for profile in profiles:
            failures = max(
                [int(row.get("consecutiveFailures") or row.get("failures") or 0) for row in negative if _matches(
                    row,
                    provider_id=provider_id,
                    provider_version=provider_version,
                    signature=signature,
                    profile=profile,
                )] or [0]
            )
            if failures >= threshold:
                suppressed.append(profile)
            else:
                kept.append(profile)
        if suppressed:
            plan["suppressedProfiles"] = sorted(set([*(plan.get("suppressedProfiles") or []), *suppressed]))
            plan["negativeMemoryApplied"] = True
            if profiles and not kept:
                plan["action"] = "collect-more-evidence"
                plan["exitReason"] = "sandbox_repeated_failed_profile"
        return kept

    quick._brain_matching_profiles = learning_matching
    os.environ["NUVIO_BRAIN_PLANNER_MODE"] = "learning"
    print(f"FIELD_BRAIN_NEGATIVE_MEMORY entries={len(negative)} threshold={threshold}", file=sys.stderr)
    return int(quick.main())


if __name__ == "__main__":
    raise SystemExit(main())
