#!/usr/bin/env python3
"""Time-budgeted adaptive provider investigation queue for NiakVIO Learning."""
from __future__ import annotations

import argparse
import copy
import json
import os
import re
import shutil
import subprocess
import sys
import time
import select
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"

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
            self.process.kill()
            self.process.wait(timeout=3)


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

        entries.append({
            "providerId": norm(provider_id),
            "providerVersion": "*",
            "failureClass": failure_class,
            "signature": signature,
            "profile": profile,
            "positiveProgramFingerprint": str(
                effective_plan.get("positiveProgramFingerprint") or ""
            ).strip().casefold(),
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
            "executionObserved": bool(attempts),
        })
    return entries


def _phase_experiment_key(row: dict[str, Any]) -> tuple[str, str, str, str, str, str, int, int]:
    return (
        norm(row.get("providerId")),
        str(row.get("providerVersion") or "*").strip() or "*",
        str(row.get("failureClass") or "").strip(),
        str(row.get("signature") or "").strip(),
        str(row.get("profile") or "").strip(),
        str(row.get("positiveProgramFingerprint") or "").strip().casefold(),
        max(0, int(row.get("experimentVariant") or 0)),
        max(1, int(row.get("experimentGeneration") or 1)),
    )


def merge_phase_learning_state(
    state: dict[str, Any],
    entries: list[dict[str, Any]],
    *,
    max_entries: int = 1000,
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
        for field in ("lastOutcome", "lastReason", "lastSeenAt", "memoryRole", "capabilityStrategy", "observedPipelineStage"):
            if field in row:
                current[field] = row[field]
        current["executionObserved"] = (
            current.get("executionObserved") is True
            or row.get("executionObserved") is True
        )

    limit = max(1, int(max_entries))
    memory["entries"] = rows[-limit:]
    memory["schemaVersion"] = max(1, int(memory.get("schemaVersion") or 1))
    return output


def merge_wave_experiment_entries(
    state: dict[str, Any],
    provider_entries: list[list[dict[str, Any]]],
    *,
    max_entries: int = 1000,
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
    """Providers whose current Repair experiment family needs a new strategy."""
    production = policy.get("production") if isinstance(policy.get("production"), dict) else {}
    negative = production.get("negativeExperimentMemory") if isinstance(production.get("negativeExperimentMemory"), dict) else {}
    max_variants = max(1, int(negative.get("maxVariantsPerSignature") or 5))
    rotate_every = max(1, int(negative.get("rotateExperimentAfterFailures") or 1))
    groups: dict[tuple[str, str, str, str], set[int]] = {}
    for row in memory.get("entries") or []:
        if not isinstance(row, dict) or int(row.get("successes") or 0) > 0:
            continue
        provider = norm(row.get("providerId"))
        if not provider or int(row.get("consecutiveFailures") or 0) < rotate_every:
            continue
        key = (
            provider,
            str(row.get("failureClass") or ""),
            str(row.get("signature") or ""),
            str(row.get("profile") or ""),
        )
        variant = max(0, min(max_variants - 1, int(row.get("experimentVariant") or 0)))
        groups.setdefault(key, set()).add(variant)
    return sorted({
        key[0]
        for key, variants in groups.items()
        if len(variants) >= max_variants
    })


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

def run(cmd: list[str], *, env: dict[str, str] | None, deadline: float, cwd: Path = ROOT, allow_fail: bool = False) -> subprocess.CompletedProcess[str]:
    timeout = remaining_seconds(deadline, 1)
    try:
        completed = subprocess.run(
            cmd,
            cwd=cwd,
            env=env,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as error:
        stdout = error.stdout.decode(errors="replace") if isinstance(error.stdout, bytes) else str(error.stdout or "")
        stderr = error.stderr.decode(errors="replace") if isinstance(error.stderr, bytes) else str(error.stderr or "")
        sys.stdout.write(stdout)
        sys.stderr.write(stderr)
        raise BudgetExhausted(
            f"Learning work budget exhausted while running: {' '.join(cmd[:4])}"
        ) from error
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

def declared_type(candidate: dict[str, Any]) -> str:
    metadata = candidate.get("metadata") if isinstance(candidate.get("metadata"), dict) else {}
    values = metadata.get("supportedTypes") or []
    if isinstance(values, str):
        values = [values]
    first = norm(values[0] if values else "movie")
    if "anime" in first or "anim" in first:
        return "anime"
    if first in {"tv", "series", "serie", "show"}:
        return "tv"
    return "movie"

def choose_fixture(config: dict[str, Any], provider_state: dict[str, Any], media_type: str) -> dict[str, Any]:
    fixtures = config.get("fixtures") if isinstance(config.get("fixtures"), dict) else {}
    pool = fixtures.get(media_type) if isinstance(fixtures.get(media_type), list) else []
    if not pool:
        pool = fixtures.get("movie") if isinstance(fixtures.get("movie"), list) else []
    if not pool:
        raise ValueError("health-config contains no Learning fixtures")
    cursors = provider_state.setdefault("fixtureCursor", {})
    index = int(cursors.get(media_type) or 0) % len(pool)
    fixture = copy.deepcopy(pool[index])
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

def run_lab(
    session: LearningLabSession,
    provider_id: str,
    registry_path: Path,
    stage: Path,
    fixture: dict[str, Any],
    run_dir: Path,
    deadline: float,
    stream_cap: int,
) -> dict[str, Any]:
    report_path = run_dir / "targeted-lab.json"
    markdown_path = run_dir / "targeted-lab.md"
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
        "max_streams_per_runtime": max(1, min(int(stream_cap), 2)),
        "probe_all_streams": False,
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
    summary["streamProbeCap"] = max(1, min(int(stream_cap), 2))
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


def repair_attempt(
    provider_id: str,
    stage: Path,
    registry_path: Path,
    output: Path,
    previous_state_path: Path,
    deadline: float,
) -> dict[str, Any]:
    env = os.environ.copy()
    env["NUVIO_BRAIN_TARGET_PROVIDER"] = provider_id
    env["NUVIO_BRAIN_LEARNING_STATE"] = str(previous_state_path)
    # The child planner imports brain_repair_runtime before sandbox main() runs,
    # so the previous sanitized Learning state must be present in the process
    # environment at spawn time. This is Learning-only memory; production Repair
    # still reads automation/brain-repair-memory.json.
    env["NIAKVIO_BRAIN_LEARNING_MEMORY"] = str(previous_state_path)
    env["NUVIO_BRAIN_DEADLINE_EPOCH_MS"] = str(int(deadline * 1000))
    env["NUVIO_WORKER_MEMORY_MB"] = "1024"
    completed = run([
        sys.executable, str(SCRIPTS / "run_brain_learning_sandbox.py"),
        "--stage", str(stage), "--registry", str(registry_path),
        "--output", str(output), "--max-rounds", "0",
    ], env=env, deadline=deadline, allow_fail=True)
    report = load_json(output / "repair-report.json", {})
    # Validate accepted repairs against the exact targeted registry before the
    # candidate is merged back into the full Learning staging tree.
    run([
        sys.executable, str(SCRIPTS / "validate_automatic_repair_results.py"),
        "--stage", str(registry_path.parent),
        "--health", str(output / "health-results.json"),
        "--repairs", str(output / "repair-report.json"),
    ], env=env, deadline=deadline)
    accepted = sum(len(x.get("accepted") or []) for x in report.get("rounds") or [] if isinstance(x, dict))
    attempted = sorted({
        str(a.get("profile") or "")
        for x in report.get("rounds") or [] if isinstance(x, dict)
        for a in x.get("attempts") or [] if isinstance(a, dict) and str(a.get("profile") or "")
    })
    methods = repair_method_fingerprints(report, attempted)
    return {
        "returnCode": completed.returncode,
        "accepted": accepted,
        "attemptedProfiles": attempted,
        "attemptedMethods": methods,
        "report": report,
    }

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--stage", type=Path, default=ROOT / "staging")
    p.add_argument("--health", type=Path, default=ROOT / "health-report.json")
    p.add_argument("--previous-state", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--provider", default="")
    p.add_argument("--budget-minutes", type=int, default=60)
    p.add_argument("--reserve-minutes", type=int, default=5)
    p.add_argument("--stream-safety-cap", type=int, default=2)
    args = p.parse_args()

    stage = args.stage.resolve()
    full_registry_path = stage / "candidates.json"
    full_registry = load_json(full_registry_path, {})
    previous = load_json(args.previous_state.resolve(), {})
    health = load_json(args.health.resolve(), {})
    health_config = load_json(ROOT / "health-config.json", {})
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)

    order, info_by_id, queue = build_queue(health, previous, args.provider)

    staged_candidates = candidate_map(full_registry)
    repair_deferred = exhausted_repair_providers(
        load_json(ROOT / "automation" / "brain-repair-memory.json", {}),
        load_json(ROOT / "engine_v2" / "config" / "brain-policy.json", {}),
    )
    census_repair, repair_deferred, census_repair_authority = current_repair_priority(
        repair_deferred,
        load_json(ROOT / "automation" / "provider-census-status.json", {}),
        info_by_id,
        staged_candidates,
    )
    handoff_state = load_json(ROOT / "automation" / "provider-repair-learn-handoff-v1.json", {})
    handoff_rows = handoff_state.get("providers") if isinstance(handoff_state.get("providers"), dict) else {}
    current_repair_set = set(census_repair)
    handoff_priority = [
        provider_id
        for provider_id in unique(list(handoff_rows.keys()))
        if provider_id in current_repair_set
        and provider_id in info_by_id
        and provider_id in staged_candidates
        and isinstance(handoff_rows.get(provider_id), dict)
        and str(handoff_rows[provider_id].get("owner") or "") == "LEARN"
        and str(handoff_rows[provider_id].get("status") or "") == "pending"
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
    causal_group_order: list[str] = []
    if handoff_priority and not args.provider:
        order, causal_group_order = causal_batch_round_robin(order, batch_plan)

    queue["fastRepairHandoffProviders"] = handoff_priority
    queue["fastRepairHandoffProviderCount"] = len(handoff_priority)
    queue["fastRepairHandoffAuthority"] = "provider-repair-learn-handoff-v1.json"
    queue["fastRepairHandoffCausalBatchOrder"] = causal_group_order
    queue["fastRepairHandoffCausalBatchCount"] = len(causal_group_order)
    queue["fastRepairHandoffOrderingPolicy"] = "causal-batch-round-robin"
    # Fast-Handoff mode is an input to causal-wave materialization. Compute it
    # before the wave builder so the real Repair->Learning handoff cannot reach
    # an uninitialized local even though static helper tests pass.
    fair_handoff = bool(handoff_priority) and not bool(args.provider)
    causal_waves = causal_family_waves(order, batch_plan, max_parallel=4) if fair_handoff else []
    queue["fastRepairHandoffCausalWaves"] = causal_waves
    queue["fastRepairHandoffCausalWaveCount"] = len(causal_waves)
    queue["fastRepairHandoffCausalWaveMaxParallel"] = 4
    queue["fastRepairHandoffParallelExecutionEnabled"] = False
    queue["fastRepairHandoffMaxAttemptsPerProviderThisPhase"] = 1 if fair_handoff else 0
    queue["fastRepairHandoffMaxEvolvedAttemptsPerProviderThisPhase"] = 3 if fair_handoff else 0
    queue["deferredRepairProviders"] = repair_deferred
    queue["deferredRepairProviderCount"] = len(repair_deferred)
    queue["deferredRepairReason"] = "repair_experiment_variants_exhausted_new_strategy_required"
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
    lab_session = LearningLabSession(work_deadline)
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
                route = route_search(provider_id, run_dir, provider_deadline)
                route_refresh = refresh_stage_routes(stage, provider_deadline, provider_id)
    
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
                    repair = repair_attempt(
                        provider_id,
                        stage,
                        target_path,
                        attempt_dir,
                        phase_learning_state_path,
                        provider_deadline,
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
                media_type = declared_type(candidate)
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
                    route = route_search(provider_id, run_dir, provider_deadline)
                    route_refresh = refresh_stage_routes(stage, provider_deadline, provider_id)
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
        lab_session.close()

    remaining_order = [pid for pid in order if pid not in processed]
    queue["retryProviders"] = unique(retry_next)
    queue["pendingProviders"] = interleave(
        queue["retryProviders"],
        unique([*(queue.get("pendingProviders") or []), *remaining_order]),
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
        "fastRepairHandoffMaxAttemptsPerProviderThisPhase": 1 if fair_handoff else 0,
        "fastRepairHandoffMaxEvolvedAttemptsPerProviderThisPhase": 3 if fair_handoff else 0,
        "cleanReconstructionRequiredProviders": reconstruction_required,
        "cleanReconstructionRequiredCount": len(reconstruction_required),
        "deferredRepairProviders": repair_deferred,
        "deferredRepairProviderCount": len(repair_deferred),
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
            len(row.get("accepted") or []) for row in combined_rounds if isinstance(row, dict)
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
