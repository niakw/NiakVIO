#!/usr/bin/env python3
"""Time-budgeted adaptive provider investigation queue for NiakVIO Learning."""
from __future__ import annotations

import argparse
import copy
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"

class BudgetExhausted(RuntimeError):
    """The bounded Learning work window ended; persist state and resume later."""


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

def refresh_stage_routes(stage: Path, deadline: float) -> None:
    for cmd in (
        [sys.executable, str(SCRIPTS / "build_provider_runtime_profiles.py"), "--stage", str(stage), "--apply-stage"],
        [sys.executable, str(SCRIPTS / "normalize_terminal_quarantine_stage.py"), "--stage", str(stage)],
        [sys.executable, str(SCRIPTS / "validate_override_pipeline.py"), "--stage", str(stage)],
    ):
        run(cmd, env=os.environ.copy(), deadline=deadline)

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
    provider_id: str,
    registry_path: Path,
    stage: Path,
    fixture: dict[str, Any],
    run_dir: Path,
    deadline: float,
    stream_cap: int,
) -> dict[str, Any]:
    report = run_dir / "targeted-lab.json"
    markdown = run_dir / "targeted-lab.md"
    args = [
        "node", str(SCRIPTS / "nuvio_client_lab.cjs"),
        "--providers", provider_id,
        "--clients", "tv,desktop,mobile",
        "--stage", str(stage),
        "--registry", str(registry_path),
        "--tmdb-id", str(fixture.get("tmdbId") or ""),
        "--media-type", str(fixture.get("mediaType") or "movie"),
        "--title", str(fixture.get("title") or fixture.get("label") or ""),
        "--year", str(fixture.get("year") or ""),
        "--all-streams", "--stream-safety-cap", str(stream_cap),
        "--playback-timeout-ms", "8000",
        "--stream-sampling", "spread",
        "--out", str(report), "--markdown", str(markdown),
    ]
    if fixture.get("season") is not None:
        args += ["--season", str(fixture.get("season"))]
    if fixture.get("episode") is not None:
        args += ["--episode", str(fixture.get("episode"))]
    completed = run(args, env=os.environ.copy(), deadline=deadline, allow_fail=True)
    payload = load_json(report, {"providers": []})
    summary = summarize_lab(payload, provider_id, fixture)
    summary["commandStatus"] = completed.returncode
    return summary

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
    return {"returnCode": completed.returncode, "accepted": accepted, "attemptedProfiles": attempted, "report": report}

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--stage", type=Path, default=ROOT / "staging")
    p.add_argument("--health", type=Path, default=ROOT / "health-report.json")
    p.add_argument("--previous-state", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--provider", default="")
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
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)

    order, info_by_id, queue = build_queue(health, previous, args.provider)
    provider_state = queue.setdefault("providerState", {})
    deadline = time.time() + max(1, args.budget_minutes) * 60
    work_deadline = deadline - max(0, args.reserve_minutes) * 60
    retry_next: list[str] = []
    processed: list[str] = []
    run_results: list[dict[str, Any]] = []
    combined_rounds: list[dict[str, Any]] = []
    combined_plans: dict[str, Any] = {}

    interrupted_provider = ""
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
            route = None
    
            if bool(info.get("needs_route_search")) and time.time() < work_deadline:
                route = route_search(provider_id, run_dir, work_deadline)
                refresh_stage_routes(stage, work_deadline)
    
            provider_attempts: list[dict[str, Any]] = []
            seen_method_sets: set[tuple[str, ...]] = set()
            final_lab: dict[str, Any] | None = None
            resolved = False
    
            while time.time() < work_deadline:
                full_registry = load_json(full_registry_path, {})
                target_path = run_dir / "candidates.json"
                write_json(target_path, targeted_registry(full_registry, provider_id))
    
                attempt_no = int(state.get("attemptCount") or 0) + 1
                attempt_dir = run_dir / f"attempt-{attempt_no}"
                attempt_dir.mkdir(parents=True, exist_ok=True)
                repair = repair_attempt(provider_id, stage, target_path, attempt_dir, args.previous_state.resolve(), work_deadline)
                merge_target_candidate(full_registry_path, target_path, provider_id)
                for key, value in ((repair["report"].get("brain") or {}).get("plans") or {}).items():
                    combined_plans[str(key)] = value
                for row in repair["report"].get("rounds") or []:
                    if isinstance(row, dict):
                        tagged = copy.deepcopy(row)
                        tagged["providerId"] = provider_id
                        combined_rounds.append(tagged)
    
                full_registry = load_json(full_registry_path, {})
                candidate = candidate_map(full_registry).get(provider_id) or {}
                media_type = declared_type(candidate)
                fixture = choose_fixture(health_config, state, media_type)
                final_lab = run_lab(provider_id, target_path, stage, fixture, attempt_dir, work_deadline, args.stream_safety_cap)
                method_set = tuple(repair["attemptedProfiles"])
                provider_attempts.append({
                    "attempt": attempt_no,
                    "repairAccepted": repair["accepted"],
                    "attemptedProfiles": repair["attemptedProfiles"],
                    "lab": final_lab,
                })
                state["attemptCount"] = attempt_no
                state["lastAttemptAt"] = datetime.now(timezone.utc).isoformat()
                state["lastStatus"] = final_lab.get("status")
                state["lastFixture"] = final_lab.get("fixtureSlug")
                state["lastClients"] = final_lab.get("clients")
    
                if final_lab.get("status") == "playable":
                    resolved = True
                    break
    
                # If the Core did not initially suspect an access problem but the
                # independent Lab cannot reach any runtime, challenge the diagnosis
                # with a route search before abandoning the provider.
                any_runtime = any(int(x.get("runtimeStreams") or 0) > 0 for x in (final_lab.get("clients") or {}).values())
                if not any_runtime and route is None and time.time() < work_deadline:
                    route = route_search(provider_id, run_dir, work_deadline)
                    refresh_stage_routes(stage, work_deadline)
                    continue
    
                # Continue only while the previous cycle found a genuinely new method
                # or accepted progress. Repeating the exact same failed method is
                # learning evidence, not a reason to burn the remaining hour.
                if method_set in seen_method_sets or (not method_set and repair["accepted"] == 0):
                    break
                seen_method_sets.add(method_set)
                if repair["accepted"] == 0:
                    break
    
            processed.append(provider_id)
            if not resolved:
                retry_next.append(provider_id)
            run_results.append({
                "provider": provider_id,
                "coreHypothesis": info,
                "routeSearch": route,
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
        "processedProviders": processed,
        "processedProviderCount": len(processed),
        "budgetInterruptionProvider": interrupted_provider,
        "timeBudgetExhausted": queue["timeBudgetExhausted"],
        "retryProviders": queue["retryProviders"],
        "hiddenFailureProviders": hidden_core_failures,
        "results": run_results,
        "productionWritesAllowed": False,
        "publicationAllowed": False,
    }

    write_json(output / "learning-queue-state.json", queue)
    write_json(output / "learning-queue-summary.json", summary)
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
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
