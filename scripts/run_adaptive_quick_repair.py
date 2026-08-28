#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Run one bounded ARCHI2 Brain repair pass during routine refreshes.

Quick is now a real quick validation path. It no longer executes the deep health
profile and relabels it afterwards. The Brain classifies the current failure,
selects only compatible targeted repair profiles, learns validated successes,
and defers safely when its mutation/time/loop budget is exhausted.
"""
from __future__ import annotations

import argparse
import contextlib
import copy
import io
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
ADAPTIVE = SCRIPTS / "adaptive_runtime"
HEALTH_CONFIG = ROOT / "health-config.json"

sys.path.insert(0, str(ADAPTIVE))
sys.path.insert(1, str(SCRIPTS))

import runtime_repair  # noqa: E402
import deep_repair_loop as loop  # noqa: E402
import brain_repair_runtime as brain  # noqa: E402
from guard_nuvio_client_brain_compat import guard as guard_nuvio_client_brain_compat  # noqa: E402
from provider_purification import purify_candidate  # noqa: E402
from repair_identity_gate import automatic_repair_safety_gate  # noqa: E402

_loaded = Path(runtime_repair.__file__).resolve()
_expected = (ADAPTIVE / "runtime_repair.py").resolve()
if _loaded != _expected:
    raise SystemExit(f"adaptive runtime layer not loaded: {_loaded} != {_expected}")

_base_run_health = loop.run_health
_base_matching_profiles = loop.matching_profiles
_base_create_repair_candidate = loop.create_repair_candidate
_sibling_resolutions: dict[str, str] = {}


def _purified_create_repair_candidate(stage, candidate, profile_name, round_number):
    repaired, error = _base_create_repair_candidate(stage, candidate, profile_name, round_number)
    if not isinstance(repaired, dict):
        return repaired, error
    try:
        repaired, _purification = purify_candidate(Path(stage), repaired)
    except Exception as exc:
        try:
            target = (Path(stage).resolve() / str(repaired.get("local_path") or "")).resolve()
            target.relative_to((Path(stage).resolve() / "providers" / "runtime-repairs").resolve())
            target.unlink(missing_ok=True)
        except (ValueError, OSError):
            pass
        return None, f"purification_failed:{type(exc).__name__}:{exc}"
    return repaired, error


def _category_playable_totals(result: dict[str, Any]) -> dict[str, int]:
    totals: dict[str, int] = {}
    for row in result.get("tests") or []:
        if not isinstance(row, dict):
            continue
        fixture = row.get("fixture") if isinstance(row.get("fixture"), dict) else {}
        category = str(fixture.get("category") or fixture.get("mediaType") or "").casefold().strip()
        if category not in {"movie", "tv", "anime"}:
            continue
        totals[category] = max(totals.get(category, 0), int(row.get("streams_playable") or 0))
    return totals


def _declared_categories(candidate: dict[str, Any]) -> set[str]:
    metadata = candidate.get("metadata") if isinstance(candidate.get("metadata"), dict) else {}
    return {
        str(value).casefold()
        for value in metadata.get("supportedTypes") or []
        if str(value).casefold() in {"movie", "tv", "anime"}
    }


def _discover_sibling_resolutions(registry_path: Path, report: dict[str, Any]) -> dict[str, str]:
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    candidates = {
        str(row.get("key")): row
        for row in registry.get("candidates") or []
        if isinstance(row, dict) and row.get("key")
    }
    target_categories: dict[str, set[str]] = {}
    for candidate in candidates.values():
        cid = str(candidate.get("canonical_id") or candidate.get("upstream_id") or "").casefold()
        if cid:
            target_categories.setdefault(cid, set()).update(_declared_categories(candidate))

    choices: dict[str, tuple[tuple[int, int, int], str]] = {}
    for result in report.get("results") or []:
        if not isinstance(result, dict) or str(result.get("status") or "") != "healthy":
            continue
        key = str(result.get("key") or "")
        candidate = candidates.get(key)
        if candidate is None:
            continue
        cid = str(candidate.get("canonical_id") or candidate.get("upstream_id") or "").casefold()
        evidence = result.get("evidence") if isinstance(result.get("evidence"), dict) else {}
        healthy_categories = {
            str(value).casefold()
            for value in evidence.get("healthy_fixture_categories") or []
            if str(value).casefold() in {"movie", "tv", "anime"}
        }
        required = target_categories.get(cid, set())
        playable = int(evidence.get("streams_playable") or 0)
        payloads = int(evidence.get("payload_verified_streams") or 0)
        contradictions = int(evidence.get("identity_contradiction_count") or 0)
        duration_mismatches = int(evidence.get("duration_identity_mismatch_count") or 0)
        if playable <= 0 or payloads <= 0 or contradictions or duration_mismatches:
            continue
        if required and not required.issubset(healthy_categories):
            continue
        score = (int(result.get("score") or 0), playable, payloads)
        current = choices.get(cid)
        if current is None or score > current[0]:
            choices[cid] = (score, key)
    return {cid: key for cid, (_score, key) in choices.items()}


def _sibling_aware_matching_profiles(candidate: dict[str, Any], result: dict[str, Any], source_text: str, config: dict[str, Any] | None = None) -> list[str]:
    cid = str(candidate.get("canonical_id") or candidate.get("upstream_id") or "").casefold()
    winner = _sibling_resolutions.get(cid)
    if winner and str(candidate.get("key") or "") != winner:
        return []
    return _base_matching_profiles(candidate, result, source_text, config)


def _brain_matching_profiles(candidate: dict[str, Any], result: dict[str, Any], source_text: str, config: dict[str, Any] | None = None) -> list[str]:
    base = _sibling_aware_matching_profiles(candidate, result, source_text, config)
    key = str(candidate.get("key") or "")
    parent_key = str((candidate.get("runtime_repair") or {}).get("parent_key") or "")
    plan = brain.PLANS.get(parent_key or key) or {}
    if str(plan.get("action") or "") != "probe-targeted-repair":
        return []
    allowed = {str(value) for value in plan.get("allowedProfiles") or [] if str(value)}
    return [profile for profile in base if profile in allowed]


def _quick_compare_results(parent: dict[str, Any], repaired: dict[str, Any]) -> tuple[bool, str]:
    repaired_status = str(repaired.get("status") or "runtime_error")
    if repaired_status in runtime_repair.HARD_FAILURES:
        return False, f"hard_failure:{repaired_status}"
    if runtime_repair.runtime_error_count(repaired) > runtime_repair.runtime_error_count(parent):
        return False, "introduced_runtime_error"
    if runtime_repair.malformed_request_count(repaired) > runtime_repair.malformed_request_count(parent):
        return False, "introduced_malformed_request"
    safety_ok, safety_reason = automatic_repair_safety_gate(repaired)
    if not safety_ok:
        return False, safety_reason

    parent_categories = _category_playable_totals(parent)
    repaired_categories = _category_playable_totals(repaired)
    parent_playable_categories = {name for name, count in parent_categories.items() if count > 0}
    repaired_playable_categories = {name for name, count in repaired_categories.items() if count > 0}
    lost_categories = sorted(parent_playable_categories - repaired_playable_categories)
    if lost_categories:
        return False, "quick_category_regression:" + ",".join(lost_categories)

    parent_total = sum(parent_categories.values())
    repaired_total = sum(repaired_categories.values())
    parent_playable = runtime_repair.playable_stream_count(parent)
    repaired_playable = runtime_repair.playable_stream_count(repaired)
    category_gain = repaired_playable_categories > parent_playable_categories
    stream_gain = repaired_total > parent_total or repaired_playable > parent_playable
    runtime_gain = runtime_repair.quality_vector(repaired) > runtime_repair.quality_vector(parent)
    if category_gain or stream_gain or runtime_gain:
        return True, "provisional_quick_runtime_improvement"
    return False, "no_quick_runtime_improvement"


def _fallback_failure_class(result: dict[str, Any]) -> str:
    status = str(result.get("status") or "runtime_error")
    return {
        "blocked": "transport_blocked",
        "no_streams": "search_gap",
        "provider_unreachable": "unknown_failure",
        "unavailable": "transport_blocked",
        "runtime_error": "runtime_contract_drift",
        "degraded": "media_validation_gap",
        "reachable": "search_gap",
    }.get(status, "unknown_failure")


def _install_control_plane_fallback_plan(candidate: dict[str, Any], result: dict[str, Any], error: Exception) -> None:
    key = str(result.get("key") or candidate.get("key") or "")
    parent_key = str((candidate.get("runtime_repair") or {}).get("parent_key") or "")
    plan_key = parent_key or key
    if not plan_key:
        return
    evidence = result.get("evidence") if isinstance(result.get("evidence"), dict) else {}
    playable = int(evidence.get("streams_playable") or 0)
    status = str(result.get("status") or "runtime_error")
    provider_id = str(candidate.get("canonical_id") or candidate.get("upstream_id") or plan_key).casefold()
    if status == "healthy" and playable > 0:
        failure_class = "healthy"
        action = "none"
        allowed_profiles: list[str] = []
    elif status == "excluded":
        failure_class = "identity_mismatch"
        action = "none"
        allowed_profiles = []
    else:
        failure_class = _fallback_failure_class(result)
        if failure_class == "unknown_failure":
            action = "deferred_retry"
            allowed_profiles = []
        else:
            action = "probe-targeted-repair"
            allowed_profiles = ["adaptive_runtime_recovery"]
    brain.PLANS[plan_key] = {
        "brainVersion": 4,
        "providerId": provider_id,
        "failureClass": failure_class,
        "signature": f"control-plane-fallback:{failure_class}:{status}",
        "action": action,
        "exitReason": "planner_transport_fallback",
        "hypotheses": [],
        "allowedProfiles": allowed_profiles,
        "plannerErrorClass": type(error).__name__,
        "fallbackPolicy": "lkg_only_after_repair_budget",
        "coreMutationPolicy": "proposal_only",
    }


def _planner_mode() -> str:
    mode = str(os.environ.get("NUVIO_BRAIN_PLANNER_MODE") or "quick").strip().casefold()
    return "learning" if mode == "learning" else "quick"


def _plan_quick_results(registry_path: Path, report: dict[str, Any]) -> None:
    """Plan each runtime observation independently.

    A malformed or oversized control-plane payload must never prevent the other
    providers from entering Repair. Every result gets its own Node planner call;
    an isolated planner failure receives a bounded generic Repair plan instead of
    aborting the 92-provider refresh.
    """
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    candidates = {
        str(row.get("key")): row
        for row in registry.get("candidates") or []
        if isinstance(row, dict) and row.get("key")
    }
    planned = 0
    fallback_plans = 0
    for result in report.get("results") or []:
        if not isinstance(result, dict) or not result.get("key"):
            continue
        key = str(result.get("key") or "")
        candidate = candidates.get(key)
        if candidate is None:
            continue
        try:
            brain.update_plans(registry_path, {"results": [result]}, _planner_mode())
            planned += 1
        except RuntimeError as error:
            _install_control_plane_fallback_plan(candidate, result, error)
            fallback_plans += 1
    print(
        f"Core Quick isolated planning complete: planned={planned} fallback_plans={fallback_plans}",
        file=sys.stderr,
    )


def _quick_run_health(*, stage: Path, registry_path: Path, output_dir: Path, mode: str, health_check: Path = loop.HEALTH_CHECK) -> dict[str, Any]:
    report = _base_run_health(
        stage=stage,
        registry_path=registry_path,
        output_dir=output_dir,
        mode="quick",
        health_check=health_check,
    )
    if not _sibling_resolutions and registry_path.name == "candidates.json":
        _sibling_resolutions.update(_discover_sibling_resolutions(registry_path, report))
    _plan_quick_results(registry_path, report)
    return report


def _strengthen_quick_probe(config: dict[str, Any]) -> None:
    modes = config.setdefault("modes", {})
    deep = copy.deepcopy(modes.get("deep", {}) or {})
    quick = modes.setdefault("quick", {})
    quick["fixture_limit"] = max(3, int(quick.get("fixture_limit") or 1))
    quick["max_streams_to_probe"] = max(2, int(quick.get("max_streams_to_probe") or 1))
    quick["probe_best_variant"] = True
    quick["probe_first_segment"] = True
    quick["probe_streams_adaptively"] = True
    quick["verify_fixture_duration_identity"] = True
    quick["minimum_fixture_duration_ratio"] = float(quick.get("minimum_fixture_duration_ratio") or deep.get("minimum_fixture_duration_ratio") or 0.55)
    quick["maximum_fixture_duration_ratio"] = float(quick.get("maximum_fixture_duration_ratio") or deep.get("maximum_fixture_duration_ratio") or 1.8)


def _rewrite_mode_metadata(stage: Path, output: Path) -> None:
    sibling_ids = sorted(_sibling_resolutions)
    for path in (stage / "candidates.json", output / "health-results.json", output / "repair-report.json"):
        if not path.exists():
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["mode"] = "quick"
        runtime = payload.setdefault("runtime_repair", {}) if path.name != "repair-report.json" else payload
        runtime["validation_mode"] = "quick"
        planner_mode = _planner_mode()
        runtime["profile_persistence"] = "learning_memory" if planner_mode == "learning" else "none_core_repair_only"
        runtime["learning_executed"] = planner_mode == "learning"
        runtime["acceptance_policy"] = "healthy_sibling_then_core_type_repair"
        runtime["sibling_resolved_provider_count"] = len(sibling_ids)
        runtime["sibling_resolved_provider_ids"] = sibling_ids
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _run_domain_search_fallback(stage: Path, output: Path) -> None:
    script = SCRIPTS / "resolve_provider_hub_search_fallback.py"
    report = output / "provider-hub-report.json"
    if not script.exists() or not report.exists():
        return
    summary = output / "provider-hub-search-fallback.json"
    subprocess.run([
        sys.executable, str(script), "--report", str(report), "--output", str(summary),
        "--apply", "--max-providers", "12", "--timeout", "8"
    ], cwd=ROOT, check=True)
    payload = json.loads(summary.read_text(encoding="utf-8")) if summary.exists() else {}
    if int(payload.get("applied") or 0) <= 0:
        return
    subprocess.run([sys.executable, str(SCRIPTS / "build_provider_runtime_profiles.py"), "--stage", str(stage), "--apply-stage"], cwd=ROOT, check=True)
    subprocess.run([sys.executable, str(SCRIPTS / "normalize_terminal_quarantine_stage.py"), "--stage", str(stage)], cwd=ROOT, check=True)
    subprocess.run([sys.executable, str(SCRIPTS / "validate_override_pipeline.py"), "--stage", str(stage)], cwd=ROOT, check=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", type=Path, default=ROOT / "staging")
    parser.add_argument("--output", type=Path, default=ROOT / "health-output")
    parser.add_argument("--max-rounds", type=int, default=1)
    args = parser.parse_args()
    stage = args.stage.resolve()
    output = args.output.resolve()
    max_rounds = 1

    original_health_config = HEALTH_CONFIG.read_bytes()
    original_argv = list(sys.argv)
    original_compare = loop.compare_results
    original_run_health = loop.run_health
    original_persist = loop.persist_runtime_profiles
    original_matching = loop.matching_profiles
    original_create = loop.create_repair_candidate
    try:
        brain.reset_runtime_state()
        _sibling_resolutions.clear()
        config = json.loads(original_health_config.decode("utf-8"))
        _strengthen_quick_probe(config)
        HEALTH_CONFIG.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        # Core Quick repair may apply already-defined Core repair types, so it is
        # subject to the same official client-runtime drift fence as deep. Learning
        # remains a separate daily workflow and is never executed in Quick mode.
        guard_nuvio_client_brain_compat(output / "nuvio-client-upstream-status.json")
        _run_domain_search_fallback(stage, output)

        loop.compare_results = _quick_compare_results
        loop.run_health = _quick_run_health
        loop.matching_profiles = _brain_matching_profiles
        loop.create_repair_candidate = brain.wrap_create_repair_candidate(_purified_create_repair_candidate)
        loop.persist_runtime_profiles = lambda _config, _assignments: []
        sys.argv = [
            str(SCRIPTS / "deep_repair_loop.py"), "--stage", str(stage), "--output", str(output),
            "--mode", "deep", "--max-rounds", str(max_rounds),
        ]
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            rc = loop.main()
        for line in buffer.getvalue().splitlines():
            if line.startswith("Deep repair loop complete:"):
                print(line.replace("Deep repair loop complete:", "Core Quick repair loop complete:", 1))
            else:
                print(line)
        _rewrite_mode_metadata(stage, output)
        brain.annotate_and_learn(output, _planner_mode())
        return int(rc)
    finally:
        HEALTH_CONFIG.write_bytes(original_health_config)
        sys.argv = original_argv
        loop.compare_results = original_compare
        loop.run_health = original_run_health
        loop.matching_profiles = original_matching
        loop.create_repair_candidate = original_create
        loop.persist_runtime_profiles = original_persist


if __name__ == "__main__":
    raise SystemExit(main())
