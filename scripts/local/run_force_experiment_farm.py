#!/usr/bin/env python3
"""Local FORCE experiment farm for NiakVIO.

Purpose:
- screen many deterministic Brain advisor experiments locally with Quick;
- Deep-validate only experiments that show provisional Quick improvement;
- isolate every provider in a detached worktree;
- resume by experiment fingerprint;
- never publish, push, dispatch workflows, or mutate the caller checkout.

The output is local evidence only. GitHub FORCE remains the publication/current-
byte authority and must revalidate any winning guidance before production use.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import copy
import hashlib
import itertools
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import brain_llm_experiment as experiment_contract  # noqa: E402
import brain_llm_guidance as guidance_contract  # noqa: E402

STATUS = ROOT / "automation" / "provider-census-status.json"
NEGATIVE_MEMORY = ROOT / "automation" / "brain-repair-memory.json"
DEFAULT_OUTPUT = ROOT / "local-output" / "force-experiment-farm"

STATUS_TEMPLATES: dict[str, tuple[str, str, str]] = {
    "ROUTE PROVEN": (
        "route-proven-gap",
        "proven_route_terminal_traversal_v1",
        "search-detail-player-terminal-traversal",
    ),
    "CHAIN REACHED": (
        "chain-terminal-gap",
        "chain_terminal_extractor_v1",
        "terminal-media-extractor-with-playback-validation",
    ),
    "CANDIDATE OK": (
        "candidate-replay-gap",
        "retained_candidate_replay_v1",
        "same-provider-candidate-program-replay",
    ),
    "PROVIDER NETWORK BLOCKED": (
        "provider-transport-gap",
        "provider_origin_failover_v1",
        "provider-owned-origin-header-and-domain-replay",
    ),
}
FALLBACK_TEMPLATE = (
    "media-extraction-gap",
    "search_contract_inference_v1",
    "discover-api-from-current-page-and-bundles",
)

ROLE_ORDERS = [
    ["search", "detail", "episode", "player", "source", "api", "other"],
    ["player", "source", "api", "episode", "detail", "search", "other"],
    ["api", "search", "detail", "player", "source", "episode", "other"],
    ["detail", "episode", "player", "source", "api", "search", "other"],
    ["source", "player", "api", "detail", "episode", "search", "other"],
    ["episode", "detail", "player", "source", "api", "search", "other"],
]
BOOLEAN_PROFILES = [
    (False, False, False, False, False),
    (False, True, False, False, False),
    (False, False, True, False, False),
    (False, False, False, True, False),
    (False, False, False, False, True),
    (True, False, True, False, False),
    (True, True, True, False, False),
    (False, True, True, True, True),
]
BUDGETS = [
    (3, 12, 12, 2),
    (4, 18, 20, 3),
    (5, 24, 28, 4),
    (6, 36, 36, 6),
]

_state_lock = threading.RLock()
_git_lock = threading.Lock()


def canon(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def atomic_write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    tmp.replace(path)


def git_output(*args: str, cwd: Path = ROOT) -> str:
    return subprocess.check_output(
        ["git", *args],
        cwd=cwd,
        text=True,
        stderr=subprocess.DEVNULL,
    ).strip()


def current_sha() -> str:
    try:
        inside = git_output("rev-parse", "--is-inside-work-tree").strip().casefold()
        if inside != "true":
            raise RuntimeError("not a Git worktree")
        return git_output("rev-parse", "HEAD").casefold()
    except (subprocess.CalledProcessError, RuntimeError) as exc:
        raise SystemExit(
            "Local FORCE farm requires a real Git clone because it isolates providers "
            "with git worktree. This directory has no usable .git metadata. "
            "Clone NiakVIO with git clone, cd into that clone, then rerun the command."
        ) from exc


def status_rows() -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    payload = load_json(STATUS, {})
    rows = {
        canon(row.get("provider")): row
        for row in payload.get("providers") or []
        if isinstance(row, dict) and canon(row.get("provider"))
    }
    return payload, rows


def template_for_status(row: dict[str, Any]) -> tuple[str, str, str]:
    status = str(row.get("status") or "").strip().upper()
    if status in STATUS_TEMPLATES:
        return STATUS_TEMPLATES[status]
    issue = str(row.get("dominantIssue") or "").casefold()
    if "transport" in issue or "network" in issue or "origin" in issue:
        return STATUS_TEMPLATES["PROVIDER NETWORK BLOCKED"]
    if "terminal" in issue or "chain" in issue:
        return STATUS_TEMPLATES["CHAIN REACHED"]
    if "route" in issue:
        return STATUS_TEMPLATES["ROUTE PROVEN"]
    if "candidate" in issue:
        return STATUS_TEMPLATES["CANDIDATE OK"]
    return FALLBACK_TEMPLATE


def negative_experiment_keys(provider: str) -> set[tuple[str, str]]:
    """Executed negative evidence is scoped to profile + experiment fingerprint."""
    payload = load_json(NEGATIVE_MEMORY, {})
    rows: list[dict[str, Any]] = []
    for raw in payload.get("entries") or []:
        if isinstance(raw, dict):
            rows.append(raw)
    memory = payload.get("experimentMemory")
    if isinstance(memory, dict):
        for raw in memory.get("entries") or []:
            if isinstance(raw, dict):
                rows.append(raw)
    out: set[tuple[str, str]] = set()
    for row in rows:
        if canon(row.get("providerId")) != provider:
            continue
        fp = str(row.get("llmAdvisorExperimentFingerprint") or "").strip().casefold()
        profile = str(row.get("profile") or "").strip().casefold()
        observed = row.get("executionObserved") is True
        failed = int(row.get("failures") or 0) > 0 or int(row.get("consecutiveFailures") or 0) > 0
        if len(fp) == 64 and profile and observed and failed:
            out.add((profile, fp))
    return out


def _row(
    provider: str,
    *,
    failure: str,
    profile: str,
    strategy: str,
    experiment: dict[str, Any],
    confidence: float = 0.95,
    source: str = "generated-local-grid",
) -> dict[str, Any]:
    clean, fingerprint = experiment_contract.validate_public(experiment)
    return {
        "providerId": provider,
        "failureClass": failure,
        "targetLayer": "provider",
        "strategy": strategy,
        "profile": profile,
        "confidence": max(0.80, min(1.0, float(confidence))),
        "priorOnly": True,
        "experiment": clean,
        "experimentFingerprint": fingerprint,
        "localExperimentSource": source,
    }


def generated_experiments(
    provider: str,
    row: dict[str, Any],
    limit: int,
) -> list[dict[str, Any]]:
    """Generate a strategy-diverse, deterministic experiment portfolio.

    The previous farm varied every low-level experiment knob while keeping one
    status-selected high-level strategy/profile fixed. That produced many
    fingerprints without exploring materially different repair families. Keep
    the status-selected family first, then round-robin all executable advisor
    strategies so a 24-variant budget covers the full strategy vocabulary.
    """
    failure, preferred_profile, preferred_strategy = template_for_status(row)
    strategy_pairs = list(guidance_contract.STRATEGY_TO_PROFILE.items())
    strategy_pairs.sort(key=lambda pair: (pair[0] != preferred_strategy, pair[0]))

    result: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()

    def append(strategy: str, profile: str, exp: dict[str, Any], source: str) -> None:
        item = _row(
            provider,
            failure=failure,
            profile=profile,
            strategy=strategy,
            experiment=exp,
            source=source,
        )
        key = (profile, item["experimentFingerprint"])
        if key not in seen:
            seen.add(key)
            result.append(item)

    # One canonical base per executable strategy gives every family at least
    # one chance even under a small local experiment budget.
    for strategy, profile in strategy_pairs:
        append(
            strategy,
            profile,
            experiment_contract.from_proposal({}, strategy=strategy),
            "generated-strategy-base",
        )
        if len(result) >= max(1, limit):
            return result[: max(1, limit)]

    per_strategy: dict[str, list[dict[str, Any]]] = {}
    for strategy, profile in strategy_pairs:
        base = experiment_contract.from_proposal({}, strategy=strategy)
        candidates: list[dict[str, Any]] = []
        local_seen: set[str] = set()
        for route, recipe, roles, bools, budget in itertools.product(
            sorted(experiment_contract.ROUTE_POLICIES),
            sorted(experiment_contract.RECIPE_POLICIES),
            ROLE_ORDERS,
            BOOLEAN_PROFILES,
            BUDGETS,
        ):
            terminal, alias, salvage, mining, session = bools
            depth, pages, embeds, recipe_passes = budget
            exp = copy.deepcopy(base)
            exp.update(
                {
                    "routePolicy": route,
                    "recipePolicy": recipe,
                    "roleOrder": list(roles),
                    "terminalOnly": terminal,
                    "aliasSearch": alias,
                    "responseSalvage": salvage,
                    "documentRequestMining": mining,
                    "sessionBootstrap": session,
                    "maxDepth": depth,
                    "maxPages": pages,
                    "maxEmbeds": embeds,
                    "maxRecipePasses": recipe_passes,
                }
            )
            try:
                clean, fp = experiment_contract.validate_public(exp)
            except ValueError:
                continue
            if fp in local_seen:
                continue
            local_seen.add(fp)
            candidates.append({"experiment": clean, "fingerprint": fp})
        candidates.sort(
            key=lambda item: hashlib.sha256(
                f"{provider}:{strategy}:{item['fingerprint']}".encode("utf-8")
            ).hexdigest()
        )
        per_strategy[strategy] = candidates

    # Round-robin strategy families instead of spending the first 24 variants
    # inside one family.
    cursor = 0
    while len(result) < max(1, limit):
        progressed = False
        for strategy, profile in strategy_pairs:
            candidates = per_strategy.get(strategy) or []
            if cursor >= len(candidates):
                continue
            item = candidates[cursor]
            append(strategy, profile, item["experiment"], "generated-diverse-strategy-grid")
            progressed = True
            if len(result) >= max(1, limit):
                break
        if not progressed:
            break
        cursor += 1
    return result[: max(1, limit)]


def discover_guidance(path: Path | None) -> dict[str, Any]:
    candidates = []
    if path is not None:
        candidates.append(path.expanduser().resolve())
    candidates.extend(
        [
            ROOT / "engine_v2" / "learning" / "llm-guidance.json",
            ROOT.parent / "NiakVIO-Brain-LLM" / "guidance" / "niakvio-guidance.json",
        ]
    )
    for candidate in candidates:
        if candidate.is_file():
            return load_json(candidate, {})

    # Offline-safe fallback: reuse an already-fetched proposal ref without
    # contacting GitHub. Failure simply means generated local variants only.
    try:
        raw = subprocess.check_output(
            [
                "git",
                "show",
                "refs/remotes/origin/brain-learning/proposals:engine_v2/learning/llm-guidance.json",
            ],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        )
        value = json.loads(raw)
        return value if isinstance(value, dict) else {}
    except (subprocess.SubprocessError, json.JSONDecodeError):
        return {}


def external_rows(payload: dict[str, Any], provider: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for raw in payload.get("rows") or []:
        if not isinstance(raw, dict) or canon(raw.get("providerId")) != provider:
            continue
        if str(raw.get("targetLayer") or "").casefold() != "provider":
            continue
        if raw.get("priorOnly") is not True:
            continue
        try:
            clean, fp = experiment_contract.validate_public(
                raw.get("experiment"),
                str(raw.get("experimentFingerprint") or ""),
            )
        except ValueError:
            continue
        item = copy.deepcopy(raw)
        item["providerId"] = provider
        item["experiment"] = clean
        item["experimentFingerprint"] = fp
        item["confidence"] = max(0.80, min(1.0, float(item.get("confidence") or 0.8)))
        item["localExperimentSource"] = "existing-guidance"
        out.append(item)
    return out


def experiment_rows(
    provider: str,
    row: dict[str, Any],
    guidance: dict[str, Any],
    limit: int,
) -> list[dict[str, Any]]:
    failed = negative_experiment_keys(provider)
    ordered = external_rows(guidance, provider) + generated_experiments(provider, row, limit * 2)
    out: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for item in ordered:
        fp = str(item.get("experimentFingerprint") or "").casefold()
        profile = str(item.get("profile") or "").casefold()
        key = (profile, fp)
        if not fp or not profile or key in failed or key in seen:
            continue
        seen.add(key)
        out.append(item)
        if len(out) >= limit:
            break
    return out


def guidance_payload(sha: str, row: dict[str, Any]) -> dict[str, Any]:
    return {
        "schemaVersion": 2,
        "sourceSha": sha,
        "sourceNiakvioSha": sha,
        "directMutationAuthority": False,
        "publicationAuthority": False,
        "proofAuthority": False,
        "rawMutationContentRetained": False,
        "privateContentRetained": False,
        "providerCount": 1,
        "rows": [copy.deepcopy(row)],
    }


def experiment_state_key(row: dict[str, Any]) -> str:
    strategy = str(row.get("strategy") or "").strip().casefold()
    profile = str(row.get("profile") or "").strip().casefold()
    fp = str(row.get("experimentFingerprint") or "").strip().casefold()
    return hashlib.sha256(f"{strategy}:{profile}:{fp}".encode("utf-8")).hexdigest()


def accepted_events(report: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for round_row in report.get("rounds") or []:
        if not isinstance(round_row, dict):
            continue
        for event in round_row.get("accepted") or []:
            if isinstance(event, dict):
                out.append(copy.deepcopy(event))
    return out


def deep_baseline_healthy_result(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    if value.get("deepBaselineHealthy") is True:
        return True
    health = value.get("deepHealth") if isinstance(value.get("deepHealth"), dict) else {}
    return (
        str(health.get("status") or "").casefold() == "healthy"
        and int(health.get("streamsPlayable") or 0) > 0
    )


def report_summary(report: dict[str, Any]) -> dict[str, Any]:
    accepted = accepted_events(report)
    rounds = [row for row in (report.get("rounds") or []) if isinstance(row, dict)]
    generated = sum(max(0, int(row.get("generated_candidates") or 0)) for row in rounds)
    exploration = sum(len(row.get("exploration_progress") or []) for row in rounds)
    return {
        "acceptedRepairs": int(report.get("accepted_repairs") or 0),
        "generatedCandidates": generated,
        "explorationProgressCount": exploration,
        "finalCounts": copy.deepcopy(report.get("final_counts") or {}),
        "accepted": accepted[:8],
    }


def provider_health_summary(path: Path, provider: str) -> dict[str, Any]:
    payload = load_json(path, {})
    rows = [
        row for row in payload.get("results") or []
        if isinstance(row, dict)
        and (
            canon(row.get("provider")) == provider
            or canon(row.get("provider_id")) == provider
            or canon(str(row.get("key") or "").split(":")[-1]) == provider
        )
    ]
    row = rows[0] if rows else {}
    evidence = row.get("evidence") if isinstance(row.get("evidence"), dict) else {}
    return {
        "status": str(row.get("status") or ""),
        "score": int(row.get("score") or 0),
        "streamsPlayable": int(evidence.get("streams_playable") or 0),
        "streamsReturned": int(evidence.get("streams_returned") or 0),
        "identityContradictions": int(evidence.get("identity_contradiction_count") or 0),
    }


def run_logged(
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str],
    log_path: Path,
    timeout: int,
) -> tuple[int, str]:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    try:
        with log_path.open("w", encoding="utf-8") as handle:
            proc = subprocess.run(
                command,
                cwd=cwd,
                env=env,
                stdout=handle,
                stderr=subprocess.STDOUT,
                timeout=timeout,
                check=False,
                text=True,
            )
        return int(proc.returncode), f"rc={proc.returncode};elapsed={time.monotonic()-started:.1f}"
    except subprocess.TimeoutExpired:
        return 124, f"timeout;elapsed={time.monotonic()-started:.1f}"


def link_shared_local_tooling(worktree: Path) -> None:
    """Reuse immutable local tooling without sharing mutable experiment state."""
    for name in ("node_modules",):
        source = ROOT / name
        target = worktree / name
        if not source.exists() or target.exists() or target.is_symlink():
            continue
        try:
            target.symlink_to(source, target_is_directory=True)
        except OSError:
            # Cache sharing is an optimization only; the experiment remains
            # valid when the sandbox has to rebuild/fetch its own tooling.
            pass


def reset_worktree(worktree: Path, sha: str) -> None:
    subprocess.run(["git", "reset", "--hard", sha], cwd=worktree, check=True, stdout=subprocess.DEVNULL)
    subprocess.run(["git", "clean", "-fdx"], cwd=worktree, check=True, stdout=subprocess.DEVNULL)
    link_shared_local_tooling(worktree)


def prepare_stage(
    worktree: Path,
    provider: str,
    root: Path,
    guidance: dict[str, Any],
) -> tuple[Path, Path, Path]:
    root.mkdir(parents=True, exist_ok=True)
    targets = root / "targets.json"
    guidance_path = root / "guidance.json"
    stage = root / "stage"
    targets.write_text(
        json.dumps({"targets": [{"id": provider}]}, indent=2) + "\n",
        encoding="utf-8",
    )
    guidance_path.write_text(
        json.dumps(guidance, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    subprocess.run(
        [
            sys.executable,
            "scripts/stage_published.py",
            "--stage",
            str(stage),
            "--include-file",
            str(targets),
        ],
        cwd=worktree,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return stage, guidance_path, root / "output"


def persist_state(output: Path, state: dict[str, Any]) -> None:
    with _state_lock:
        atomic_write_json(output / "STATE.json", state)
        winners = []
        for provider, rows in sorted((state.get("results") or {}).items()):
            for fp, result in sorted((rows or {}).items()):
                if isinstance(result, dict) and result.get("deepAccepted") is True:
                    guidance = result.get("guidance")
                    if isinstance(guidance, dict):
                        winners.append(copy.deepcopy(guidance))
        atomic_write_json(
            output / "WINNING_GUIDANCE.json",
            {
                "schemaVersion": 2,
                "sourceSha": state.get("sourceSha"),
                "directMutationAuthority": False,
                "publicationAuthority": False,
                "proofAuthority": False,
                "rawMutationContentRetained": False,
                "privateContentRetained": False,
                "providerCount": len({canon(row.get("providerId")) for row in winners}),
                "rows": winners,
            },
        )
        summary = {
            "schemaVersion": 1,
            "sourceSha": state.get("sourceSha"),
            "providerCount": len(state.get("providers") or []),
            "experimentCount": sum(len(rows or {}) for rows in (state.get("results") or {}).values()),
            "deepWinnerProviders": sorted(
                provider
                for provider, rows in (state.get("results") or {}).items()
                if any(isinstance(item, dict) and item.get("deepAccepted") is True for item in (rows or {}).values())
            ),
            "deepBaselineHealthyProviders": sorted(
                provider
                for provider, rows in (state.get("results") or {}).items()
                if any(deep_baseline_healthy_result(item) for item in (rows or {}).values())
            ),
            "quickAcceptedExperiments": sum(
                1
                for rows in (state.get("results") or {}).values()
                for item in (rows or {}).values()
                if isinstance(item, dict) and item.get("quickAccepted") is True
            ),
            "quickPromisingExperiments": sum(
                1
                for rows in (state.get("results") or {}).values()
                for item in (rows or {}).values()
                if isinstance(item, dict) and item.get("quickPromising") is True
            ),
            "quickExplorationProgress": sum(
                int(((item.get("quick") or {}).get("explorationProgressCount") or 0))
                for rows in (state.get("results") or {}).values()
                for item in (rows or {}).values()
                if isinstance(item, dict)
            ),
            "generatedCandidates": sum(
                int(((item.get("quick") or {}).get("generatedCandidates") or 0))
                for rows in (state.get("results") or {}).values()
                for item in (rows or {}).values()
                if isinstance(item, dict)
            ),
            "strategyCounts": {
                strategy: sum(
                    1
                    for rows in (state.get("results") or {}).values()
                    for item in (rows or {}).values()
                    if isinstance(item, dict) and item.get("strategy") == strategy
                )
                for strategy in sorted({
                    str(item.get("strategy") or "")
                    for rows in (state.get("results") or {}).values()
                    for item in (rows or {}).values()
                    if isinstance(item, dict) and str(item.get("strategy") or "")
                })
            },
            "publicationPerformed": False,
            "githubWorkflowDispatched": False,
            "learningPlannerModeExecuted": False,
            "clientDriftGuardSkippedForLocalExperiments": True,
        }
        atomic_write_json(output / "SUMMARY.json", summary)


def provider_worker(
    *,
    provider: str,
    row: dict[str, Any],
    experiments: list[dict[str, Any]],
    sha: str,
    output: Path,
    work_root: Path,
    state: dict[str, Any],
    quick_timeout: int,
    deep_timeout: int,
    deep_rounds: int,
    continue_after_win: bool,
    rerun: bool,
) -> dict[str, Any]:
    provider_dir = output / "providers" / provider
    provider_dir.mkdir(parents=True, exist_ok=True)
    worktree = work_root / provider
    with _git_lock:
        subprocess.run(
            ["git", "worktree", "add", "--detach", str(worktree), sha],
            cwd=ROOT,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    try:
        existing = (state.setdefault("results", {}).setdefault(provider, {}))
        if not continue_after_win and any(
            isinstance(value, dict) and value.get("deepAccepted") is True
            for value in existing.values()
        ):
            return {"provider": provider, "deepAccepted": True, "deepBaselineHealthy": False, "skipped": "winner-already-recorded"}
        if not continue_after_win and any(
            deep_baseline_healthy_result(value)
            for value in existing.values()
        ):
            return {"provider": provider, "deepAccepted": False, "deepBaselineHealthy": True, "skipped": "deep-baseline-healthy-already-recorded"}

        for index, guidance_row in enumerate(experiments, start=1):
            fp = str(guidance_row.get("experimentFingerprint") or "").casefold()
            if not fp:
                continue
            state_key = experiment_state_key(guidance_row)
            if not rerun and state_key in existing:
                if not continue_after_win and existing[state_key].get("deepAccepted") is True:
                    break
                continue

            reset_worktree(worktree, sha)
            local_root = worktree / ".local-force-farm"
            payload = guidance_payload(sha, guidance_row)
            env = os.environ.copy()
            env["GITHUB_SHA"] = sha
            env["NIAKVIO_BRAIN_LLM_GUIDANCE"] = str(local_root / "quick" / "guidance.json")
            env["NUVIO_BRAIN_EXPLORATION_CHAIN"] = "1"
            env["NUVIO_HEALTH_CONCURRENCY"] = "1"
            # Local experiment worktrees are non-authoritative and cannot
            # reliably verify all upstream client repositories. Production
            # publication remains fenced by GitHub FORCE, which re-runs the
            # real client drift guard before accepting any winner.
            env["NIAKVIO_SKIP_CLIENT_DRIFT_GUARD"] = "1"
            env.pop("NUVIO_BRAIN_PLANNER_MODE", None)

            result: dict[str, Any] = {
                "provider": provider,
                "experimentIndex": index,
                "experimentFingerprint": fp,
                "strategy": str(guidance_row.get("strategy") or ""),
                "profile": str(guidance_row.get("profile") or ""),
                "guidance": copy.deepcopy(guidance_row),
                "quickAccepted": False,
                "quickPromising": False,
                "deepAccepted": False,
                "deepBaselineHealthy": False,
                "publicationPerformed": False,
            }
            quick_log = provider_dir / f"{index:03d}-{fp[:12]}-quick.log"
            try:
                quick_stage, quick_guidance, quick_out = prepare_stage(
                    worktree, provider, local_root / "quick", payload
                )
                env["NIAKVIO_BRAIN_LLM_GUIDANCE"] = str(quick_guidance)
                rc, runtime = run_logged(
                    [
                        sys.executable,
                        "scripts/run_adaptive_quick_repair.py",
                        "--stage",
                        str(quick_stage),
                        "--registry",
                        str(quick_stage / "candidates.json"),
                        "--output",
                        str(quick_out),
                        "--max-rounds",
                        "1",
                    ],
                    cwd=worktree,
                    env=env,
                    log_path=quick_log,
                    timeout=quick_timeout,
                )
                quick_report = load_json(quick_out / "repair-report.json", {})
                result["quickReturnCode"] = rc
                result["quickRuntime"] = runtime
                result["quick"] = report_summary(quick_report)
                result["quickHealth"] = provider_health_summary(
                    quick_out / "health-results.json", provider
                )
                quick_summary = result["quick"]
                result["quickAccepted"] = int(quick_summary.get("acceptedRepairs") or 0) > 0
                result["quickPromising"] = (
                    result["quickAccepted"]
                    or int(quick_summary.get("explorationProgressCount") or 0) > 0
                )
            except (OSError, subprocess.SubprocessError, ValueError) as exc:
                result["quickError"] = f"{type(exc).__name__}:{str(exc)[:500]}"

            if result["quickPromising"]:
                # Deep starts again from exact current bytes, never from Quick's
                # provisional candidate.
                reset_worktree(worktree, sha)
                local_root = worktree / ".local-force-farm"
                deep_log = provider_dir / f"{index:03d}-{fp[:12]}-deep.log"
                try:
                    deep_stage, deep_guidance, deep_out = prepare_stage(
                        worktree, provider, local_root / "deep", payload
                    )
                    env["NIAKVIO_BRAIN_LLM_GUIDANCE"] = str(deep_guidance)
                    rc, runtime = run_logged(
                        [
                            sys.executable,
                            "scripts/run_adaptive_deep_repair.py",
                            "--stage",
                            str(deep_stage),
                            "--registry",
                            str(deep_stage / "candidates.json"),
                            "--output",
                            str(deep_out),
                            "--max-rounds",
                            str(deep_rounds),
                        ],
                        cwd=worktree,
                        env=env,
                        log_path=deep_log,
                        timeout=deep_timeout,
                    )
                    deep_report = load_json(deep_out / "repair-report.json", {})
                    result["deepReturnCode"] = rc
                    result["deepRuntime"] = runtime
                    result["deep"] = report_summary(deep_report)
                    result["deepHealth"] = provider_health_summary(
                        deep_out / "health-results.json", provider
                    )
                    result["deepBaselineHealthy"] = (
                        str(result["deepHealth"].get("status") or "").casefold() == "healthy"
                        and int(result["deepHealth"].get("streamsPlayable") or 0) > 0
                    )
                    result["deepAccepted"] = int(deep_report.get("accepted_repairs") or 0) > 0
                    if result["deepAccepted"]:
                        programs = [
                            event.get("accepted_program")
                            for event in accepted_events(deep_report)
                            if isinstance(event.get("accepted_program"), dict)
                            and event.get("accepted_program")
                        ]
                        result["acceptedPrograms"] = programs[:4]
                except (OSError, subprocess.SubprocessError, ValueError) as exc:
                    result["deepError"] = f"{type(exc).__name__}:{str(exc)[:500]}"

            with _state_lock:
                existing[state_key] = result
                persist_state(output, state)
            print(
                "FIELD_LOCAL_FORCE_EXPERIMENT "
                f"provider={provider} index={index}/{len(experiments)} fp={fp[:12]} "
                f"profile={result['profile']} "
                f"quick={str(result['quickAccepted']).lower()} "
                f"promising={str(result['quickPromising']).lower()} "
                f"deep={str(result['deepAccepted']).lower()} "
                f"baseline_healthy={str(result['deepBaselineHealthy']).lower()}",
                flush=True,
            )
            if (result["deepAccepted"] or result["deepBaselineHealthy"]) and not continue_after_win:
                break
        return {
            "provider": provider,
            "deepAccepted": any(
                isinstance(value, dict) and value.get("deepAccepted") is True
                for value in existing.values()
            ),
            "deepBaselineHealthy": any(
                deep_baseline_healthy_result(value)
                for value in existing.values()
            ),
            "experimentsRecorded": len(existing),
        }
    finally:
        with _git_lock:
            subprocess.run(
                ["git", "worktree", "remove", "--force", str(worktree)],
                cwd=ROOT,
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            subprocess.run(
                ["git", "worktree", "prune"],
                cwd=ROOT,
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", action="append", default=[])
    parser.add_argument("--provider-file", type=Path)
    parser.add_argument("--guidance", type=Path)
    parser.add_argument("--variants-per-provider", type=int, default=24)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--quick-timeout", type=int, default=240)
    parser.add_argument("--deep-timeout", type=int, default=900)
    parser.add_argument("--deep-rounds", type=int, default=3)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--work-root", type=Path)
    parser.add_argument("--continue-after-win", action="store_true")
    parser.add_argument("--rerun", action="store_true")
    args = parser.parse_args()

    sha = current_sha()
    census, rows = status_rows()
    requested = {canon(value) for value in args.provider if canon(value)}
    if args.provider_file and args.provider_file.is_file():
        for line in args.provider_file.read_text(encoding="utf-8").splitlines():
            if canon(line):
                requested.add(canon(line))
    queue = {canon(value) for value in census.get("repairQueue") or [] if canon(value)}
    providers = sorted(requested & queue) if requested else sorted(queue)
    if not providers:
        raise SystemExit("no providers selected from current census repairQueue")

    variants = max(1, min(int(args.variants_per_provider), 96))
    workers = max(1, min(int(args.workers), 8, len(providers)))
    quick_timeout = max(60, min(int(args.quick_timeout), 1800))
    deep_timeout = max(120, min(int(args.deep_timeout), 3600))
    deep_rounds = max(1, min(int(args.deep_rounds), 5))
    output = args.output.expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)

    guidance = discover_guidance(args.guidance)
    experiments_by_provider = {
        provider: experiment_rows(provider, rows.get(provider) or {}, guidance, variants)
        for provider in providers
    }
    state_path = output / "STATE.json"
    previous = load_json(state_path, {})
    if previous.get("sourceSha") == sha and isinstance(previous.get("results"), dict):
        state = previous
    else:
        state = {
            "schemaVersion": 1,
            "sourceSha": sha,
            "providers": providers,
            "results": {},
            "publicationPerformed": False,
            "githubWorkflowDispatched": False,
            "learningPlannerModeExecuted": False,
        }
    state["providers"] = providers
    state["experimentBudgetPerProvider"] = variants
    state["workerCount"] = workers
    persist_state(output, state)

    owned_work_root = args.work_root is None
    work_root = (
        Path(tempfile.mkdtemp(prefix="niakvio-local-force-farm-"))
        if owned_work_root
        else args.work_root.expanduser().resolve()
    )
    work_root.mkdir(parents=True, exist_ok=True)

    print(
        "FIELD_LOCAL_FORCE_FARM "
        f"sha={sha} providers={len(providers)} variants={variants} workers={workers} "
        f"quick_then_deep=true output={output}",
        flush=True,
    )
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
            futures = [
                pool.submit(
                    provider_worker,
                    provider=provider,
                    row=rows.get(provider) or {},
                    experiments=experiments_by_provider[provider],
                    sha=sha,
                    output=output,
                    work_root=work_root,
                    state=state,
                    quick_timeout=quick_timeout,
                    deep_timeout=deep_timeout,
                    deep_rounds=deep_rounds,
                    continue_after_win=args.continue_after_win,
                    rerun=args.rerun,
                )
                for provider in providers
            ]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        persist_state(output, state)
        winners = sorted(
            row["provider"]
            for row in results
            if row.get("deepAccepted") is True
        )
        baseline_healthy = sorted(
            row["provider"]
            for row in results
            if row.get("deepBaselineHealthy") is True
        )
        print(
            "FIELD_LOCAL_FORCE_FARM_DONE "
            f"providers={len(providers)} winners={len(winners)} "
            f"ids={','.join(winners) or 'none'} "
            f"baseline_healthy={','.join(baseline_healthy) or 'none'}",
            flush=True,
        )
        return 0
    finally:
        if owned_work_root:
            shutil.rmtree(work_root, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
