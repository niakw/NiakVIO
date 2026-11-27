#!/usr/bin/env python3
"""Time-budgeted adaptive provider investigation queue for NiakVIO Learning."""
from __future__ import annotations

import argparse
import copy
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
import select
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
from brain_negative_memory_retention import select_bounded_negative_memory
from repair_promotion_state import durable_accepted_event, provisional_accepted_event
from fill_brain_learning_guidance_gaps import (
    attested_source_contract_frontier,
    attested_source_resolver_frontier,
    attested_source_player_target_frontier,
    attested_source_player_structure_frontier,
)
from build_provider_execution_plan import build as build_provider_execution_plan
from brain_source_family_state import (
    RESOLVER_CONTRACT,
    RESOLVER_FAILURE_CLASS,
    RESOLVER_STRATEGY_ID,
    source_family_parser_installed,
    source_family_resolver_installed,
)

PLAYER_REQUEST_CONTRACT_PROFILE = "document_request_contract_mining_v2"
PLAYER_REQUEST_CONTRACT_FAILURE = "media_extraction_gap"
SESSION_BOOTSTRAP_FOLLOWUP_PROFILE = "provider_session_bootstrap_replay_v1"

class BudgetExhausted(RuntimeError):
    """The bounded Learning work window ended; persist state and resume later."""


class LearningLabSession:
    """One warm Node Lab process reused for every provider in a Learning window."""

    PREFIX = "NUVIO_LAB_SESSION_RESULT="

    def __init__(self, deadline: float) -> None:
        self.deadline = deadline
        self.process = subprocess.Popen(
            ["node", str(SCRIPTS / "nuvio_client_lab_session.cjs")],
            cwd=ROOT,
            env=os.environ.copy(),
            text=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=None,
            bufsize=1,
            start_new_session=(os.name == "posix"),
        )
        self.request({"action": "ping"}, deadline=deadline)

    def request(self, payload: dict[str, Any], *, deadline: float) -> dict[str, Any]:
        if self.process.poll() is not None:
            raise RuntimeError(f"Learning Lab session exited early: {self.process.returncode}")
        assert self.process.stdin is not None and self.process.stdout is not None
        self.process.stdin.write(json.dumps(payload, ensure_ascii=False) + "\n")
        self.process.stdin.flush()
        timeout = remaining_seconds(deadline, 1)
        ready, _, _ = select.select([self.process.stdout], [], [], timeout)
        if not ready:
            self.close()
            raise BudgetExhausted("Learning Lab session exceeded remaining global budget")
        line = self.process.stdout.readline()
        if not line:
            raise RuntimeError("Learning Lab session closed without a response")
        if not line.startswith(self.PREFIX):
            raise RuntimeError(f"unexpected Learning Lab session output: {line[:160]!r}")
        response = json.loads(line[len(self.PREFIX):])
        if response.get("ok") is not True:
            raise RuntimeError(f"Learning Lab session request failed: {response.get('error') or 'unknown'}")
        return response

    def close(self) -> None:
        if self.process.poll() is not None:
            return
        try:
            if self.process.stdin is not None:
                self.process.stdin.write('{"action":"close"}\n')
                self.process.stdin.flush()
        except Exception:
            pass
        try:
            self.process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            terminate_process_group(self.process, grace_seconds=2.0)


def ensure_learning_lab_session(
    session: LearningLabSession,
    deadline: float,
    *,
    factory: Any = LearningLabSession,
) -> LearningLabSession:
    """Recreate the warm Lab process after a provider-local slice timeout.

    A request timeout intentionally closes the shared Node process so no stale
    request can bleed into the next provider. The queue itself is longer-lived:
    the next provider must get a fresh session rather than failing the whole
    Learning phase because the previous provider consumed its fair-share slice.
    """
    if session.process.poll() is None:
        return session
    return factory(deadline)


ANOMALY_SCORES = {
    "provider_unreachable": 120,
    "unavailable": 110,
    "blocked": 100,
    "runtime_error": 90,
    "no_streams": 70,
    "degraded": 60,
    "reachable": 30,
    "healthy": 0,
}

def load_json(path: Path, default: Any = None) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {} if default is None else default

def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def norm(value: Any) -> str:
    return str(value or "").strip().casefold().replace("_", "-")

def provider_rows(report: dict[str, Any]) -> list[dict[str, Any]]:
    rows = report.get("providers")
    if isinstance(rows, list):
        return [x for x in rows if isinstance(x, dict)]
    rows = report.get("results")
    return [x for x in rows if isinstance(x, dict)] if isinstance(rows, list) else []

def diagnostic(row: dict[str, Any]) -> dict[str, Any]:
    provider_id = norm(row.get("id") or row.get("canonical_id") or row.get("upstream_id"))
    status = str(row.get("observed_status") or row.get("status") or "").strip()
    evidence = row.get("evidence") if isinstance(row.get("evidence"), dict) else {}
    server_ok = bool(evidence.get("provider_server_successful_response", False))
    server_accessible = bool(evidence.get("provider_server_accessible", False))
    hosts = [str(x) for x in (evidence.get("provider_server_hosts") or []) if str(x)]
    score = int(ANOMALY_SCORES.get(status, 40 if status else 20))
    if status in {"blocked", "runtime_error", "no_streams"} and server_ok:
        score = max(1, score - 35)
    return {
        "provider": provider_id,
        "status": status,
        "score": score,
        "needs_route_search": (
            status in {"provider_unreachable", "unavailable"}
            or (status in {"blocked", "runtime_error"} and not server_accessible)
            or (not hosts and status not in {"healthy", "no_streams"})
        ),
        "server_accessible": server_accessible,
        "server_successful_response": server_ok,
        "host_count": len(hosts),
    }

def unique(values: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        key = norm(value)
        if key and key not in seen:
            out.append(key)
            seen.add(key)
    return out


def sanitize_experiment_reason(value: Any, limit: int = 180) -> str:
    """Keep cross-phase experiment evidence compact and free of raw network data."""
    text = str(value or "")
    text = re.sub(r"https?://\S+", "<url>", text, flags=re.IGNORECASE)
    text = re.sub(
        r"(?i)(token|authorization|cookie|secret)\s*[:=]\s*\S+",
        r"\1=<redacted>",
        text,
    )
    return " ".join(text.split())[:limit]


def sanitize_network_execution_summary(value: Any) -> dict[str, Any]:
    """Allow only bounded aggregate execution facts into cross-run memory."""
    if not isinstance(value, dict):
        return {}
    buckets = value.get("statusBuckets") if isinstance(value.get("statusBuckets"), dict) else {}
    allowed_bucket_names = ("2xx", "3xx", "4xx", "5xx", "network")
    status_buckets = {
        name: max(0, min(10000, int(buckets.get(name) or 0)))
        for name in allowed_bucket_names
    }
    allowed_methods = {"GET", "POST", "HEAD"}
    methods = sorted({
        str(item).upper()
        for item in value.get("methods") or []
        if str(item).upper() in allowed_methods
    })
    allowed_stages = {"search", "content_lookup", "detail", "episode", "player", "media", "provider_fetch", "other"}
    stages = sorted({
        str(item).strip().casefold()
        for item in value.get("stages") or []
        if str(item).strip().casefold() in allowed_stages
    })
    allowed_kinds = {"html", "json", "javascript", "text", "binary", "media"}
    response_kinds = sorted({
        str(item).strip().casefold()
        for item in value.get("responseKinds") or []
        if str(item).strip().casefold() in allowed_kinds
    })
    deepest = str(value.get("deepestStage") or "none").strip().casefold()
    if deepest not in allowed_stages | {"none"}:
        deepest = "none"
    return {
        "schemaVersion": 1,
        "providerRequestCount": max(0, min(10000, int(value.get("providerRequestCount") or 0))),
        "successfulProviderRequestCount": max(0, min(10000, int(value.get("successfulProviderRequestCount") or 0))),
        "networkFailureCount": max(0, min(10000, int(value.get("networkFailureCount") or 0))),
        "statusBuckets": status_buckets,
        "methods": methods,
        "stages": stages,
        "deepestStage": deepest,
        "responseKinds": response_kinds,
        "proofAuthority": False,
        "publicationAuthority": False,
        "rawAddressRetained": False,
        "headersRetained": False,
        "bodyRetained": False,
    }


def sanitize_network_execution_delta(value: Any) -> dict[str, Any]:
    """Allow only bounded signed parent-vs-candidate causal deltas."""
    if not isinstance(value, dict):
        return {}
    bucket_names = ("2xx", "3xx", "4xx", "5xx", "network")
    raw_buckets = value.get("statusBucketDelta") if isinstance(value.get("statusBucketDelta"), dict) else {}
    def signed(raw: Any) -> int:
        try:
            number = int(raw or 0)
        except (TypeError, ValueError):
            number = 0
        return max(-10000, min(10000, number))
    allowed_methods = {"GET", "POST", "HEAD"}
    allowed_stages = {"search", "content_lookup", "detail", "episode", "player", "media", "provider_fetch", "other"}
    allowed_kinds = {"html", "json", "javascript", "text", "binary", "media"}
    parent_deepest = str(value.get("parentDeepestStage") or "none").strip().casefold()
    candidate_deepest = str(value.get("candidateDeepestStage") or "none").strip().casefold()
    if parent_deepest not in allowed_stages | {"none"}:
        parent_deepest = "none"
    if candidate_deepest not in allowed_stages | {"none"}:
        candidate_deepest = "none"
    return {
        "schemaVersion": 1,
        "providerRequestDelta": signed(value.get("providerRequestDelta")),
        "successfulProviderRequestDelta": signed(value.get("successfulProviderRequestDelta")),
        "networkFailureDelta": signed(value.get("networkFailureDelta")),
        "statusBucketDelta": {name: signed(raw_buckets.get(name)) for name in bucket_names},
        "newMethods": sorted({
            str(item).upper()
            for item in value.get("newMethods") or []
            if str(item).upper() in allowed_methods
        }),
        "newStages": sorted({
            str(item).strip().casefold()
            for item in value.get("newStages") or []
            if str(item).strip().casefold() in allowed_stages
        }),
        "newResponseKinds": sorted({
            str(item).strip().casefold()
            for item in value.get("newResponseKinds") or []
            if str(item).strip().casefold() in allowed_kinds
        }),
        "parentDeepestStage": parent_deepest,
        "candidateDeepestStage": candidate_deepest,
        "stageRankDelta": max(-16, min(16, signed(value.get("stageRankDelta")))),
        "stageAdvanced": value.get("stageAdvanced") is True,
        "proofAuthority": False,
        "publicationAuthority": False,
        "rawAddressRetained": False,
        "headersRetained": False,
        "bodyRetained": False,
    }


def phase_experiment_entries(
    provider_id: str,
    plan: dict[str, Any],
    repair: dict[str, Any],
    final_lab: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Materialize the exact fair-share experiment identity and outcome.

    The outer Learning queue is the authoritative owner of one experiment per
    provider/phase. Child runtime memory can contain older or replanned state;
    this ledger freezes the exact provider plan that the queue actually ran so
    the next phase cannot accidentally turn g3/v4 back into g1/v0.
    """
    if not isinstance(plan, dict) or not plan:
        return []

    # The experiment identity is the selected causal profile/generation, not a
    # fragile planner action label. A plan can legitimately fall back to
    # collect/defer semantics when the selected profile cannot materialize;
    # that profile_unavailable outcome must still advance cross-phase memory.
    if str(plan.get("failureClass") or "").strip().casefold() == "healthy":
        return []

    report = repair.get("report") if isinstance(repair.get("report"), dict) else {}
    rounds = [row for row in report.get("rounds") or [] if isinstance(row, dict)]
    allowed = [
        str(value)
        for value in plan.get("allowedProfiles") or []
        if str(value).strip()
    ]
    attempted = [
        str(value)
        for value in repair.get("attemptedProfiles") or []
        if str(value).strip()
    ]
    # If the child replanned after testing a profile, allowedProfiles belongs
    # to the *next* hypothesis, not the experiment that just ran. Never record
    # that future strategy as failed before it has actually been attempted.
    profiles = list(dict.fromkeys(attempted or allowed))
    if not profiles:
        return []

    now = datetime.now(timezone.utc).isoformat()
    playable = isinstance(final_lab, dict) and str(final_lab.get("status") or "") == "playable"

    def events(kind: str, profile: str) -> list[dict[str, Any]]:
        output: list[dict[str, Any]] = []
        for round_row in rounds:
            for raw in round_row.get(kind) or []:
                if not isinstance(raw, dict):
                    continue
                raw_profile = str(raw.get("profile") or "")
                if raw_profile and raw_profile != profile:
                    continue
                if not raw_profile and kind == "accepted":
                    # Accepted events may omit profile; the planned/attempted
                    # profile is still exact when the fair-share plan has one.
                    if len(profiles) != 1:
                        continue
                output.append(raw)
        return output

    entries: list[dict[str, Any]] = []
    for profile in profiles:
        attempts = events("attempts", profile)
        accepted = events("accepted", profile)
        progress = events("exploration_progress", profile)
        rejected = events("rejected", profile)
        not_generated = [
            row for row in attempts
            if str(row.get("status") or "") == "not_generated"
        ]
        generated = [
            row for row in attempts
            if str(row.get("status") or "") == "generated"
        ]

        # Round events snapshot the plan that actually selected this profile.
        # The report-level plan may already be the replan for the next strategy.
        event_plan = next(
            (
                row.get("brain_plan")
                for row in [*attempts, *accepted, *progress, *rejected]
                if isinstance(row.get("brain_plan"), dict) and row.get("brain_plan")
            ),
            None,
        )
        effective_plan = event_plan if isinstance(event_plan, dict) else plan
        variant = max(0, int(effective_plan.get("experimentVariant") or 0))
        generation = max(1, int(effective_plan.get("experimentGeneration") or 1))
        signature = str(
            effective_plan.get("signature")
            or effective_plan.get("failureClass")
            or ""
        ).strip()
        failure_class = str(effective_plan.get("failureClass") or "unknown_failure").strip()

        success_count = len(accepted) if playable else 0
        failures = 0
        progresses = 0
        outcome = ""
        reason = ""

        if success_count > 0:
            outcome = "accepted"
            reason = str(accepted[-1].get("reason") or "strict_playable_stream_improvement")
        elif progress:
            failures = 1
            progresses = len(progress)
            outcome = "exploration_progress_nonpublishable"
            reason = str(progress[-1].get("reason") or "sandbox_diagnostic_progress")
        elif rejected:
            failures = 1
            outcome = "rejected"
            reason = str(rejected[-1].get("reason") or "no_validated_improvement")
        elif not_generated:
            failures = 1
            outcome = "not_generated"
            reason = str(not_generated[-1].get("reason") or "candidate_generation_failed")
        elif profile not in attempted and not generated:
            failures = 1
            outcome = "profile_unavailable"
            reason = "planned_profile_not_applicable_to_current_bytes"
        else:
            failures = 1
            outcome = "rejected"
            reason = "fair_share_no_validated_improvement"

        network_event = (
            accepted[-1] if accepted
            else progress[-1] if progress
            else rejected[-1] if rejected
            else {}
        )
        network_execution = sanitize_network_execution_summary(
            network_event.get("network_execution") if isinstance(network_event, dict) else {}
        )

        network_execution_delta = sanitize_network_execution_delta(
            network_event.get("network_execution_delta") if isinstance(network_event, dict) else {}
        )

        entries.append({
            "providerId": norm(provider_id),
            "providerVersion": "*",
            "failureClass": failure_class,
            "signature": signature,
            "profile": profile,
            "positiveProgramFingerprint": str(
                effective_plan.get("positiveProgramFingerprint") or ""
            ).strip().casefold(),
            "strategyImplementationFingerprint": str(
                effective_plan.get("strategyImplementationFingerprint") or ""
            ).strip().casefold(),
            "llmAdvisorExperimentFingerprint": str(
                effective_plan.get("llmAdvisorExperimentFingerprint") or ""
            ).strip().casefold(),
            "llmAdvisorGuidanceKind": str(
                effective_plan.get("llmAdvisorGuidanceKind") or ""
            ).strip().casefold(),
            "llmAdvisorMetaGapGeneration": max(
                -1,
                int(
                    effective_plan["llmAdvisorMetaGapGeneration"]
                    if effective_plan.get("llmAdvisorMetaGapGeneration") is not None
                    else -1
                ),
            ),
            "experimentVariant": variant,
            "experimentGeneration": generation,
            "capabilityStrategy": str(effective_plan.get("capabilityStrategy") or "").strip().casefold(),
            "observedPipelineStage": str(effective_plan.get("observedPipelineStage") or "").strip().casefold(),
            "attempts": max(1, len(attempts)),
            "successes": success_count,
            "failures": failures,
            "consecutiveFailures": 0 if success_count else failures,
            "progresses": progresses,
            "lastOutcome": outcome,
            "lastReason": sanitize_experiment_reason(reason),
            "lastSeenAt": now,
            "memoryRole": "fair-share-exact-experiment-ledger",
            # A generated-and-retested child is distinct from an attempt that
            # never produced executable bytes. Do not poison runtime-negative
            # memory with not_generated/profile_unavailable outcomes.
            "executionObserved": bool(accepted or rejected or progress),
            "generationAttemptObserved": bool(not_generated),
            "networkExecutionSummary": network_execution,
            "networkExecutionDelta": network_execution_delta,
        })
    return entries


def missing_network_diagnostic_negative(
    state: dict[str, Any],
    provider_id: str,
    profile: str,
) -> dict[str, Any] | None:
    """Return the newest executed negative missing causal network telemetry."""
    memory = state.get("experimentMemory") if isinstance(state.get("experimentMemory"), dict) else {}
    rows = memory.get("entries") if isinstance(memory.get("entries"), list) else []
    provider = norm(provider_id)
    wanted_profile = str(profile or "").strip()
    candidates: list[dict[str, Any]] = []
    for raw in rows:
        if not isinstance(raw, dict):
            continue
        if norm(raw.get("providerId")) != provider:
            continue
        if str(raw.get("profile") or "").strip() != wanted_profile:
            continue
        if raw.get("executionObserved") is not True:
            continue
        if str(raw.get("lastOutcome") or "") in {"not_generated", "profile_unavailable"}:
            continue
        fingerprint = str(raw.get("strategyImplementationFingerprint") or "").strip().casefold()
        if not re.fullmatch(r"[0-9a-f]{64}", fingerprint):
            continue
        summary = raw.get("networkExecutionSummary")
        delta = raw.get("networkExecutionDelta")
        if (
            isinstance(summary, dict)
            and "providerRequestCount" in summary
            and isinstance(delta, dict)
            and "providerRequestDelta" in delta
        ):
            continue
        candidates.append(raw)
    if not candidates:
        return None
    return copy.deepcopy(sorted(
        candidates,
        key=lambda row: str(row.get("lastSeenAt") or ""),
        reverse=True,
    )[0])


def network_causal_followup(
    state: dict[str, Any],
    provider_id: str,
    *,
    source_profile: str = PLAYER_REQUEST_CONTRACT_PROFILE,
    failure_class: str = PLAYER_REQUEST_CONTRACT_FAILURE,
) -> dict[str, str] | None:
    """Turn sanitized executed-negative network facts into one next causal Lego.

    This is decision evidence only. It never grants proof, playback, mutation or
    publication authority. The transition is intentionally narrow: the scripted
    request miner must have emitted real provider requests, received some 2xx
    responses, hit a 4xx-heavy surface, and observed HTML only without media.
    That shape is compatible with missing provider session/bootstrap context,
    not with a dead transport or a parser that emitted nothing.
    """
    memory = state.get("experimentMemory") if isinstance(state.get("experimentMemory"), dict) else {}
    rows = [
        row for row in memory.get("entries") or []
        if isinstance(row, dict) and norm(row.get("providerId")) == norm(provider_id)
    ]
    wanted_failure = str(failure_class or "").strip().casefold()

    # Do not suppress the causal proposal merely because an older implementation
    # of the same profile executed. Implementation freshness belongs to the
    # planner's strategyImplementationFingerprint-aware negative memory. This is
    # essential when a Lego evolves from session-only to resolver+V2+session:
    # the old negative remains historical evidence but cannot veto new bytes.

    candidates: list[dict[str, Any]] = []
    for row in rows:
        if str(row.get("profile") or "").strip() != str(source_profile or "").strip():
            continue
        row_failure = str(row.get("failureClass") or "").strip().casefold()
        if row_failure not in {"", wanted_failure}:
            continue
        if row.get("executionObserved") is not True:
            continue
        if str(row.get("lastOutcome") or "") not in {
            "rejected", "exploration_progress_nonpublishable",
        }:
            continue
        summary = sanitize_network_execution_summary(row.get("networkExecutionSummary"))
        delta = sanitize_network_execution_delta(row.get("networkExecutionDelta"))
        if "providerRequestCount" not in summary or "providerRequestDelta" not in delta:
            continue
        requests = int(summary.get("providerRequestCount") or 0)
        successful = int(summary.get("successfulProviderRequestCount") or 0)
        network_failures = int(summary.get("networkFailureCount") or 0)
        buckets = summary.get("statusBuckets") or {}
        four_xx = int(buckets.get("4xx") or 0)
        kinds = set(summary.get("responseKinds") or [])
        deepest = str(summary.get("deepestStage") or "none")
        request_delta = int(delta.get("providerRequestDelta") or 0)
        successful_delta = int(delta.get("successfulProviderRequestDelta") or 0)
        delta_buckets = delta.get("statusBucketDelta") or {}
        four_xx_delta = int(delta_buckets.get("4xx") or 0)
        new_kinds = set(delta.get("newResponseKinds") or [])
        if requests <= 0 or successful <= 0:
            continue
        if four_xx < max(2, successful):
            continue
        if network_failures >= requests:
            continue
        if kinds != {"html"}:
            continue
        if deepest not in {"content_lookup", "episode", "player"}:
            continue
        # The aggregate shape is only a hint. Require causal attribution to
        # the candidate: V2 must have introduced requests, successful responses
        # and additional 4xx pressure. If the parent already owned those facts,
        # session bootstrap is not justified by this experiment.
        if request_delta <= 0 or successful_delta <= 0 or four_xx_delta <= 0:
            continue
        if "media" in new_kinds:
            continue
        if new_kinds - {"html"}:
            continue
        candidates.append(row)

    if not candidates:
        return None
    source = sorted(
        candidates,
        key=lambda row: str(row.get("lastSeenAt") or ""),
        reverse=True,
    )[0]
    summary = sanitize_network_execution_summary(source.get("networkExecutionSummary"))
    return {
        "profile": SESSION_BOOTSTRAP_FOLLOWUP_PROFILE,
        "failureClass": PLAYER_REQUEST_CONTRACT_FAILURE,
        "reason": "scripted_requests_reached_html_with_4xx_pressure_session_bootstrap_untried",
        "sourceProfile": str(source_profile),
        "providerRequestCount": str(int(summary.get("providerRequestCount") or 0)),
        "successfulProviderRequestCount": str(int(summary.get("successfulProviderRequestCount") or 0)),
        "fourXxCount": str(int((summary.get("statusBuckets") or {}).get("4xx") or 0)),
        "providerRequestDelta": str(int((source.get("networkExecutionDelta") or {}).get("providerRequestDelta") or 0)),
        "successfulProviderRequestDelta": str(int((source.get("networkExecutionDelta") or {}).get("successfulProviderRequestDelta") or 0)),
        "fourXxDelta": str(int(((source.get("networkExecutionDelta") or {}).get("statusBucketDelta") or {}).get("4xx") or 0)),
        "deepestStage": str(summary.get("deepestStage") or "none"),
    }


def diagnostic_replay_memory(
    state: dict[str, Any],
    target: dict[str, Any],
) -> dict[str, Any]:
    """Mask one exact executed implementation only inside a diagnostic child."""
    output = copy.deepcopy(state)
    memory = output.get("experimentMemory") if isinstance(output.get("experimentMemory"), dict) else {}
    rows = memory.get("entries") if isinstance(memory.get("entries"), list) else []
    provider = norm(target.get("providerId"))
    profile = str(target.get("profile") or "").strip()
    fingerprint = str(target.get("strategyImplementationFingerprint") or "").strip().casefold()
    memory["entries"] = [
        row for row in rows
        if not (
            isinstance(row, dict)
            and norm(row.get("providerId")) == provider
            and str(row.get("profile") or "").strip() == profile
            and str(row.get("strategyImplementationFingerprint") or "").strip().casefold() == fingerprint
            and row.get("executionObserved") is True
        )
    ]
    output["experimentMemory"] = memory
    output["publicationAllowed"] = False
    output["productionWritesAllowed"] = False
    return output


def repair_network_execution_summary(
    repair: dict[str, Any],
    profile: str,
) -> dict[str, Any]:
    report = repair.get("report") if isinstance(repair.get("report"), dict) else {}
    matches: list[dict[str, Any]] = []
    for round_row in report.get("rounds") or []:
        if not isinstance(round_row, dict):
            continue
        for kind in ("accepted", "exploration_progress", "rejected"):
            for event in round_row.get(kind) or []:
                if not isinstance(event, dict):
                    continue
                if str(event.get("profile") or "").strip() != str(profile or "").strip():
                    continue
                summary = sanitize_network_execution_summary(event.get("network_execution"))
                if "providerRequestCount" in summary:
                    matches.append(summary)
    return matches[-1] if matches else {}


def repair_network_execution_delta(
    repair: dict[str, Any],
    profile: str,
) -> dict[str, Any]:
    report = repair.get("report") if isinstance(repair.get("report"), dict) else {}
    matches: list[dict[str, Any]] = []
    for round_row in report.get("rounds") or []:
        if not isinstance(round_row, dict):
            continue
        for kind in ("accepted", "exploration_progress", "rejected"):
            for event in round_row.get(kind) or []:
                if not isinstance(event, dict):
                    continue
                if str(event.get("profile") or "").strip() != str(profile or "").strip():
                    continue
                delta = sanitize_network_execution_delta(event.get("network_execution_delta"))
                if "providerRequestDelta" in delta:
                    matches.append(delta)
    return matches[-1] if matches else {}


def diagnostic_network_backfill_entry(
    target: dict[str, Any],
    plan: dict[str, Any],
    summary: dict[str, Any],
    delta: dict[str, Any],
) -> dict[str, Any] | None:
    """Update telemetry only; never change the historical experiment verdict."""
    target_fp = str(target.get("strategyImplementationFingerprint") or "").strip().casefold()
    plan_fp = str(plan.get("strategyImplementationFingerprint") or "").strip().casefold()
    if not re.fullmatch(r"[0-9a-f]{64}", target_fp) or plan_fp != target_fp:
        return None
    safe = sanitize_network_execution_summary(summary)
    if "providerRequestCount" not in safe:
        return None
    safe_delta = sanitize_network_execution_delta(delta)
    if "providerRequestDelta" not in safe_delta:
        return None
    row = copy.deepcopy(target)
    row["networkExecutionSummary"] = safe
    row["networkExecutionDelta"] = safe_delta
    # The replay enriches an already-counted experiment; counters and verdict
    # intentionally remain byte-for-byte those of the historical row.
    return row


def _phase_experiment_key(row: dict[str, Any]) -> tuple[str, str, str, str, str, str, str, str, int, int]:
    """Match the production Brain memory identity, including LLM experiment bytes.

    A meta-gap fingerprint is part of the executable hypothesis. Dropping it
    collapses distinct Qwen experiments into the same profile/generation row
    and makes failedFingerprint() unable to rotate away from an executed
    negative hypothesis.
    """
    return (
        norm(row.get("providerId")),
        str(row.get("providerVersion") or "*").strip() or "*",
        str(row.get("failureClass") or "").strip(),
        str(row.get("signature") or "").strip(),
        str(row.get("profile") or "").strip(),
        str(row.get("positiveProgramFingerprint") or "").strip().casefold(),
        str(row.get("strategyImplementationFingerprint") or "").strip().casefold(),
        str(row.get("llmAdvisorExperimentFingerprint") or "").strip().casefold(),
        max(0, int(row.get("experimentVariant") or 0)),
        max(1, int(row.get("experimentGeneration") or 1)),
    )


def _learning_memory_capacity() -> int:
    """Use the same bounded negative-memory budget in Learning and Repair."""
    policy_path = ROOT / "engine_v2" / "config" / "brain-policy.json"
    try:
        policy = json.loads(policy_path.read_text(encoding="utf-8"))
        production = policy.get("production") if isinstance(policy, dict) else {}
        memory = production.get("negativeExperimentMemory") if isinstance(production, dict) else {}
        return max(1, min(20000, int(memory.get("maxEntries") or 1000)))
    except (OSError, ValueError, TypeError, OverflowError, AttributeError):
        return 1000


def apply_diagnostic_network_backfill(
    state: dict[str, Any],
    backfill: dict[str, Any],
) -> dict[str, Any]:
    """Attach telemetry to one existing experiment without changing counters."""
    output = copy.deepcopy(state) if isinstance(state, dict) else {}
    output["publicationAllowed"] = False
    output["productionWritesAllowed"] = False
    memory = output.get("experimentMemory")
    if not isinstance(memory, dict):
        raise ValueError("diagnostic backfill requires existing experiment memory")
    rows = memory.get("entries")
    if not isinstance(rows, list):
        raise ValueError("diagnostic backfill requires existing experiment entries")
    key = _phase_experiment_key(backfill)
    safe = sanitize_network_execution_summary(backfill.get("networkExecutionSummary"))
    safe_delta = sanitize_network_execution_delta(backfill.get("networkExecutionDelta"))
    if "providerRequestCount" not in safe or "providerRequestDelta" not in safe_delta:
        raise ValueError("diagnostic backfill requires sanitized network telemetry and delta")
    matched = 0
    for row in rows:
        if not isinstance(row, dict) or _phase_experiment_key(row) != key:
            continue
        row["networkExecutionSummary"] = copy.deepcopy(safe)
        row["networkExecutionDelta"] = copy.deepcopy(safe_delta)
        matched += 1
    if matched != 1:
        raise ValueError(
            f"diagnostic backfill must match exactly one historical experiment, matched={matched}"
        )
    return output


def merge_phase_learning_state(
    state: dict[str, Any],
    entries: list[dict[str, Any]],
    *,
    max_entries: int | None = None,
) -> dict[str, Any]:
    """Feed exact experiment outcomes to the next attempt without publishing them."""
    output = copy.deepcopy(state) if isinstance(state, dict) else {}
    output["publicationAllowed"] = False
    output["productionWritesAllowed"] = False
    memory = output.get("experimentMemory")
    if not isinstance(memory, dict):
        memory = {"schemaVersion": 1, "entries": []}
        output["experimentMemory"] = memory
    rows = [
        copy.deepcopy(row)
        for row in memory.get("entries") or []
        if isinstance(row, dict)
    ]
    by_key = {_phase_experiment_key(row): row for row in rows}

    for raw in entries:
        if not isinstance(raw, dict):
            continue
        row = copy.deepcopy(raw)
        key = _phase_experiment_key(row)
        current = by_key.get(key)
        if current is None:
            rows.append(row)
            by_key[key] = row
            continue

        new_successes = max(0, int(row.get("successes") or 0))
        new_failures = max(0, int(row.get("failures") or 0))
        current["attempts"] = max(0, int(current.get("attempts") or 0)) + max(1, int(row.get("attempts") or 1))
        current["successes"] = max(0, int(current.get("successes") or 0)) + new_successes
        current["failures"] = max(0, int(current.get("failures") or 0)) + new_failures
        current["progresses"] = max(0, int(current.get("progresses") or 0)) + max(0, int(row.get("progresses") or 0))
        current["consecutiveFailures"] = (
            0
            if new_successes > 0
            else max(0, int(current.get("consecutiveFailures") or 0)) + new_failures
        )
        # Preserve genuine executed-negative authority if a later phase only
        # failed to generate bytes for this same fingerprint. Conversely, an
        # old not_generated row with executionObserved=true was never executed.
        nonexecuted_outcomes = {"not_generated", "profile_unavailable"}
        prior_executed = (
            current.get("executionObserved") is True
            and str(current.get("lastOutcome") or "") not in nonexecuted_outcomes
        )
        incoming_executed = (
            row.get("executionObserved") is True
            and str(row.get("lastOutcome") or "") not in nonexecuted_outcomes
        )
        for field in (
            "lastOutcome", "lastReason", "lastSeenAt", "memoryRole",
            "capabilityStrategy", "observedPipelineStage",
            "llmAdvisorGuidanceKind", "llmAdvisorMetaGapGeneration",
            "networkExecutionSummary",
            "networkExecutionDelta",
        ):
            if field in row and (incoming_executed or not prior_executed or field not in {"lastOutcome", "lastReason"}):
                current[field] = row[field]
        current["executionObserved"] = prior_executed or incoming_executed
        current["generationAttemptObserved"] = (
            current.get("generationAttemptObserved") is True
            or row.get("generationAttemptObserved") is True
            or str(row.get("lastOutcome") or "") == "not_generated"
        )

    limit = max(1, min(20000, int(max_entries if max_entries is not None else _learning_memory_capacity())))
    # Dropping oldest rows before provider-aware selection lets busy cohorts
    # evict the only executed negative proof for a new hub. Keep smaller
    # wave histories in their original order; compact only on overflow.
    memory["entries"] = (
        select_bounded_negative_memory(rows, limit=limit, minimum_per_provider=12)
        if len(rows) > limit else rows
    )
    memory["schemaVersion"] = max(1, int(memory.get("schemaVersion") or 1))
    return output


def merge_wave_experiment_entries(
    state: dict[str, Any],
    provider_entries: list[list[dict[str, Any]]],
    *,
    max_entries: int | None = None,
) -> dict[str, Any]:
    """Merge isolated provider evidence deterministically at a causal-wave barrier.

    Concurrent workers must never write shared Learning state directly. Each
    worker returns sanitized experiment rows; the barrier sorts those rows by
    their exact experiment identity and reuses the canonical phase-memory merge.
    """
    rows = [
        copy.deepcopy(row)
        for group in provider_entries
        for row in group
        if isinstance(row, dict)
    ]
    rows.sort(key=_phase_experiment_key)
    return merge_phase_learning_state(state, rows, max_entries=max_entries)


def should_continue_evolved_frontier(
    plan: dict[str, Any],
    attempts_this_phase: int,
    *,
    max_attempts: int = 3,
) -> bool:
    """Use the remaining fair-share slice to cross the g5 -> evolved-strategy boundary."""
    if not (
        1 <= int(attempts_this_phase) < max(2, int(max_attempts))
        and isinstance(plan, dict)
        and str(plan.get("action") or "") == "probe-targeted-repair"
        and bool([value for value in plan.get("allowedProfiles") or [] if str(value).strip()])
    ):
        return False

    if (
        str(plan.get("repairType") or "") == "evolved_strategy"
        and str(plan.get("learningDisposition") or "") == "execute_bounded_evolved_strategy"
    ):
        return True

    # The report returned by a sandbox attempt describes the strategy that just
    # ran. The next post-g5 strategy is only visible after that exact g5 failure
    # is merged into phase-learning-state.json. Allow one bounded continuation
    # at the explicit final Learning generation so the next sandbox process can
    # actually cross the boundary instead of stopping after merely proving g5.
    variant = max(0, int(plan.get("experimentVariant") or 0))
    generation = max(1, int(plan.get("experimentGeneration") or 1))
    generation_limit = max(0, int(plan.get("experimentGenerationLimit") or 0))
    return (
        variant == 4
        and generation_limit >= 3
        and generation >= generation_limit
        and plan.get("experimentExhausted") is not True
    )


def interleave(retries: list[str], pending: list[str]) -> list[str]:
    """Retry unresolved work without starving unseen providers."""
    retries = list(retries)
    pending = list(pending)
    out: list[str] = []
    while retries or pending:
        if retries:
            out.append(retries.pop(0))
        for _ in range(2):
            if pending:
                out.append(pending.pop(0))
    return unique(out)


def causal_batch_round_robin(
    order: list[str],
    batch_plan: dict[str, Any],
) -> tuple[list[str], list[str]]:
    """Visit one provider per causal batch before siblings from the same batch.

    This does not skip providers or transfer unverified fixes. It only changes
    investigation order so a strategy learned on the first member of a causal
    family is available in memory before the next member is explored.
    """
    groups = batch_plan.get("groups") if isinstance(batch_plan.get("groups"), list) else []
    provider_group: dict[str, str] = {}
    for row in groups:
        if not isinstance(row, dict):
            continue
        group_id = str(row.get("groupId") or "").strip()
        if not group_id:
            continue
        for value in row.get("providers") or []:
            provider = norm(value)
            if provider and provider not in provider_group:
                provider_group[provider] = group_id

    buckets: dict[str, list[str]] = {}
    group_order: list[str] = []
    for provider in unique(order):
        group_id = provider_group.get(provider) or f"provider-local:{provider}"
        if group_id not in buckets:
            buckets[group_id] = []
            group_order.append(group_id)
        buckets[group_id].append(provider)

    out: list[str] = []
    while True:
        progressed = False
        for group_id in group_order:
            bucket = buckets[group_id]
            if bucket:
                out.append(bucket.pop(0))
                progressed = True
        if not progressed:
            break
    return unique(out), group_order

def causal_family_waves(
    order: list[str],
    batch_plan: dict[str, Any],
    *,
    max_parallel: int = 4,
) -> list[list[str]]:
    """Build safe Learning waves with at most one provider per causal family.

    Families are causal memory barriers: siblings from one family must see the
    evidence produced by an earlier sibling. Different families may eventually
    execute in parallel from the same read-only phase-memory snapshot, then
    merge sanitized evidence at the wave barrier.
    """
    groups = batch_plan.get("groups") if isinstance(batch_plan.get("groups"), list) else []
    provider_group: dict[str, str] = {}
    for row in groups:
        if not isinstance(row, dict):
            continue
        group_id = str(row.get("groupId") or "").strip()
        if not group_id:
            continue
        for value in row.get("providers") or []:
            provider = norm(value)
            if provider and provider not in provider_group:
                provider_group[provider] = group_id

    buckets: dict[str, list[str]] = {}
    group_order: list[str] = []
    for provider in unique(order):
        group_id = provider_group.get(provider) or f"provider-local:{provider}"
        if group_id not in buckets:
            buckets[group_id] = []
            group_order.append(group_id)
        buckets[group_id].append(provider)

    width = max(1, int(max_parallel))
    waves: list[list[str]] = []
    while any(buckets[group_id] for group_id in group_order):
        round_rows: list[str] = []
        for group_id in group_order:
            if buckets[group_id]:
                round_rows.append(buckets[group_id].pop(0))
        for index in range(0, len(round_rows), width):
            wave = round_rows[index:index + width]
            if wave:
                waves.append(wave)
    return waves


def causal_family_frontier(
    order: list[str],
    batch_plan: dict[str, Any],
    provider_info: dict[str, dict[str, Any]] | None = None,
) -> tuple[list[str], list[str]]:
    """Select one evidence-strong Learning oracle per causal family.

    The explicit cohort remains the eligibility boundary. Within each causal
    family prefer a provider whose current observation already reached the
    provider server and does not require route rediscovery. This reduces the
    chance that transport noise, not the causal family, determines the learned
    strategy. Siblings stay pending and still require independent Repair proof.
    """
    groups = batch_plan.get("groups") if isinstance(batch_plan.get("groups"), list) else []
    provider_group: dict[str, str] = {}
    for row in groups:
        if not isinstance(row, dict):
            continue
        group_id = str(row.get("groupId") or "").strip()
        if not group_id:
            continue
        for value in row.get("providers") or []:
            provider = norm(value)
            if provider and provider not in provider_group:
                provider_group[provider] = group_id

    info = provider_info if isinstance(provider_info, dict) else {}
    family_order: list[str] = []
    members: dict[str, list[str]] = {}
    ordered = unique(order)
    for provider in ordered:
        group_id = provider_group.get(provider) or f"provider-local:{provider}"
        if group_id not in members:
            members[group_id] = []
            family_order.append(group_id)
        members[group_id].append(provider)

    def oracle_rank(provider: str, position: int) -> tuple[Any, ...]:
        row = info.get(provider) if isinstance(info.get(provider), dict) else {}
        status = str(row.get("status") or "").strip().casefold()
        return (
            status == "healthy",
            bool(row.get("needs_route_search", True)),
            row.get("server_successful_response") is not True,
            row.get("server_accessible") is not True,
            -max(0, int(row.get("host_count") or 0)),
            max(0, int(row.get("score") or 0)),
            position,
        )

    frontier: list[str] = []
    for group_id in family_order:
        group_members = members[group_id]
        chosen = min(
            enumerate(group_members),
            key=lambda item: oracle_rank(item[1], item[0]),
        )[1]
        frontier.append(chosen)

    chosen_set = set(frontier)
    deferred = [provider for provider in ordered if provider not in chosen_set]
    return frontier, deferred


def build_queue(
    report: dict[str, Any],
    previous: dict[str, Any],
    explicit: str = "",
) -> tuple[list[str], dict[str, dict[str, Any]], dict[str, Any]]:
    infos = [diagnostic(row) for row in provider_rows(report)]
    by_id = {row["provider"]: row for row in infos if row["provider"]}
    if explicit:
        pid = norm(explicit)
        if pid not in by_id:
            raise ValueError(f"unknown Learning provider: {explicit}")
        return [pid], by_id, {
            "schemaVersion": 2,
            "cycle": int((previous.get("learningQueue") or {}).get("cycle") or 1),
            "pendingProviders": [],
            "retryProviders": [],
            "completedInCycle": [],
            "providerState": copy.deepcopy((previous.get("learningQueue") or {}).get("providerState") or {}),
            "manualTarget": pid,
        }

    prev = previous.get("learningQueue") if isinstance(previous.get("learningQueue"), dict) else {}
    if not prev and isinstance(previous.get("learningScheduler"), dict):
        scheduler = previous.get("learningScheduler") or {}
        fixture_history = scheduler.get("fixtureHistory") if isinstance(scheduler.get("fixtureHistory"), dict) else {}
        provider_state = {
            norm(pid): {"attemptCount": 0, "fixtureCursor": {"movie": len(rows or []), "tv": len(rows or []), "anime": len(rows or [])}}
            for pid, rows in fixture_history.items()
            if norm(pid)
        }
        prev = {
            "cycle": int(scheduler.get("cycle") or 1),
            "pendingProviders": scheduler.get("pendingProviders") or [],
            "retryProviders": [],
            "completedInCycle": scheduler.get("completedProviders") or [],
            "providerState": provider_state,
        }
    cycle = max(1, int(prev.get("cycle") or 1))
    provider_state = copy.deepcopy(prev.get("providerState") or {})
    completed = [pid for pid in unique(prev.get("completedInCycle") or []) if pid in by_id]
    pending = [pid for pid in unique(prev.get("pendingProviders") or []) if pid in by_id and pid not in completed]
    retries = [pid for pid in unique(prev.get("retryProviders") or []) if pid in by_id]

    if not pending and not completed:
        anomalies = sorted(
            (x for x in infos if x["status"] != "healthy"),
            key=lambda x: (-int(x["score"]), x["provider"]),
        )
        healthy = sorted((x for x in infos if x["status"] == "healthy"), key=lambda x: x["provider"])
        pending = [x["provider"] for x in [*anomalies, *healthy]]
    else:
        known = set(pending) | set(completed)
        new_ids = [x["provider"] for x in infos if x["provider"] not in known]
        if new_ids:
            new_infos = sorted((by_id[x] for x in new_ids), key=lambda x: (-int(x["score"]), x["provider"]))
            pending = [x["provider"] for x in new_infos] + pending

    order = interleave(retries, pending)
    state = {
        "schemaVersion": 2,
        "cycle": cycle,
        "pendingProviders": pending,
        "retryProviders": retries,
        "completedInCycle": completed,
        "providerState": provider_state,
    }
    return order, by_id, state

def exhausted_repair_providers(memory: dict[str, Any], policy: dict[str, Any]) -> list[str]:
    """Providers whose bounded Repair/Learning experiment family is exhausted.

    Production rotates base variants, then Learning advances the final variant
    through explicit generations. Count executable negative evidence only:
    profile_unavailable and not_generated are architecture/generation debt,
    never successful execution of a repair hypothesis.
    """
    production = policy.get("production") if isinstance(policy.get("production"), dict) else {}
    negative = production.get("negativeExperimentMemory") if isinstance(production.get("negativeExperimentMemory"), dict) else {}
    max_variants = max(1, int(negative.get("maxVariantsPerSignature") or 5))
    rotate_every = max(1, int(negative.get("rotateExperimentAfterFailures") or 1))
    final_variant = max_variants - 1
    first_final_generation = max(1, int(negative.get("finalVariantGeneration") or 1))
    max_learning_generation = max(
        first_final_generation,
        int(negative.get("maxLearningGenerationsPerSignature") or first_final_generation),
    )
    groups: dict[tuple[str, str, str], dict[str, set[int]]] = {}
    for row in memory.get("entries") or []:
        if not isinstance(row, dict) or int(row.get("successes") or 0) > 0:
            continue
        provider = norm(row.get("providerId"))
        if not provider or int(row.get("consecutiveFailures") or 0) < rotate_every:
            continue
        outcome = str(row.get("lastOutcome") or "").strip().casefold().replace("-", "_")
        if outcome in {"profile_unavailable", "not_generated"} or row.get("executionObserved") is False:
            continue
        key = (
            provider,
            str(row.get("failureClass") or ""),
            str(row.get("signature") or ""),
        )
        state = groups.setdefault(key, {"baseVariants": set(), "finalGenerations": set()})
        variant = max(0, min(final_variant, int(row.get("experimentVariant") or 0)))
        if variant < final_variant:
            state["baseVariants"].add(variant)
        else:
            generation = max(1, int(row.get("experimentGeneration") or 1))
            if first_final_generation <= generation <= max_learning_generation:
                state["finalGenerations"].add(generation)
    expected_base = set(range(final_variant))
    expected_generations = set(range(first_final_generation, max_learning_generation + 1))
    return sorted({
        key[0]
        for key, state in groups.items()
        if expected_base.issubset(state["baseVariants"])
        and expected_generations.issubset(state["finalGenerations"])
    })

def current_handoff_rows(
    handoff_rows: dict[str, Any],
    census: dict[str, Any],
) -> tuple[dict[str, Any], list[str]]:
    """Only exact current-census LEARN handoffs may override causal ownership."""
    current_run = str(census.get("runId") or "").strip()
    current_sha = str(census.get("triggerSha") or "").strip().casefold()
    current: dict[str, Any] = {}
    stale: list[str] = []
    for raw_provider, row in handoff_rows.items():
        provider_id = norm(raw_provider)
        if (not provider_id or not isinstance(row, dict)
                or str(row.get("owner") or "") != "LEARN"
                or str(row.get("status") or "") != "pending"):
            continue
        row_run = str(row.get("sourceCensusRunId") or "").strip()
        row_sha = str(row.get("sourceCensusSha") or "").strip().casefold()
        if (current_run and re.fullmatch(r"[0-9a-f]{40}", current_sha)
                and row_run == current_run and row_sha == current_sha):
            current[provider_id] = row
        else:
            stale.append(provider_id)
    return current, sorted(set(stale))


def exhausted_handoff_repair_providers(
    handoff_rows: dict[str, Any],
    current_repair: set[str],
    info_by_id: dict[str, dict[str, Any]],
    staged_candidates: dict[str, dict[str, Any]],
) -> list[str]:
    """Treat Fast Repair's explicit exhausted-strategy handoff as architecture debt.

    The handoff registry is written from Fast Repair's own deferred/exhausted
    result, so it is stronger than inferring exhaustion from an ordinary failed
    Learning lab. Only current census Repair providers that remain LEARN-owned,
    pending, and explicitly tagged brain-strategy-exhausted qualify.
    """
    return sorted([
        provider_id
        for provider_id in unique(list(handoff_rows.keys()))
        if provider_id in current_repair
        and provider_id in info_by_id
        and provider_id in staged_candidates
        and isinstance(handoff_rows.get(provider_id), dict)
        and str(handoff_rows[provider_id].get("owner") or "") == "LEARN"
        and str(handoff_rows[provider_id].get("status") or "") == "pending"
        and str(handoff_rows[provider_id].get("reason") or "") == "brain-strategy-exhausted"
    ])


def current_repair_priority(
    exhausted: list[str],
    census: dict[str, Any],
    info_by_id: dict[str, dict[str, Any]],
    staged_candidates: dict[str, dict[str, Any]],
) -> tuple[list[str], list[str], str]:
    """Reconcile historical Repair debt with current census/observation authority."""
    raw_census_repair = census.get("repairQueue") if isinstance(census, dict) else None
    census_authoritative = isinstance(raw_census_repair, list)
    if census_authoritative:
        census_repair = [
            provider_id
            for provider_id in unique(raw_census_repair or [])
            if provider_id in info_by_id and provider_id in staged_candidates
        ]
        current = set(census_repair)
        deferred = [
            provider_id for provider_id in exhausted
            if provider_id in current
        ]
        return census_repair, deferred, "provider-census-status.json"

    deferred = [
        provider_id for provider_id in exhausted
        if provider_id in info_by_id
        and provider_id in staged_candidates
        and str(info_by_id[provider_id].get("status") or "") != "healthy"
    ]
    return list(deferred), list(deferred), "learning-current-observation-fallback"


def authoritative_learning_order(
    base_order: list[str],
    handoff_priority: list[str],
    census_repair: list[str],
    repair_deferred: list[str],
    reconstruction_required: list[str],
    info_by_id: dict[str, dict[str, Any]],
    staged_candidates: dict[str, dict[str, Any]],
) -> list[str]:
    """Put current census repair debt before broad reconstruction/backlog work.

    Learning has a finite wall-clock budget. A portfolio-wide reconstruction
    backlog must therefore never consume the slot before providers that the
    current canonical census says are broken. Historical exhausted signatures
    remain next, then clean-reconstruction debt, then ordinary queue cycling.
    """
    priority = unique([
        *handoff_priority,
        *repair_deferred,
        *census_repair,
        *reconstruction_required,
    ])
    eligible_priority = [
        provider_id
        for provider_id in priority
        if provider_id in info_by_id and provider_id in staged_candidates
    ]
    priority_set = set(eligible_priority)
    return unique([
        *eligible_priority,
        *[provider_id for provider_id in base_order if provider_id not in priority_set],
    ])


def brain_owned_current_repair_providers(
    batch_plan: dict[str, Any],
    census: dict[str, Any],
) -> tuple[list[str], str]:
    """Resolve current Brain ownership from the exact causal execution plan.

    The repairQueue is a symptom queue, not an execution owner list. Learning
    only owns rows routed to BRAIN_LEARNING by the current batch/census pair.
    Stale causal provenance fails closed to zero automatic ownership.
    """
    plan = build_provider_execution_plan(batch_plan, census)
    if plan.get("sourceCensusConsistent") is not True:
        return [], "provider-execution-plan-stale-fail-closed"
    current_repair = {
        norm(value) for value in census.get("repairQueue") or [] if norm(value)
    }
    owned: list[str] = []
    for row in plan.get("executions") or []:
        if not isinstance(row, dict):
            continue
        if str(row.get("lane") or "") != "BRAIN_LEARNING":
            continue
        if row.get("dispatchAllowed") is not True:
            continue
        for value in row.get("providers") or []:
            provider_id = norm(value)
            if provider_id in current_repair and provider_id not in owned:
                owned.append(provider_id)
    return owned, "current-census-causal-execution-plan"


def repair_learning_scope(
    order: list[str],
    explicit_cohort: list[str],
    handoff_priority: list[str],
    brain_owned_repair: list[str],
    info_by_id: dict[str, dict[str, Any]],
    staged_candidates: dict[str, dict[str, Any]],
) -> list[str]:
    """Bound family-first Learning to providers currently owned by Brain.

    Explicit cohorts remain exact. Otherwise current causal Brain ownership is
    combined only with an explicit current Fast-Repair -> LEARN handoff. Durable
    negative memory may change strategy ordering but cannot steal ownership
    from REMAT/FAST/CORE_CLIENT lanes.
    """
    requested = unique(
        explicit_cohort
        if explicit_cohort
        else [*handoff_priority, *brain_owned_repair]
    )
    eligible = [
        provider_id for provider_id in requested
        if provider_id in info_by_id and provider_id in staged_candidates
    ]
    allowed = set(eligible)
    return unique([
        *[provider_id for provider_id in order if provider_id in allowed],
        *[provider_id for provider_id in eligible if provider_id not in order],
    ])


def candidate_map(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        norm(row.get("canonical_id") or row.get("upstream_id")): row
        for row in registry.get("candidates") or []
        if isinstance(row, dict) and norm(row.get("canonical_id") or row.get("upstream_id"))
    }

def targeted_registry(full: dict[str, Any], provider_id: str) -> dict[str, Any]:
    rows = candidate_map(full)
    if provider_id not in rows:
        raise ValueError(f"provider absent from staging: {provider_id}")
    out = copy.deepcopy(full)
    out["candidates"] = [copy.deepcopy(rows[provider_id])]
    out["candidate_count"] = 1
    out["canonical_provider_count"] = 1
    out["learning_target_provider"] = provider_id
    return out

def merge_target_candidate(full_registry_path: Path, target_registry_path: Path, provider_id: str) -> None:
    full = load_json(full_registry_path, {})
    target = load_json(target_registry_path, {})
    final = candidate_map(target).get(provider_id)
    if not final:
        return
    rows = []
    replaced = False
    for row in full.get("candidates") or []:
        if isinstance(row, dict) and norm(row.get("canonical_id") or row.get("upstream_id")) == provider_id:
            rows.append(copy.deepcopy(final))
            replaced = True
        else:
            rows.append(row)
    if not replaced:
        rows.append(copy.deepcopy(final))
    full["candidates"] = rows
    full["candidate_count"] = len(rows)
    full["canonical_provider_count"] = len({norm(x.get("canonical_id") or x.get("upstream_id")) for x in rows if isinstance(x, dict)})
    write_json(full_registry_path, full)

def remaining_seconds(deadline: float, reserve: float = 0.0) -> int:
    return max(1, int(deadline - time.time() - reserve))


def terminate_process_group(
    process: subprocess.Popen[str],
    *,
    grace_seconds: float = 2.0,
) -> None:
    """Terminate the whole spawned tree, not only its Python/Node parent."""
    if process.poll() is not None:
        return
    try:
        if os.name == "posix":
            os.killpg(process.pid, signal.SIGTERM)
        else:
            process.terminate()
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=grace_seconds)
        return
    except subprocess.TimeoutExpired:
        pass
    try:
        if os.name == "posix":
            os.killpg(process.pid, signal.SIGKILL)
        else:
            process.kill()
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=grace_seconds)
    except subprocess.TimeoutExpired:
        process.kill()


def run(cmd: list[str], *, env: dict[str, str] | None, deadline: float, cwd: Path = ROOT, allow_fail: bool = False) -> subprocess.CompletedProcess[str]:
    timeout = remaining_seconds(deadline, 1)
    process = subprocess.Popen(
        cmd,
        cwd=cwd,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=(os.name == "posix"),
    )
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired as error:
        terminate_process_group(process)
        try:
            stdout, stderr = process.communicate(timeout=3)
        except subprocess.TimeoutExpired:
            terminate_process_group(process, grace_seconds=0.5)
            stdout, stderr = process.communicate(timeout=3)
        sys.stdout.write(stdout or "")
        sys.stderr.write(stderr or "")
        raise BudgetExhausted(
            f"Learning work budget exhausted while running: {' '.join(cmd[:4])}"
        ) from error
    completed = subprocess.CompletedProcess(
        cmd,
        int(process.returncode or 0),
        stdout or "",
        stderr or "",
    )
    sys.stdout.write(completed.stdout)
    sys.stderr.write(completed.stderr)
    if completed.returncode != 0 and not allow_fail:
        raise RuntimeError(f"command failed ({completed.returncode}): {' '.join(cmd[:4])}")
    return completed

def route_evidence_count(value: Any) -> int:
    if isinstance(value, list):
        return sum(route_evidence_count(item) for item in value)
    if not isinstance(value, dict):
        return 0
    count = 0
    for key, child in value.items():
        lowered = str(key).casefold()
        if lowered in {"official_site", "site_final_url", "validated_api", "terminal_url", "resolved_domain"} and child:
            count += 1
        elif lowered in {"site_candidates", "api_candidates", "terminal_candidates"} and isinstance(child, list):
            count += len(child)
        if isinstance(child, (dict, list)):
            count += route_evidence_count(child)
    return count


def route_search(provider_id: str, run_dir: Path, deadline: float) -> dict[str, Any]:
    hub_report = run_dir / "provider-hub-report.json"
    fallback_report = run_dir / "provider-hub-search-fallback.json"
    base = [
        sys.executable, str(SCRIPTS / "resolve_provider_hubs.py"),
        "--apply", "--mode", "deep", "--include-disabled", "--search-disabled",
        "--provider", provider_id, "--workers", "1", "--timeout", "8",
        "--output", str(hub_report),
    ]
    first = run(base, env=os.environ.copy(), deadline=deadline, allow_fail=True)
    fallback = run([
        sys.executable, str(SCRIPTS / "resolve_provider_hub_search_fallback.py"),
        "--report", str(hub_report), "--output", str(fallback_report),
        "--apply", "--max-providers", "1", "--timeout", "8",
    ], env=os.environ.copy(), deadline=deadline, allow_fail=True)
    payload = load_json(fallback_report, {})
    hub_payload = load_json(hub_report, {})
    return {
        "resolverStatus": first.returncode,
        "fallbackStatus": fallback.returncode,
        "fallbackApplied": int(payload.get("applied") or 0),
        "routeEvidenceCount": route_evidence_count(hub_payload) + route_evidence_count(payload),
    }

def refresh_stage_routes(stage: Path, deadline: float, provider_id: str) -> dict[str, Any]:
    # Route discovery can rotate a provider terminal. Reconcile provider-owned
    # metadata/config bytes before reapplying runtime profiles, exactly as the
    # canonical Domain Refresh lane does. A provider-local refresh failure is
    # evidence about that provider, not a reason to abort the whole Learning
    # superset: return a structured blocker so the queue can persist/retry it.
    steps = (
        ("domain_metadata_reconcile", [sys.executable, str(SCRIPTS / "reconcile_provider_domain_metadata.py"), "--rebuild", "--provider", provider_id]),
        ("runtime_profile_reapply", [sys.executable, str(SCRIPTS / "build_provider_runtime_profiles.py"), "--stage", str(stage), "--apply-stage", "--provider", provider_id]),
        ("terminal_quarantine_normalize", [sys.executable, str(SCRIPTS / "normalize_terminal_quarantine_stage.py"), "--stage", str(stage)]),
        ("override_pipeline_validate", [sys.executable, str(SCRIPTS / "validate_override_pipeline.py"), "--stage", str(stage), "--provider", provider_id]),
    )
    for step, cmd in steps:
        completed = run(cmd, env=os.environ.copy(), deadline=deadline, allow_fail=True)
        if completed.returncode != 0:
            result = {
                "ok": False,
                "provider": provider_id,
                "step": step,
                "returncode": int(completed.returncode),
            }
            print(
                "FIELD_BRAIN_PROVIDER_REFRESH_ISOLATED "
                f"provider={provider_id} step={step} returncode={completed.returncode}"
            )
            return result
    return {"ok": True, "provider": provider_id, "step": "complete", "returncode": 0}


def route_refresh_with_budget_scope(
    provider_id: str,
    run_dir: Path,
    stage: Path,
    provider_deadline: float,
    work_deadline: float,
    fair_handoff: bool,
    *,
    route_search_fn: Any | None = None,
    refresh_fn: Any | None = None,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    """Keep a provider fair-share timeout local while preserving true global exhaustion."""
    search = route_search if route_search_fn is None else route_search_fn
    refresh = refresh_stage_routes if refresh_fn is None else refresh_fn
    route: dict[str, Any] | None = None
    try:
        route = search(provider_id, run_dir, provider_deadline)
        return route, refresh(stage, provider_deadline, provider_id)
    except BudgetExhausted:
        # When min(work_deadline, now+slice) selected the global deadline,
        # this is a real phase exhaustion and must retain the outer fail-closed
        # persistence semantics. Only a strictly earlier fair-share deadline
        # is provider-local.
        if not fair_handoff or provider_deadline >= work_deadline:
            raise
        return route, {
            "ok": False,
            "provider": provider_id,
            "step": "fair_share_route_refresh",
            "returncode": 124,
            "sliceExhausted": True,
            "proofAuthority": False,
        }

def _semantic_type(value: Any) -> str:
    value = norm(value)
    if value == "anime" or value.startswith("anim"):
        return "anime"
    if value in {"tv", "series", "serie", "show"}:
        return "tv"
    if value in {"movie", "film"}:
        return "movie"
    return ""


def authoritative_declared_types(
    provider_id: str,
    candidate: dict[str, Any],
    *,
    manifest: dict[str, Any] | None = None,
    census: dict[str, Any] | None = None,
) -> list[str]:
    """Resolve Learning fixture types from catalogue authority, never a movie default."""
    wanted = norm(provider_id)
    manifest = manifest if isinstance(manifest, dict) else load_json(ROOT / "manifest.json", {})
    for row in manifest.get("scrapers") or []:
        if not isinstance(row, dict) or norm(row.get("id")) != wanted:
            continue
        raw = row.get("types") or row.get("supportedTypes") or row.get("supported_types") or []
        if isinstance(raw, str):
            raw = [raw]
        values = unique([_semantic_type(value) for value in raw if _semantic_type(value)])
        if values:
            return values

    census = census if isinstance(census, dict) else load_json(
        ROOT / "automation" / "provider-census-status.json",
        {},
    )
    for row in census.get("providers") or []:
        if not isinstance(row, dict) or norm(row.get("provider")) != wanted:
            continue
        raw = row.get("declaredLanes") or []
        if isinstance(raw, str):
            raw = [raw]
        values = unique([_semantic_type(value) for value in raw if _semantic_type(value)])
        if values:
            return values

    metadata = candidate.get("metadata") if isinstance(candidate.get("metadata"), dict) else {}
    raw = metadata.get("supportedTypes") or metadata.get("types") or []
    if isinstance(raw, str):
        raw = [raw]
    return unique([_semantic_type(value) for value in raw if _semantic_type(value)])


def declared_type(
    provider_id: str,
    candidate: dict[str, Any],
    *,
    manifest: dict[str, Any] | None = None,
    census: dict[str, Any] | None = None,
) -> str:
    values = authoritative_declared_types(
        provider_id,
        candidate,
        manifest=manifest,
        census=census,
    )
    if not values:
        raise ValueError(
            f"Learning provider {norm(provider_id) or '<unknown>'} has no authoritative declared media type"
        )
    # Providers that explicitly support anime + episodic TV but not ordinary
    # movies must be exercised with anime identity/season semantics.
    if "anime" in values and "movie" not in values:
        return "anime"
    return values[0]


def choose_fixture(config: dict[str, Any], provider_state: dict[str, Any], media_type: str) -> dict[str, Any]:
    fixtures = config.get("fixtures") if isinstance(config.get("fixtures"), dict) else {}
    pool = fixtures.get(media_type) if isinstance(fixtures.get(media_type), list) else []
    if not pool:
        raise ValueError(f"health-config contains no Learning fixtures for declared type: {media_type}")
    cursors = provider_state.setdefault("fixtureCursor", {})
    index = int(cursors.get(media_type) or 0) % len(pool)
    fixture = copy.deepcopy(pool[index])
    fixture_type = _semantic_type(fixture.get("mediaType"))
    if fixture_type != media_type:
        raise ValueError(
            f"Learning fixture type mismatch: declared={media_type} fixture={fixture_type or '<missing>'}"
        )
    cursors[media_type] = (index + 1) % len(pool)
    return fixture

def summarize_lab(report: dict[str, Any], provider_id: str, fixture: dict[str, Any]) -> dict[str, Any]:
    row = next((x for x in report.get("providers") or [] if norm(x.get("id")) == provider_id), None) or {}
    clients: dict[str, Any] = {}
    unresolved = False
    for name, value in (row.get("clients") or {}).items():
        if not isinstance(value, dict):
            continue
        verdict = str(value.get("verdict") or "no_report")
        playable = int(value.get("playable_probe_count") or 0)
        unplayable = int(value.get("unplayable_probe_count") or 0)
        inconclusive = int(value.get("inconclusive_probe_count") or 0)
        contradictions = int(value.get("identity_contradiction_count") or 0)
        complete = bool(value.get("probe_coverage_complete"))
        hidden_failure = verdict != "playable" or unplayable > 0 or inconclusive > 0 or contradictions > 0 or not complete
        unresolved = unresolved or hidden_failure
        clients[name] = {
            "verdict": verdict,
            "runtimeStreams": int(value.get("runtime_stream_count") or 0),
            "probedStreams": int(value.get("probed_stream_count") or 0),
            "playableProbes": playable,
            "unplayableProbes": unplayable,
            "inconclusiveProbes": inconclusive,
            "identityContradictions": contradictions,
            "identityStatus": str(value.get("identity_status") or "unknown"),
            "probeCoverageComplete": complete,
            "hiddenFailure": hidden_failure,
        }
    return {
        "providerId": provider_id,
        "status": "unresolved" if unresolved else "playable",
        "fixtureSlug": str(fixture.get("label") or fixture.get("title") or fixture.get("tmdbId") or ""),
        "firstDeclaredType": str(fixture.get("mediaType") or ""),
        "clients": clients,
        "coreIsAuthoritative": False,
        "sandboxCandidate": bool(row.get("sandbox_candidate")),
        "allReturnedStreams": all(bool(x.get("probeCoverageComplete")) for x in clients.values()) if clients else False,
    }

def requires_full_variant_probe(plan: dict[str, Any] | None) -> bool:
    """Return true only for Learning experiments whose causal debt is variant loss."""
    if not isinstance(plan, dict):
        return False
    failure = str(plan.get("failureClass") or "").strip().casefold()
    group = str(plan.get("groupId") or plan.get("causalGroup") or "").strip().casefold()
    stage = str(plan.get("observedPipelineStage") or "").strip().casefold()
    return (
        failure == "variant_coverage_gap"
        or group.startswith("variant-coverage|")
        or stage in {"variant_coverage_gap", "variant-coverage"}
    )


def learning_stream_probe_policy(stream_cap: int, full_variant_probe: bool) -> tuple[int, bool]:
    """Keep ordinary Learning cheap, but never study variant debt through two streams."""
    bounded = max(1, min(int(stream_cap), 40))
    if full_variant_probe:
        return bounded, True
    return min(bounded, 2), False


def run_lab(
    session: LearningLabSession,
    provider_id: str,
    registry_path: Path,
    stage: Path,
    fixture: dict[str, Any],
    run_dir: Path,
    deadline: float,
    stream_cap: int,
    full_variant_probe: bool = False,
) -> dict[str, Any]:
    report_path = run_dir / "targeted-lab.json"
    markdown_path = run_dir / "targeted-lab.md"
    stream_probe_cap, probe_all_streams = learning_stream_probe_policy(
        stream_cap,
        full_variant_probe,
    )
    config: dict[str, Any] = {
        "providers": provider_id,
        "clients": ["tv", "desktop", "mobile"],
        "stage": str(stage),
        "registry": str(registry_path),
        "fixture": {
            "tmdbId": str(fixture.get("tmdbId") or ""),
            "mediaType": str(fixture.get("mediaType") or "movie"),
            "title": str(fixture.get("title") or fixture.get("label") or ""),
            "year": fixture.get("year"),
            "season": fixture.get("season"),
            "episode": fixture.get("episode"),
        },
        "provider_timeout_ms": 12000,
        "retry_provider_timeouts": False,
        "max_settings_profiles": 1,
        "max_streams_per_runtime": stream_probe_cap,
        "probe_all_streams": probe_all_streams,
        "all_streams_safety_cap": stream_probe_cap if probe_all_streams else 40,
        "playback_timeout_ms": 5000,
        "stream_sampling": "spread",
        "provider_concurrency": 1,
        "max_fetches": 18,
        "max_distinct_hosts": 12,
        "max_redirects": 4,
    }
    response = session.request({"action": "run", "config": config}, deadline=deadline)
    payload = response.get("report") if isinstance(response.get("report"), dict) else {"providers": []}
    write_json(report_path, payload)
    markdown_path.write_text(str(response.get("markdown") or ""), encoding="utf-8")
    summary = summarize_lab(payload, provider_id, fixture)
    summary["commandStatus"] = 0
    summary["labMode"] = "learning-quick"
    summary["warmSession"] = True
    summary["providerTimeoutMs"] = 12000
    summary["playbackTimeoutMs"] = 5000
    summary["streamProbeCap"] = stream_probe_cap
    summary["probeAllStreams"] = probe_all_streams
    summary["variantCoverageProbe"] = bool(full_variant_probe)
    return summary

def repair_method_fingerprints(report: dict[str, Any], attempted_profiles: list[str]) -> list[str]:
    """Identify one causal Learning method beyond the coarse profile name.

    Adaptive recovery deliberately reuses the same profile while the Brain rotates
    experiment variants/generations. Comparing only profile names makes every
    later hypothesis look identical and prematurely stops same-run Learning.
    """
    output: list[str] = []
    plans = (report.get("brain") or {}).get("plans") if isinstance(report.get("brain"), dict) else {}
    if isinstance(plans, dict):
        for plan in plans.values():
            if not isinstance(plan, dict):
                continue
            provider_id = norm(plan.get("providerId"))
            signature = str(plan.get("signature") or plan.get("failureClass") or "").strip()
            generation = max(1, int(plan.get("experimentGeneration") or 1))
            variant = max(0, int(plan.get("experimentVariant") or 0))
            profiles = sorted({str(value) for value in plan.get("allowedProfiles") or [] if str(value)})
            if str(plan.get("action") or "") != "probe-targeted-repair" or not profiles:
                continue
            if provider_id or signature:
                output.append(
                    f"{provider_id}|{signature}|g{generation}|v{variant}|{','.join(profiles)}"
                )
    if not output:
        output = [f"profile:{value}" for value in attempted_profiles if str(value)]
    return sorted(set(output))


def learning_preferred_env(profile: str = "", failure_class: str = "") -> dict[str, str]:
    profile = str(profile or "").strip().casefold()
    failure_class = str(failure_class or "").strip().casefold()
    if bool(profile) != bool(failure_class):
        raise ValueError("Learning preferred strategy requires profile and causal failure class together")
    if not profile:
        return {}
    if not re.fullmatch(r"[a-z][a-z0-9_]*_v[0-9]+", profile):
        raise ValueError("invalid Learning preferred profile")
    if not re.fullmatch(r"[a-z][a-z0-9_]{0,95}", failure_class):
        raise ValueError("invalid Learning preferred failure class")
    return {
        "NUVIO_BRAIN_LEARNING_PREFERRED_PROFILE": profile,
        "NUVIO_BRAIN_LEARNING_PREFERRED_FAILURE_CLASS": failure_class,
    }


def repair_attempt(
    provider_id: str,
    stage: Path,
    registry_path: Path,
    output: Path,
    previous_state_path: Path,
    deadline: float,
    *,
    preferred_profile: str = "",
    preferred_failure_class: str = "",
    causal_failure_class: str = "",
) -> dict[str, Any]:
    env = os.environ.copy()
    env["NUVIO_BRAIN_TARGET_PROVIDER"] = provider_id
    preferred = learning_preferred_env(preferred_profile, preferred_failure_class)
    env.update(preferred)
    causal_failure_class = str(causal_failure_class or "").strip().casefold()
    if causal_failure_class:
        if not re.fullmatch(r"[a-z][a-z0-9_]{0,95}", causal_failure_class):
            raise ValueError("invalid Learning causal failure class")
        env["NUVIO_BRAIN_LEARNING_CAUSAL_FAILURE_CLASS"] = causal_failure_class
        print(
            "FIELD_BRAIN_LEARNING_CAUSAL_HANDOFF "
            f"provider={provider_id} failure={causal_failure_class} "
            "proof_authority=false mutation_authority=false",
            flush=True,
        )
    if preferred:
        print(
            "FIELD_BRAIN_LEARNING_PREFERRED_HANDOFF "
            f"provider={provider_id} profile={preferred['NUVIO_BRAIN_LEARNING_PREFERRED_PROFILE']} "
            f"failure={preferred['NUVIO_BRAIN_LEARNING_PREFERRED_FAILURE_CLASS']} "
            "proof_authority=false",
            flush=True,
        )
    env["NUVIO_BRAIN_LEARNING_STATE"] = str(previous_state_path)
    # The child planner imports brain_repair_runtime before sandbox main() runs,
    # so the previous sanitized Learning state must be present in the process
    # environment at spawn time. This is Learning-only memory; production Repair
    # still reads automation/brain-repair-memory.json.
    env["NIAKVIO_BRAIN_LEARNING_MEMORY"] = str(previous_state_path)
    env["NUVIO_BRAIN_DEADLINE_EPOCH_MS"] = str(int(deadline * 1000))
    env["NUVIO_WORKER_MEMORY_MB"] = "1024"
    baseline_registry = load_json(registry_path, {})
    baseline_counts: dict[str, int] = {}
    for candidate in baseline_registry.get("candidates") or []:
        if not isinstance(candidate, dict):
            continue
        key = str(candidate.get("key") or "")
        if not key:
            continue
        count = sum(
            1
            for event in candidate.get("repair_history") or []
            if isinstance(event, dict) and event.get("accepted")
        )
        if count:
            baseline_counts[key] = count
    history_baseline_path = output / "repair-history-baseline.json"
    write_json(history_baseline_path, baseline_counts)

    completed = run([
        sys.executable, str(SCRIPTS / "run_brain_learning_sandbox.py"),
        "--stage", str(stage), "--registry", str(registry_path),
        "--output", str(output), "--max-rounds", "0",
    ], env=env, deadline=deadline, allow_fail=True)
    health_path = output / "health-results.json"
    repair_path = output / "repair-report.json"
    report = load_json(repair_path, {})
    attempted = sorted({
        str(a.get("profile") or "")
        for x in report.get("rounds") or [] if isinstance(x, dict)
        for a in x.get("attempts") or [] if isinstance(a, dict) and str(a.get("profile") or "")
    })
    methods = repair_method_fingerprints(report, attempted)

    # A Learning child is exploratory evidence, never an authority boundary.
    # If it crashes or fails to materialize its final validation artifacts,
    # restore the exact targeted registry baseline and record a rejected attempt
    # instead of aborting the whole causal-family cohort. This prevents partial
    # candidate bytes/history from leaking into the full Learning staging tree.
    incomplete_reasons: list[str] = []
    if completed.returncode != 0:
        incomplete_reasons.append(f"child_return_code_{completed.returncode}")
    if not health_path.is_file():
        incomplete_reasons.append("missing_health_results")
    if not repair_path.is_file():
        incomplete_reasons.append("missing_repair_report")
    if incomplete_reasons:
        write_json(registry_path, baseline_registry)
        reason = ",".join(incomplete_reasons)
        print(
            "FIELD_BRAIN_LEARNING_REPAIR_CHILD_REJECTED "
            f"provider={provider_id} reason={reason} rollback=true",
            flush=True,
        )
        return {
            "returnCode": completed.returncode,
            "accepted": 0,
            "attemptedProfiles": attempted,
            "attemptedMethods": methods,
            "report": report,
            "validationStatus": "rejected_incomplete_child",
            "validationReason": reason,
        }

    # Validate accepted repairs against the exact targeted registry before the
    # candidate is merged back into the full Learning staging tree. A validator
    # rejection is evidence about this experiment, not permission to abort all
    # unrelated Learning providers; roll the targeted registry back fail-closed.
    try:
        run([
            sys.executable, str(SCRIPTS / "validate_automatic_repair_results.py"),
            "--stage", str(registry_path.parent),
            "--health", str(health_path),
            "--repairs", str(repair_path),
            "--history-baseline", str(history_baseline_path),
        ], env=env, deadline=deadline)
    except RuntimeError as error:
        write_json(registry_path, baseline_registry)
        print(
            "FIELD_BRAIN_LEARNING_REPAIR_CHILD_REJECTED "
            f"provider={provider_id} reason=validator_rejected rollback=true",
            flush=True,
        )
        return {
            "returnCode": completed.returncode,
            "accepted": 0,
            "attemptedProfiles": attempted,
            "attemptedMethods": methods,
            "report": report,
            "validationStatus": "rejected_validator",
            "validationReason": str(error)[:320],
        }

    accepted = sum(len(x.get("accepted") or []) for x in report.get("rounds") or [] if isinstance(x, dict))
    return {
        "returnCode": completed.returncode,
        "accepted": accepted,
        "attemptedProfiles": attempted,
        "attemptedMethods": methods,
        "report": report,
        "validationStatus": "validated",
        "validationReason": "",
    }

def source_contract_provider_states(
    order: list[str],
    frontier: set[str] | dict[str, Any],
    parser_installed: bool,
    resolver_frontier: set[str] | dict[str, Any] | None = None,
    resolver_installed: bool = False,
    player_target_frontier: set[str] | dict[str, Any] | None = None,
) -> dict[str, str]:
    """Return one monotone source-contract state per provider.

    Installed parser/resolver capabilities are global code facts, while evidence
    depth is provider-local. Never let one representative's deeper frontier
    advance or rewind a sibling in the same Learning cohort.
    """
    resolver_frontier = resolver_frontier or set()
    player_target_frontier = player_target_frontier or set()
    states: dict[str, str] = {}
    for provider_id in order:
        if provider_id not in frontier:
            continue
        if not parser_installed:
            states[provider_id] = "new_family_required"
        elif provider_id in player_target_frontier and resolver_installed:
            states[provider_id] = "player_target_observed"
        elif provider_id in resolver_frontier and not resolver_installed:
            states[provider_id] = "resolver_family_required"
        elif provider_id in resolver_frontier and resolver_installed:
            states[provider_id] = "resolver_installed_replay_required"
        else:
            states[provider_id] = "parser_installed_replay_required"
    return states


def source_contract_capability_state(
    order: list[str],
    frontier: set[str] | dict[str, Any],
    parser_installed: bool,
    resolver_frontier: set[str] | dict[str, Any] | None = None,
    resolver_installed: bool = False,
    player_target_frontier: set[str] | dict[str, Any] | None = None,
) -> tuple[list[str], list[str], str]:
    states = source_contract_provider_states(
        order,
        frontier,
        parser_installed,
        resolver_frontier,
        resolver_installed,
        player_target_frontier,
    )
    if not states:
        return [], [], "not_attested"
    deferred_states = {"new_family_required", "resolver_family_required"}
    deferred = [pid for pid in order if states.get(pid) in deferred_states]
    replay = [pid for pid in order if pid in states and pid not in set(deferred)]
    distinct = sorted(set(states.values()))
    status = distinct[0] if len(distinct) == 1 else "mixed_source_contract_frontier"
    return deferred, replay, status


def defer_new_source_contract_family(
    provider_id: str,
    state: dict[str, Any],
    info: dict[str, Any],
    queue: dict[str, Any],
) -> dict[str, Any]:
    """Preserve a new source-contract family as debt without legacy executor work."""
    provider_states = queue.get("sourceContractProviderStates")
    status = str(
        (provider_states.get(provider_id) if isinstance(provider_states, dict) else "")
        or queue.get("sourceContractFamilyExecutableStatus")
        or "new_family_required"
    )
    resolver_debt = status == "resolver_family_required"
    state["lastStatus"] = (
        "new_source_resolver_executable_required"
        if resolver_debt else "new_source_family_executable_required"
    )
    state["lastAttemptAt"] = datetime.now(timezone.utc).isoformat()
    queue["pendingProviders"] = [
        pid for pid in queue.get("pendingProviders") or []
        if pid != provider_id
    ]
    queue["completedInCycle"] = unique([
        *(queue.get("completedInCycle") or []), provider_id,
    ])
    return {
        "provider": provider_id,
        "coreHypothesis": info,
        "routeSearch": None,
        "routeRefresh": None,
        "resolved": False,
        "attempts": [],
        "finalLab": None,
        "sourceContractFamilyStatus": status,
        "independentSourceEvidenceNotNativePlayback": True,
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--stage", type=Path, default=ROOT / "staging")
    p.add_argument("--health", type=Path, default=ROOT / "health-report.json")
    p.add_argument("--previous-state", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--provider", default="")
    p.add_argument("--provider-filter", default="", help="Explicit, comma-separated Learning cohort from the caller; never silently narrow it to family representatives.")
    p.add_argument("--budget-minutes", type=int, default=60)
    p.add_argument("--reserve-minutes", type=int, default=5)
    p.add_argument("--stream-safety-cap", type=int, default=40)
    args = p.parse_args()

    stage = args.stage.resolve()
    full_registry_path = stage / "candidates.json"
    full_registry = load_json(full_registry_path, {})
    previous = load_json(args.previous_state.resolve(), {})
    health = load_json(args.health.resolve(), {})
    health_config = load_json(ROOT / "health-config.json", {})
    manifest_authority = load_json(ROOT / "manifest.json", {})
    census_authority = load_json(ROOT / "automation" / "provider-census-status.json", {})
    # A diagnostic from an independent GitHub runner is usable to *defer*
    # an unrelated legacy Core executor only with the same official TV
    # source/run/fixture and currently materialized JS bytes. It never proves
    # NuvioTV playback, identity, or permission to mutate.
    source_history = load_json(
        ROOT / "automation" / "brain-catalogue-source-probe-history.json", {}
    )
    native_history = load_json(
        ROOT / "automation" / "brain-android-tv-emulator-history.json", {}
    )
    source_contract_frontier = attested_source_contract_frontier(
        source_history, native_history, manifest_authority, ROOT,
    )
    source_resolver_frontier = attested_source_resolver_frontier(
        source_history, native_history, manifest_authority, ROOT,
    )
    source_player_target_frontier = attested_source_player_target_frontier(
        source_history, native_history, manifest_authority, ROOT,
    )
    source_player_structures = attested_source_player_structure_frontier(
        source_history, native_history, manifest_authority, ROOT,
    )
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)

    order, info_by_id, queue = build_queue(health, previous, args.provider)

    staged_candidates = candidate_map(full_registry)
    explicit_cohort = unique([
        norm(item) for item in args.provider_filter.split(",") if item.strip()
    ])
    if explicit_cohort:
        bad = [provider_id for provider_id in explicit_cohort
               if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,95}", provider_id)]
        if bad:
            raise ValueError("invalid explicit Learning cohort provider: " + ",".join(bad))
        if args.provider and norm(args.provider) not in explicit_cohort:
            raise ValueError("single Learning target is outside explicit cohort")
        unavailable = [
            provider_id for provider_id in explicit_cohort
            if provider_id not in staged_candidates or provider_id not in info_by_id
        ]
        if unavailable:
            raise ValueError(
                "explicit Learning cohort lacks current staged/health evidence: "
                + ",".join(unavailable)
            )
    memory_exhausted = exhausted_repair_providers(
        load_json(ROOT / "automation" / "brain-repair-memory.json", {}),
        load_json(ROOT / "engine_v2" / "config" / "brain-policy.json", {}),
    )
    census_repair, repair_deferred, census_repair_authority = current_repair_priority(
        memory_exhausted,
        load_json(ROOT / "automation" / "provider-census-status.json", {}),
        info_by_id,
        staged_candidates,
    )
    handoff_state = load_json(ROOT / "automation" / "provider-repair-learn-handoff-v1.json", {})
    handoff_rows = handoff_state.get("providers") if isinstance(handoff_state.get("providers"), dict) else {}
    current_handoff, stale_handoff = current_handoff_rows(handoff_rows, census_authority)
    current_repair_set = set(census_repair)
    handoff_exhausted = exhausted_handoff_repair_providers(
        current_handoff,
        current_repair_set,
        info_by_id,
        staged_candidates,
    )
    # Negative experiment memory can be sparse or absent on the publication
    # branch. Only an exact-current-census explicit handoff may override the
    # causal execution owner; legacy rows remain historical prior only.
    repair_deferred = unique([*repair_deferred, *handoff_exhausted])
    handoff_priority = [
        provider_id
        for provider_id in unique(list(current_handoff.keys()))
        if provider_id in current_repair_set
        and provider_id in info_by_id
        and provider_id in staged_candidates
        and isinstance(current_handoff.get(provider_id), dict)
        and str(current_handoff[provider_id].get("owner") or "") == "LEARN"
        and str(current_handoff[provider_id].get("status") or "") == "pending"
    ]
    # Current census evidence outranks historical experiment debt. A provider
    # that recovered to FULL/PARTIAL must not be reopened solely because an old
    # signature exhausted its variants. Conversely every current Repair target
    # deserves early Learning attention even before all variants are exhausted.
    repair_deferred_set = set(repair_deferred)
    if not args.provider and repair_deferred:
        # New Repair evidence reopens a provider even if an older Learning cycle
        # had already marked it complete. This is new-strategy debt, not a retry
        # of the same exhausted Core experiment.
        queue["completedInCycle"] = [
            provider_id for provider_id in queue.get("completedInCycle") or []
            if provider_id not in repair_deferred_set
        ]
        order = [
            *repair_deferred,
            *[provider_id for provider_id in order if provider_id not in repair_deferred_set],
        ]
    reconstruction_required = sorted(
        provider_id
        for provider_id, candidate in staged_candidates.items()
        if candidate.get("provider_base_reconstruction_required") is True
    )
    reconstruction_required_set = set(reconstruction_required)
    if not args.provider:
        # The canonical current census is the first Learning authority. Broad
        # clean-reconstruction debt is important, but it must not starve current
        # broken providers inside a finite Learning slot.
        order = authoritative_learning_order(
            order,
            handoff_priority,
            census_repair,
            repair_deferred,
            reconstruction_required,
            info_by_id,
            staged_candidates,
        )

    batch_plan = load_json(ROOT / "automation" / "provider-repair-batch-plan-latest.json", {})
    brain_owned_repair, brain_owner_authority = brain_owned_current_repair_providers(
        batch_plan, census_authority
    )
    causal_group_order: list[str] = []
    learning_scope = repair_learning_scope(
        order,
        explicit_cohort,
        handoff_priority,
        brain_owned_repair,
        info_by_id,
        staged_candidates,
    )

    # Current Repair debt is the bounded execution scope. The broad catalogue
    # remains observable Learning backlog, but it cannot dilute a repair phase
    # into one provider-local family per catalogue entry.
    fair_handoff = bool(learning_scope) and not bool(args.provider)
    portfolio_deferred = [
        provider_id for provider_id in order if provider_id not in set(learning_scope)
    ] if fair_handoff else []
    full_handoff_order = list(learning_scope)
    family_frontier: list[str] = []
    family_deferred: list[str] = []
    if fair_handoff:
        scoped_order, causal_group_order = causal_batch_round_robin(
            full_handoff_order, batch_plan
        )
        family_frontier, family_deferred = causal_family_frontier(
            scoped_order, batch_plan, info_by_id
        )
        # Execute one independently chosen oracle per current repair family.
        # Siblings remain pending for canonical Repair/next Learning and the
        # portfolio backlog is untouched by this repair-focused phase.
        order = family_frontier

    queue["explicitLearningCohort"] = explicit_cohort
    queue["explicitLearningCohortCount"] = len(explicit_cohort)
    queue["brainOwnedCurrentRepairProviders"] = brain_owned_repair
    queue["brainOwnedCurrentRepairProviderCount"] = len(brain_owned_repair)
    queue["brainOwnedCurrentRepairAuthority"] = brain_owner_authority
    queue["repairLearningScopeProviders"] = learning_scope
    queue["repairLearningScopeProviderCount"] = len(learning_scope)
    queue["repairLearningScopePolicy"] = (
        "explicit-cohort-current-debt-only"
        if explicit_cohort else "current-causal-brain-owner-plus-explicit-learn-handoff"
    )
    queue["repairLearningDeferredPortfolioProviders"] = portfolio_deferred
    queue["repairLearningDeferredPortfolioProviderCount"] = len(portfolio_deferred)
    queue["fastRepairHandoffProviders"] = handoff_priority
    queue["fastRepairHandoffProviderCount"] = len(handoff_priority)
    queue["staleRepairHandoffProviders"] = stale_handoff
    queue["staleRepairHandoffProviderCount"] = len(stale_handoff)
    queue["repairHandoffFreshnessAuthority"] = "exact-current-census-run-and-sha"
    queue["fastRepairHandoffAuthority"] = "provider-repair-learn-handoff-v1.json"
    queue["fastRepairExhaustedHandoffProviders"] = handoff_exhausted
    queue["fastRepairExhaustedHandoffProviderCount"] = len(handoff_exhausted)
    queue["fastRepairHandoffCausalBatchOrder"] = causal_group_order
    queue["fastRepairHandoffCausalBatchCount"] = len(causal_group_order)
    queue["fastRepairHandoffOrderingPolicy"] = "causal-batch-round-robin"
    # Keep the current-repair family wave map for observability even though
    # this phase executes only the first representative frontier.
    causal_waves = causal_family_waves(full_handoff_order, batch_plan, max_parallel=4) if fair_handoff else []
    queue["fastRepairHandoffCausalWaves"] = causal_waves
    queue["fastRepairHandoffCausalWaveCount"] = len(causal_waves)
    queue["fastRepairHandoffCausalWaveMaxParallel"] = 4
    queue["fastRepairHandoffParallelExecutionEnabled"] = False
    queue["fastRepairHandoffFamilyFrontierProviders"] = family_frontier
    queue["fastRepairHandoffFamilyFrontierCount"] = len(family_frontier)
    queue["fastRepairHandoffDeferredFamilySiblings"] = family_deferred
    queue["fastRepairHandoffDeferredFamilySiblingCount"] = len(family_deferred)
    queue["fastRepairHandoffFamilyFrontierPolicy"] = (
        "explicit-cohort-one-representative-per-causal-family-siblings-pending"
        if explicit_cohort else "one-representative-per-causal-family-then-return-to-repair"
    )
    queue["fastRepairHandoffMaxAttemptsPerProviderThisPhase"] = 1 if fair_handoff else 0
    queue["fastRepairHandoffMaxEvolvedAttemptsPerProviderThisPhase"] = 3 if fair_handoff else 0
    source_family_parser_ready = (
        source_family_parser_installed(ROOT) if source_contract_frontier else False
    )
    source_family_resolver_ready = (
        source_family_resolver_installed(ROOT) if source_resolver_frontier else False
    )
    source_contract_provider_states_map = source_contract_provider_states(
        order,
        source_contract_frontier,
        source_family_parser_ready,
        source_resolver_frontier,
        source_family_resolver_ready,
        source_player_target_frontier,
    )
    source_contract_deferred, source_contract_replay, source_contract_status = (
        source_contract_capability_state(
            order,
            source_contract_frontier,
            source_family_parser_ready,
            source_resolver_frontier,
            source_family_resolver_ready,
            source_player_target_frontier,
        )
    )
    queue["sourceContractProviderStates"] = source_contract_provider_states_map
    queue["sourceContractFamilyDeferredProviders"] = source_contract_deferred
    queue["sourceContractFamilyDeferredProviderCount"] = len(source_contract_deferred)
    queue["sourceContractFamilyReplayProviders"] = source_contract_replay
    queue["sourceContractFamilyReplayProviderCount"] = len(source_contract_replay)
    queue["sourceContractResolverProviders"] = [
        pid for pid in order if pid in source_resolver_frontier
    ]
    queue["sourceContractPlayerTargetProviders"] = [
        pid for pid in order if pid in source_player_target_frontier
    ]
    queue["sourceContractPlayerTargetProviderCount"] = len(
        queue["sourceContractPlayerTargetProviders"]
    )
    queue["sourceContractPlayerTargetStructures"] = {
        pid: source_player_structures[pid]
        for pid in order
        if pid in source_player_structures and pid in source_player_target_frontier
    }
    queue["sourceContractPlayerTargetStructureProviderCount"] = len(
        queue["sourceContractPlayerTargetStructures"]
    )
    queue["sourceContractPlayerTargetStructureAuthority"] = (
        "exact-parent-sanitized-player-target-structure-diagnostic-only"
    )
    queue["sourceContractResolverProviderCount"] = len(
        queue["sourceContractResolverProviders"]
    )
    queue["sourceContractResolverContract"] = (
        RESOLVER_CONTRACT if queue["sourceContractResolverProviders"] else ""
    )
    queue["sourceContractResolverInstalled"] = source_family_resolver_ready
    queue["sourceContractFamilyEvidenceAuthority"] = (
        "native-parent-and-independent-source-exact-current-js-diagnostic-only"
    )
    queue["sourceContractFamilyExecutableStatus"] = source_contract_status
    print(
        "FIELD_BRAIN_SOURCE_FAMILY_CAPABILITY "
        f"parser_installed={str(source_family_parser_ready).lower()} "
        f"resolver_attested={len(queue['sourceContractResolverProviders'])} "
        f"resolver_installed={str(source_family_resolver_ready).lower()} "
        f"player_target={len(queue['sourceContractPlayerTargetProviders'])} "
        f"player_structure={queue['sourceContractPlayerTargetStructureProviderCount']} "
        f"deferred={len(source_contract_deferred)} replay={len(source_contract_replay)} "
        f"status={source_contract_status}",
        flush=True,
    )
    queue["deferredRepairProviders"] = unique([*repair_deferred, *source_contract_deferred])
    queue["deferredRepairProviderCount"] = len(queue["deferredRepairProviders"])
    queue["deferredRepairReason"] = "repair_experiment_variants_exhausted_new_strategy_required"
    queue["deferredRepairAuthorities"] = [
        "brain-repair-memory.json",
        "provider-repair-learn-handoff-v1.json",
    ]
    queue["censusRepairProviders"] = census_repair
    queue["censusRepairProviderCount"] = len(census_repair)
    queue["censusRepairAuthority"] = census_repair_authority
    queue["cleanReconstructionRequiredProviders"] = reconstruction_required
    queue["cleanReconstructionRequiredCount"] = len(reconstruction_required)
    queue["cleanReconstructionAuthoringPolicy"] = "niakvio-owned-v2"
    queue["legacyExecutableSeedAllowed"] = False
    provider_state = queue.setdefault("providerState", {})
    deadline = time.time() + max(1, args.budget_minutes) * 60
    work_deadline = deadline - max(0, args.reserve_minutes) * 60
    retry_next: list[str] = []
    processed: list[str] = []
    run_results: list[dict[str, Any]] = []
    combined_rounds: list[dict[str, Any]] = []
    combined_plans: dict[str, Any] = {}
    phase_experiment_ledger: list[dict[str, Any]] = []
    phase_learning_state = copy.deepcopy(previous)
    phase_learning_state["publicationAllowed"] = False
    phase_learning_state["productionWritesAllowed"] = False
    phase_learning_state_path = output / "phase-learning-state.json"
    write_json(phase_learning_state_path, phase_learning_state)

    interrupted_provider = ""
    lab_session = (
        LearningLabSession(work_deadline)
        if source_family_parser_ready or any(pid not in source_contract_frontier for pid in order)
        else None
    )
    try:
        for provider_id in order:
            if time.time() >= work_deadline:
                break
            full_registry = load_json(full_registry_path, {})
            if provider_id not in candidate_map(full_registry):
                retry_next.append(provider_id)
                continue
    
            state = provider_state.setdefault(provider_id, {"attemptCount": 0, "fixtureCursor": {}})
            run_dir = output / "providers" / provider_id
            run_dir.mkdir(parents=True, exist_ok=True)
            info = info_by_id.get(provider_id, {"provider": provider_id, "status": "", "needs_route_search": False})
            if provider_id in source_contract_deferred:
                run_results.append(
                    defer_new_source_contract_family(provider_id, state, info, queue)
                )
                processed.append(provider_id)
                print(
                    "FIELD_BRAIN_LEARNING_SOURCE_CONTRACT_DEFER "
                    f"provider={provider_id} old_profiles_executed=0 "
                    f"status={source_contract_status} native_playback=false "
                    "publication=false",
                    flush=True,
                )
                continue
            provider_deadline = work_deadline
            if fair_handoff:
                remaining_providers = max(1, len(order) - len(processed))
                fair_seconds = max(
                    45,
                    min(
                        120,
                        int(max(1.0, work_deadline - time.time()) / remaining_providers),
                    ),
                )
                provider_deadline = min(work_deadline, time.time() + fair_seconds)
                print(
                    "FIELD_BRAIN_HANDOFF_FAIR_SHARE "
                    f"provider={provider_id} max_attempts=1 evolved_max_attempts=3 "
                    f"slice_seconds={fair_seconds} "
                    f"remaining_providers={remaining_providers}"
                )

            route = None
            route_refresh: dict[str, Any] | None = None
            if bool(info.get("needs_route_search")) and time.time() < provider_deadline:
                route, route_refresh = route_refresh_with_budget_scope(
                    provider_id,
                    run_dir,
                    stage,
                    provider_deadline,
                    work_deadline,
                    fair_handoff,
                )
    
            provider_attempts: list[dict[str, Any]] = []
            seen_method_sets: set[tuple[str, ...]] = set()
            final_lab: dict[str, Any] | None = None
            resolved = False
            attempts_this_phase = 0
    
            while time.time() < work_deadline and not (
                isinstance(route_refresh, dict) and route_refresh.get("ok") is False
            ):
                full_registry = load_json(full_registry_path, {})
                target_path = run_dir / "candidates.json"
                write_json(target_path, targeted_registry(full_registry, provider_id))
    
                attempt_no = int(state.get("attemptCount") or 0) + 1
                attempt_dir = run_dir / f"attempt-{attempt_no}"
                attempt_dir.mkdir(parents=True, exist_ok=True)
                try:
                    provider_source_contract_status = str(
                        source_contract_provider_states_map.get(provider_id) or source_contract_status
                    )
                    resolver_replay = (
                        source_family_resolver_ready
                        and provider_id in source_resolver_frontier
                        and provider_source_contract_status == "resolver_installed_replay_required"
                    )
                    player_structure = source_player_structures.get(provider_id) or {}
                    request_contract_replay = (
                        source_family_resolver_ready
                        and provider_id in source_player_target_frontier
                        and provider_source_contract_status == "player_target_observed"
                        and player_structure.get("resolvedTargetRequestBootstrapObserved") is True
                    )
                    preferred_profile = (
                        PLAYER_REQUEST_CONTRACT_PROFILE
                        if request_contract_replay else
                        RESOLVER_STRATEGY_ID if resolver_replay else ""
                    )
                    preferred_failure_class = (
                        PLAYER_REQUEST_CONTRACT_FAILURE
                        if request_contract_replay else
                        RESOLVER_FAILURE_CLASS if resolver_replay else ""
                    )
                    causal_failure_class = (
                        "media_extraction_gap"
                        if provider_id in source_player_target_frontier
                        else ""
                    )

                    # Older executed negatives predate per-experiment network
                    # telemetry. Replay the exact installed implementation once
                    # in a temporary child memory, enrich the historical row,
                    # and keep its attempts/failures/outcome unchanged.
                    diagnostic_target = (
                        missing_network_diagnostic_negative(
                            phase_learning_state,
                            provider_id,
                            preferred_profile,
                        )
                        if preferred_profile else None
                    )
                    if diagnostic_target is not None:
                        diagnostic_state = diagnostic_replay_memory(
                            phase_learning_state,
                            diagnostic_target,
                        )
                        diagnostic_state_path = attempt_dir / "diagnostic-learning-state.json"
                        write_json(diagnostic_state_path, diagnostic_state)
                        diagnostic_output = attempt_dir / "diagnostic-network-replay"
                        diagnostic_repair = repair_attempt(
                            provider_id,
                            stage,
                            target_path,
                            diagnostic_output,
                            diagnostic_state_path,
                            provider_deadline,
                            preferred_profile=preferred_profile,
                            preferred_failure_class=preferred_failure_class,
                            causal_failure_class=causal_failure_class,
                        )
                        # Diagnostic replay never owns the staged registry.
                        write_json(target_path, targeted_registry(full_registry, provider_id))
                        diagnostic_plans = (
                            (diagnostic_repair.get("report") or {}).get("brain") or {}
                        ).get("plans") or {}
                        diagnostic_plan: dict[str, Any] = {}
                        for value in diagnostic_plans.values():
                            if (
                                isinstance(value, dict)
                                and norm(value.get("providerId")) == provider_id
                            ):
                                diagnostic_plan = value
                                break
                        diagnostic_summary = repair_network_execution_summary(
                            diagnostic_repair,
                            preferred_profile,
                        )
                        diagnostic_delta = repair_network_execution_delta(
                            diagnostic_repair,
                            preferred_profile,
                        )
                        target_fingerprint = str(
                            diagnostic_target.get("strategyImplementationFingerprint") or ""
                        ).strip().casefold()
                        if int(diagnostic_repair.get("accepted") or 0) > 0:
                            # A previously negative implementation changed
                            # outcome. Remove only that exact historical
                            # implementation from this phase so the normal path
                            # can revalidate and, if still green, promote it
                            # through the ordinary strict gates.
                            phase_learning_state = diagnostic_replay_memory(
                                phase_learning_state,
                                diagnostic_target,
                            )
                            write_json(phase_learning_state_path, phase_learning_state)
                            print(
                                "FIELD_BRAIN_DIAGNOSTIC_REPLAY_CHANGED "
                                f"provider={provider_id} profile={preferred_profile} "
                                f"fingerprint={target_fingerprint[:12]} "
                                "outcome=accepted action=normal_revalidation_required "
                                "publication=false",
                                flush=True,
                            )
                        else:
                            backfill = diagnostic_network_backfill_entry(
                                diagnostic_target,
                                diagnostic_plan,
                                diagnostic_summary,
                                diagnostic_delta,
                            )
                            if backfill is not None:
                                phase_experiment_ledger.append(backfill)
                                phase_learning_state = apply_diagnostic_network_backfill(
                                    phase_learning_state,
                                    backfill,
                                )
                                write_json(phase_learning_state_path, phase_learning_state)
                                summary = backfill["networkExecutionSummary"]
                                print(
                                    "FIELD_BRAIN_DIAGNOSTIC_NETWORK_BACKFILL "
                                    f"provider={provider_id} profile={preferred_profile} "
                                    f"fingerprint={target_fingerprint[:12]} "
                                    f"requests={int(summary.get('providerRequestCount') or 0)} "
                                    f"successful={int(summary.get('successfulProviderRequestCount') or 0)} "
                                    f"network_failures={int(summary.get('networkFailureCount') or 0)} "
                                    f"deepest={str(summary.get('deepestStage') or 'none')} "
                                    f"request_delta={int((backfill.get('networkExecutionDelta') or {}).get('providerRequestDelta') or 0)} "
                                    f"success_delta={int((backfill.get('networkExecutionDelta') or {}).get('successfulProviderRequestDelta') or 0)} "
                                    f"stage_advanced={str(bool((backfill.get('networkExecutionDelta') or {}).get('stageAdvanced'))).lower()} "
                                    "attempts_incremented=false failures_incremented=false "
                                    "publication=false",
                                    flush=True,
                                )
                            else:
                                print(
                                    "FIELD_BRAIN_DIAGNOSTIC_NETWORK_BACKFILL "
                                    f"provider={provider_id} profile={preferred_profile} "
                                    f"fingerprint={target_fingerprint[:12]} "
                                    "status=unavailable reason=fingerprint-or-summary-mismatch "
                                    "publication=false",
                                    flush=True,
                                )

                    followup = network_causal_followup(
                        phase_learning_state,
                        provider_id,
                    )
                    if followup is not None:
                        preferred_profile = followup["profile"]
                        preferred_failure_class = followup["failureClass"]
                        causal_failure_class = followup["failureClass"]
                        print(
                            "FIELD_BRAIN_NETWORK_CAUSAL_FOLLOWUP "
                            f"provider={provider_id} "
                            f"source_profile={followup['sourceProfile']} "
                            f"profile={preferred_profile} "
                            f"failure={preferred_failure_class} "
                            f"requests={followup['providerRequestCount']} "
                            f"successful={followup['successfulProviderRequestCount']} "
                            f"four_xx={followup['fourXxCount']} "
                            f"request_delta={followup['providerRequestDelta']} "
                            f"successful_delta={followup['successfulProviderRequestDelta']} "
                            f"four_xx_delta={followup['fourXxDelta']} "
                            f"deepest={followup['deepestStage']} "
                            f"reason={followup['reason']} "
                            "proof_authority=false publication=false",
                            flush=True,
                        )

                    repair = repair_attempt(
                        provider_id,
                        stage,
                        target_path,
                        attempt_dir,
                        phase_learning_state_path,
                        provider_deadline,
                        preferred_profile=preferred_profile,
                        preferred_failure_class=preferred_failure_class,
                        causal_failure_class=causal_failure_class,
                    )
                except BudgetExhausted as error:
                    state["lastStatus"] = "fair_share_slice_exhausted"
                    state["lastAttemptAt"] = datetime.now(timezone.utc).isoformat()
                    print(
                        "FIELD_BRAIN_HANDOFF_SLICE_EXHAUSTED "
                        f"provider={provider_id} stage=repair reason={error}"
                    )
                    break
                merge_target_candidate(full_registry_path, target_path, provider_id)
                brain_plans = ((repair["report"].get("brain") or {}).get("plans") or {})
                provider_plan: dict[str, Any] = {}
                for key, value in brain_plans.items():
                    combined_plans[str(key)] = value
                    if (
                        isinstance(value, dict)
                        and str(value.get("providerId") or "").strip().casefold() == provider_id
                    ):
                        provider_plan = value
                if provider_plan:
                    profiles = ",".join(
                        str(value)
                        for value in provider_plan.get("allowedProfiles") or []
                        if str(value)
                    ) or "none"
                    print(
                        "FIELD_BRAIN_PROVIDER_PLAN "
                        f"provider={provider_id} "
                        f"failure={str(provider_plan.get('failureClass') or 'unknown')} "
                        f"derived_failure={str(provider_plan.get('derivedFailureClass') or 'unknown')} "
                        f"causal_requested={str(provider_plan.get('learningCausalFailureRequested') or 'none')} "
                        f"causal_applied={str(provider_plan.get('learningCausalFailureApplied') is True).lower()} "
                        f"action={str(provider_plan.get('action') or 'unknown')} "
                        f"variant={int(provider_plan.get('experimentVariant') or 0)} "
                        f"generation={max(1, int(provider_plan.get('experimentGeneration') or 1))} "
                        f"profiles={profiles} "
                        f"historical={str(provider_plan.get('historicalStrategyCase') or 'none')} "
                        f"exhausted={str(provider_plan.get('experimentExhausted') is True).lower()}"
                    )
                for row in repair["report"].get("rounds") or []:
                    if isinstance(row, dict):
                        tagged = copy.deepcopy(row)
                        tagged["providerId"] = provider_id
                        combined_rounds.append(tagged)
    
                full_registry = load_json(full_registry_path, {})
                candidate = candidate_map(full_registry).get(provider_id) or {}
                media_type = declared_type(
                    provider_id,
                    candidate,
                    manifest=manifest_authority,
                    census=census_authority,
                )
                fixture = choose_fixture(health_config, state, media_type)
                try:
                    lab_session = ensure_learning_lab_session(
                        lab_session,
                        work_deadline,
                    )
                    final_lab = run_lab(
                        lab_session,
                        provider_id,
                        target_path,
                        stage,
                        fixture,
                        attempt_dir,
                        provider_deadline,
                        args.stream_safety_cap,
                        requires_full_variant_probe(provider_plan),
                    )
                except BudgetExhausted as error:
                    state["lastStatus"] = "fair_share_slice_exhausted"
                    state["lastAttemptAt"] = datetime.now(timezone.utc).isoformat()
                    provider_attempts.append({
                        "attempt": attempt_no,
                        "repairAccepted": repair["accepted"],
                        "attemptedProfiles": repair["attemptedProfiles"],
                        "attemptedMethods": repair["attemptedMethods"],
                        "lab": {"status": "fair_share_slice_exhausted"},
                    })
                    attempts_this_phase += 1
                    print(
                        "FIELD_BRAIN_HANDOFF_SLICE_EXHAUSTED "
                        f"provider={provider_id} stage=lab reason={error}"
                    )
                    break
                method_set = tuple(repair["attemptedMethods"])
                provider_attempts.append({
                    "attempt": attempt_no,
                    "repairAccepted": repair["accepted"],
                    "attemptedProfiles": repair["attemptedProfiles"],
                    "attemptedMethods": repair["attemptedMethods"],
                    "lab": final_lab,
                })
                state["attemptCount"] = attempt_no
                state["lastAttemptAt"] = datetime.now(timezone.utc).isoformat()
                state["lastStatus"] = final_lab.get("status")
                state["lastFixture"] = final_lab.get("fixtureSlug")
                state["lastClients"] = final_lab.get("clients")
                attempts_this_phase += 1

                if provider_plan:
                    attempt_entries = phase_experiment_entries(
                        provider_id,
                        provider_plan,
                        repair,
                        final_lab,
                    )
                    phase_experiment_ledger.extend(attempt_entries)
                    if attempt_entries:
                        phase_learning_state = merge_phase_learning_state(
                            phase_learning_state,
                            attempt_entries,
                        )
                        write_json(phase_learning_state_path, phase_learning_state)
    
                if final_lab.get("status") == "playable":
                    resolved = True
                    break
    
                # If the Core did not initially suspect an access problem but the
                # independent Lab cannot reach any runtime, challenge the diagnosis
                # with a route search before abandoning the provider.
                any_runtime = any(int(x.get("runtimeStreams") or 0) > 0 for x in (final_lab.get("clients") or {}).values())
                if not any_runtime and route is None and time.time() < provider_deadline:
                    route, route_refresh = route_refresh_with_budget_scope(
                        provider_id,
                        run_dir,
                        stage,
                        provider_deadline,
                        work_deadline,
                        fair_handoff,
                    )
                    if route_refresh.get("ok") is False:
                        break
                    if fair_handoff and attempts_this_phase >= 1 and not should_continue_evolved_frontier(
                        provider_plan,
                        attempts_this_phase,
                    ):
                        break
                    continue

                # Ordinary Fast-Handoff still rotates after one complete
                # experiment. The only exception is a bounded post-g5 evolved
                # frontier: its newly planned strategy is fed the exact outcome
                # above and may execute immediately while this provider's
                # existing fair-share deadline still has budget.
                if fair_handoff and attempts_this_phase >= 1 and not should_continue_evolved_frontier(
                    provider_plan,
                    attempts_this_phase,
                ):
                    break
    
                # Learning is allowed to turn a failed experiment into the next
                # planner variant/generation in the same run. The adaptive profile
                # name is intentionally stable, so the causal fingerprint includes
                # signature + experiment generation + variant. Stop only when the
                # Brain repeats that exact method (or produced no method at all).
                if method_set in seen_method_sets or not method_set:
                    break
                seen_method_sets.add(method_set)
                if repair["accepted"] == 0:
                    continue
    
            if isinstance(route_refresh, dict) and route_refresh.get("ok") is False:
                if route_refresh.get("sliceExhausted") is True:
                    state["lastStatus"] = "fair_share_slice_exhausted"
                    state["lastAttemptAt"] = datetime.now(timezone.utc).isoformat()
                    print(
                        "FIELD_BRAIN_HANDOFF_SLICE_EXHAUSTED "
                        f"provider={provider_id} stage=route-refresh reason=provider-fair-share-deadline"
                    )
                else:
                    state["lastStatus"] = "stage_refresh_blocked"
                state["lastStageRefresh"] = copy.deepcopy(route_refresh)
            processed.append(provider_id)
            if not resolved:
                retry_next.append(provider_id)
            run_results.append({
                "provider": provider_id,
                "coreHypothesis": info,
                "routeSearch": route,
                "routeRefresh": route_refresh,
                "resolved": resolved,
                "attempts": provider_attempts,
                "finalLab": final_lab,
            })
    
            pending = [x for x in queue.get("pendingProviders") or [] if x != provider_id]
            queue["pendingProviders"] = pending
            completed = unique([*(queue.get("completedInCycle") or []), provider_id])
            queue["completedInCycle"] = completed
    
    except BudgetExhausted as error:
        interrupted_provider = provider_id
        retry_next.append(provider_id)
        combined_rounds = [
            row for row in combined_rounds
            if norm(row.get("providerId")) != interrupted_provider
        ]
        combined_plans = {
            key: value for key, value in combined_plans.items()
            if norm(key) != interrupted_provider
            and not (
                isinstance(value, dict)
                and norm(value.get("provider") or value.get("providerId") or value.get("targetProvider")) == interrupted_provider
            )
        }
        print(
            "FIELD_BRAIN_QUEUE_BUDGET_EXHAUSTED "
            f"provider={interrupted_provider} reason={error}"
        )
    finally:
        if lab_session is not None:
            lab_session.close()

    remaining_order = [pid for pid in order if pid not in processed]
    queue["retryProviders"] = unique(retry_next)
    queue["pendingProviders"] = interleave(
        queue["retryProviders"],
        unique([
            *(queue.get("pendingProviders") or []),
            *remaining_order,
            *family_deferred,
        ]),
    )
    queue["processedThisRun"] = processed
    queue["generatedAt"] = datetime.now(timezone.utc).isoformat()
    queue["budgetMinutes"] = args.budget_minutes
    queue["timeBudgetExhausted"] = bool(interrupted_provider) or time.time() >= work_deadline
    queue["budgetInterruptionProvider"] = interrupted_provider
    queue["remainingProviderCount"] = len(queue["pendingProviders"])
    queue["retryProviderCount"] = len(queue["retryProviders"])

    if not queue["pendingProviders"] and not args.provider:
        queue["cycle"] = int(queue.get("cycle") or 1) + 1
        queue["completedInCycle"] = []

    hidden_failures = [
        row["provider"]
        for row in run_results
        if isinstance(row, dict)
        and isinstance(row.get("finalLab"), dict)
        and row["finalLab"].get("status") != "playable"
        and str((row.get("coreHypothesis") or {}).get("status") or "") in {"healthy", "reachable"}
    ]
    fixture_updates = {
        row["provider"]: [
            str(attempt.get("lab", {}).get("fixtureSlug") or "")
            for attempt in row.get("attempts") or []
            if isinstance(attempt, dict) and str(attempt.get("lab", {}).get("fixtureSlug") or "")
        ]
        for row in run_results
        if isinstance(row, dict) and row.get("provider")
    }
    queue["completedProviders"] = processed
    queue["hiddenFailureProviders"] = unique(hidden_failures)
    queue["fixtureHistoryUpdates"] = fixture_updates
    queue["isolatedProviderRefreshFailures"] = unique([
        str(row.get("provider") or "")
        for row in run_results
        if isinstance(row, dict)
        and isinstance(row.get("routeRefresh"), dict)
        and row["routeRefresh"].get("ok") is False
        and str(row.get("provider") or "")
    ])

    hidden_core_failures = sorted({
        str(row.get("provider") or "")
        for row in run_results
        if isinstance(row, dict)
        and str((row.get("coreHypothesis") or {}).get("status") or "") in {"healthy", "reachable"}
        and isinstance(row.get("finalLab"), dict)
        and str((row.get("finalLab") or {}).get("status") or "") != "playable"
        and str(row.get("provider") or "")
    })
    previous_hidden = [
        norm(value) for value in queue.get("hiddenFailureProviders") or []
        if norm(value)
    ]
    queue["hiddenFailureProviders"] = unique([*previous_hidden, *hidden_core_failures])

    summary = {
        "schemaVersion": 3,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "coreEvidenceAuthority": "hypothesis_only",
        "budgetMinutes": args.budget_minutes,
        "fastRepairHandoffProviders": handoff_priority,
        "fastRepairHandoffProviderCount": len(handoff_priority),
        "fastRepairHandoffCausalBatchCount": len(causal_group_order),
        "fastRepairHandoffCausalBatchOrder": causal_group_order,
        "fastRepairHandoffOrderingPolicy": "causal-batch-round-robin",
        "fastRepairHandoffCausalWaves": causal_waves,
        "fastRepairHandoffCausalWaveCount": len(causal_waves),
        "fastRepairHandoffCausalWaveMaxParallel": 4,
        "fastRepairHandoffParallelExecutionEnabled": False,
        "fastRepairHandoffFamilyFrontierProviders": family_frontier,
        "fastRepairHandoffFamilyFrontierCount": len(family_frontier),
        "fastRepairHandoffDeferredFamilySiblings": family_deferred,
        "fastRepairHandoffDeferredFamilySiblingCount": len(family_deferred),
        "fastRepairHandoffFamilyFrontierPolicy": "one-representative-per-causal-family-then-return-to-repair",
        "fastRepairHandoffMaxAttemptsPerProviderThisPhase": 1 if fair_handoff else 0,
        "fastRepairHandoffMaxEvolvedAttemptsPerProviderThisPhase": 3 if fair_handoff else 0,
        "cleanReconstructionRequiredProviders": reconstruction_required,
        "cleanReconstructionRequiredCount": len(reconstruction_required),
        "deferredRepairProviders": queue["deferredRepairProviders"],
        "deferredRepairProviderCount": queue["deferredRepairProviderCount"],
        "sourceContractFamilyDeferredProviders": source_contract_deferred,
        "sourceContractFamilyDeferredProviderCount": len(source_contract_deferred),
        "sourceContractFamilyReplayProviders": source_contract_replay,
        "sourceContractFamilyReplayProviderCount": len(source_contract_replay),
        "sourceContractResolverProviders": queue["sourceContractResolverProviders"],
        "sourceContractResolverProviderCount": queue["sourceContractResolverProviderCount"],
        "sourceContractResolverContract": queue["sourceContractResolverContract"],
        "sourceContractResolverInstalled": queue["sourceContractResolverInstalled"],
        "sourceContractPlayerTargetProviders": queue["sourceContractPlayerTargetProviders"],
        "sourceContractPlayerTargetProviderCount": queue["sourceContractPlayerTargetProviderCount"],
        "sourceContractPlayerTargetStructures": queue["sourceContractPlayerTargetStructures"],
        "sourceContractPlayerTargetStructureProviderCount": queue["sourceContractPlayerTargetStructureProviderCount"],
        "sourceContractPlayerTargetStructureAuthority": queue["sourceContractPlayerTargetStructureAuthority"],
        "sourceContractProviderStates": queue["sourceContractProviderStates"],
        "sourceContractFamilyExecutableStatus": queue["sourceContractFamilyExecutableStatus"],
        "legacyExecutableSeedAllowed": False,
        "processedProviders": processed,
        "processedProviderCount": len(processed),
        "budgetInterruptionProvider": interrupted_provider,
        "timeBudgetExhausted": queue["timeBudgetExhausted"],
        "retryProviders": queue["retryProviders"],
        "hiddenFailureProviders": hidden_core_failures,
        "isolatedProviderRefreshFailures": queue["isolatedProviderRefreshFailures"],
        "results": run_results,
        "productionWritesAllowed": False,
        "publicationAllowed": False,
    }

    write_json(output / "learning-queue-state.json", queue)
    write_json(output / "learning-queue-summary.json", summary)
    write_json(output / "runtime-experiment-memory.json", {
        "schemaVersion": 2,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "memoryRole": "fair-share-exact-experiment-ledger",
        "productionWritesAllowed": False,
        "publicationAllowed": False,
        "providerCount": len({str(row.get("providerId") or "") for row in phase_experiment_ledger if str(row.get("providerId") or "")}),
        "entries": phase_experiment_ledger,
    })
    write_json(output / "repair-report.json", {
        "schema_version": 3,
        "mode": "learning_queue",
        "rounds": combined_rounds,
        "queue": queue,
        "accepted_repairs": sum(
            sum(durable_accepted_event(event) for event in row.get("accepted") or [])
            for row in combined_rounds if isinstance(row, dict)
        ),
        "provisional_candidates": sum(
            sum(provisional_accepted_event(event) for event in row.get("accepted") or [])
            for row in combined_rounds if isinstance(row, dict)
        ),
        "brain": {"plans": combined_plans},
    })
    write_json(output / "targeted-lab-summary.json", {
        "schemaVersion": 3,
        "status": "multi_provider",
        "providers": [x.get("finalLab") for x in run_results if isinstance(x.get("finalLab"), dict)],
        "providerId": processed[-1] if processed else "",
        "hiddenFailureProviders": hidden_core_failures,
        "productionWritesAllowed": False,
        "publicationAllowed": False,
    })
    print(
        "FIELD_BRAIN_QUEUE "
        f"processed={len(processed)} retries={len(queue['retryProviders'])} "
        f"pending={len(queue['pendingProviders'])} exhausted={str(queue['timeBudgetExhausted']).lower()}"
    )
    print(
        "FIELD_BRAIN_PHASE_LEDGER "
        f"entries={len(phase_experiment_ledger)} "
        f"providers={len({str(row.get('providerId') or '') for row in phase_experiment_ledger if str(row.get('providerId') or '')})}"
    )
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
