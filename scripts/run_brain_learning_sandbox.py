#!/usr/bin/env python3
"""Run the existing Quick Brain in daily learning mode with cross-day memory.

The production repair engine is not forked. This wrapper adds two evidence
sources before the Brain chooses mutations:
- repeated failed provider/signature/profile combinations from prior learning;
- sanitized official Nuvio reader failures from the latest native corpus.

Native reader evidence never contains raw stream URLs, cookies or header values.
It only carries causal classes/codes/signatures so repair remains provider-agnostic.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import run_adaptive_quick_repair as quick  # noqa: E402


PLAYER_FAILURE_PRIORITY = (
    "playback_context_gap",
    "media_extraction_gap",
    "player_container_unsupported",
    "player_container_malformed",
    "player_manifest_gap",
    "player_decoder_gap",
    "player_engine_compatibility_gap",
    "player_runtime_gap",
)
SAFE_TOKEN = re.compile(r"[^A-Za-z0-9_.:-]+")


def _load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _load_state() -> dict[str, Any]:
    raw = str(os.environ.get("NUVIO_BRAIN_LEARNING_STATE") or "").strip()
    return _load_json(Path(raw).resolve()) if raw else {}


def _native_summary_path() -> Path:
    raw = str(os.environ.get("NUVIO_NATIVE_CORPUS_SUMMARY") or "").strip()
    if raw:
        return Path(raw).resolve()
    return ROOT / "brain-learning-input/native/native-corpus-summary.json"


def _native_player_feedback() -> dict[str, dict[str, Any]]:
    summary = _load_json(_native_summary_path())
    player = summary.get("playerFeedback") if isinstance(summary.get("playerFeedback"), dict) else {}
    rows = player.get("providers") if isinstance(player.get("providers"), list) else []
    output: dict[str, dict[str, Any]] = {}
    for raw in rows:
        if not isinstance(raw, dict):
            continue
        provider_id = _norm(raw.get("providerId"))
        failed = max(0, int(raw.get("failedAttempts") or 0))
        if not provider_id or failed <= 0:
            continue
        failure_classes = _safe_tokens(raw.get("failureClasses"), 96)
        primary = next((name for name in PLAYER_FAILURE_PRIORITY if name in failure_classes), None)
        if primary is None:
            primary = failure_classes[0] if failure_classes else "player_runtime_gap"
        exo_codes = _safe_ints(raw.get("exoCodes"))
        exo_names = _safe_tokens(raw.get("exoCodeNames"), 96)
        source_statuses = _safe_ints(raw.get("sourceStatuses"))
        signatures = _safe_tokens(raw.get("sourceSignatures"), 64)
        output[provider_id] = {
            "providerId": provider_id,
            "attempts": max(0, int(raw.get("attempts") or 0)),
            "readyAttempts": max(0, int(raw.get("readyAttempts") or 0)),
            "failedAttempts": failed,
            "failureClass": primary,
            "failureClasses": failure_classes,
            "exoCode": exo_codes[0] if exo_codes else _exo_code_from_names(exo_names),
            "exoCodeName": exo_names[0] if exo_names else "",
            "sourceStatus": source_statuses[0] if source_statuses else 0,
            "sourceSignature": signatures[0] if signatures else "unknown",
            "mpvRecovered": raw.get("mpvRecovered") is True,
        }
    return output


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


def _safe_tokens(value: Any, limit: int) -> list[str]:
    rows = value if isinstance(value, list) else []
    output: list[str] = []
    for raw in rows:
        token = SAFE_TOKEN.sub("", str(raw or ""))[:limit]
        if token and token not in output:
            output.append(token)
        if len(output) >= 24:
            break
    return output


def _safe_ints(value: Any) -> list[int]:
    rows = value if isinstance(value, list) else []
    output: list[int] = []
    for raw in rows:
        try:
            number = int(raw)
        except (TypeError, ValueError):
            continue
        if 0 <= number <= 9999 and number not in output:
            output.append(number)
        if len(output) >= 16:
            break
    return output


def _exo_code_from_names(names: list[str]) -> int:
    mapping = {
        "ERROR_CODE_PARSING_CONTAINER_MALFORMED": 3001,
        "ERROR_CODE_PARSING_MANIFEST_MALFORMED": 3002,
        "ERROR_CODE_PARSING_CONTAINER_UNSUPPORTED": 3003,
        "ERROR_CODE_PARSING_MANIFEST_UNSUPPORTED": 3004,
        "ERROR_CODE_DECODING_FAILED": 4003,
        "ERROR_CODE_DECODING_FORMAT_EXCEEDS_CAPABILITIES": 4004,
        "ERROR_CODE_DECODING_FORMAT_UNSUPPORTED": 4005,
    }
    return next((mapping[name] for name in names if name in mapping), 0)


def _candidate_map(registry_path: Path) -> dict[str, dict[str, Any]]:
    registry = _load_json(registry_path)
    return {
        str(row.get("key")): row
        for row in registry.get("candidates") or []
        if isinstance(row, dict) and row.get("key")
    }


def _inject_native_reader_evidence(registry_path: Path, report: dict[str, Any], feedback: dict[str, dict[str, Any]]) -> int:
    if not feedback:
        return 0
    candidates = _candidate_map(registry_path)
    injected = 0
    for result in report.get("results") or []:
        if not isinstance(result, dict):
            continue
        key = str(result.get("key") or "")
        candidate = candidates.get(key)
        if not candidate:
            continue
        provider_id = _norm(candidate.get("canonical_id") or candidate.get("upstream_id"))
        native = feedback.get(provider_id)
        if not native:
            continue
        tests = result.setdefault("tests", [])
        if not isinstance(tests, list):
            tests = []
            result["tests"] = tests
        # One sanitized synthetic observation is sufficient for the existing
        # planner transport. No provider id-specific rule is created here.
        message = (
            f"native_player exo_code={native['exoCode']} source_status={native['sourceStatus']} "
            f"signature={native['sourceSignature']} mpv_ready={'true' if native['mpvRecovered'] else 'false'} "
            "exo_ready=false playable=false"
        )
        tests.append({
            "failure_class": native["failureClass"],
            "status": "native_player_failure",
            "error_details": {
                "code": native["exoCodeName"] or str(native["exoCode"]),
                "message": message,
            },
            "network_observations": ([{
                "status": native["sourceStatus"],
                "infrastructure": False,
            }] if native["sourceStatus"] else []),
            "fixture": {},
            "streams_playable": 0,
            "stream_count": 0,
            "streams_returned": 0,
        })
        injected += 1
    return injected


def main() -> int:
    state = _load_state()
    negative = _negative_entries(state)
    player_feedback = _native_player_feedback()
    policy = quick.brain.policy()
    lab = policy.get("learningLab") if isinstance(policy.get("learningLab"), dict) else {}
    threshold = max(1, int(lab.get("maxRepeatedFailedProfile") or 2))
    original_matching = quick._brain_matching_profiles
    original_planner = quick._plan_quick_results

    def player_aware_planner(registry_path: Path, report: dict[str, Any]) -> None:
        injected = _inject_native_reader_evidence(registry_path, report, player_feedback)
        if injected:
            print(f"FIELD_BRAIN_NATIVE_PLAYER_FEEDBACK injected={injected} providers={len(player_feedback)}", file=sys.stderr)
        original_planner(registry_path, report)

    def learning_matching(candidate: dict[str, Any], result: dict[str, Any], source_text: str, config: dict[str, Any] | None = None) -> list[str]:
        profiles = list(original_matching(candidate, result, source_text, config))
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

    quick._plan_quick_results = player_aware_planner
    quick._brain_matching_profiles = learning_matching
    os.environ["NUVIO_BRAIN_PLANNER_MODE"] = "learning"
    print(
        f"FIELD_BRAIN_NEGATIVE_MEMORY entries={len(negative)} threshold={threshold} "
        f"native_player_providers={len(player_feedback)}",
        file=sys.stderr,
    )
    try:
        return int(quick.main())
    finally:
        quick._plan_quick_results = original_planner
        quick._brain_matching_profiles = original_matching


if __name__ == "__main__":
    raise SystemExit(main())
