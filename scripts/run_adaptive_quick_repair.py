#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Run one bounded adaptive repair pass during routine provider refreshes.

Routine refresh is repair-first at the *canonical provider* level:

1. test every discovered upstream sibling;
2. when one sibling already proves every declared catalogue category, treat the
   provider as structurally resolved and do not waste repair attempts on its
   broken siblings;
3. only unresolved provider families enter structural adaptive repair;
4. keep a repair only when it improves coverage/runtime without introducing a
   positive identity/duration contradiction.

This makes variant selection the cheapest and safest repair strategy. Deep
remains stricter for durable profile learning and broader corpus proof.
"""
from __future__ import annotations

import argparse
import copy
import json
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
from repair_identity_gate import automatic_repair_safety_gate  # noqa: E402

_loaded = Path(runtime_repair.__file__).resolve()
_expected = (ADAPTIVE / "runtime_repair.py").resolve()
if _loaded != _expected:
    raise SystemExit(f"adaptive runtime layer not loaded: {_loaded} != {_expected}")

_base_run_health = loop.run_health
_base_matching_profiles = loop.matching_profiles
_sibling_resolutions: dict[str, str] = {}


def _category_playable_totals(result: dict[str, Any]) -> dict[str, int]:
    totals: dict[str, int] = {}
    for row in result.get("tests") or []:
        if not isinstance(row, dict):
            continue
        fixture = row.get("fixture") if isinstance(row.get("fixture"), dict) else {}
        category = str(fixture.get("category") or fixture.get("mediaType") or "").casefold().strip()
        if category not in {"movie", "tv", "anime"}:
            continue
        playable = int(row.get("streams_playable") or 0)
        totals[category] = max(totals.get(category, 0), playable)
    return totals


def _declared_categories(candidate: dict[str, Any]) -> set[str]:
    metadata = candidate.get("metadata") if isinstance(candidate.get("metadata"), dict) else {}
    return {
        str(value).casefold()
        for value in metadata.get("supportedTypes") or []
        if str(value).casefold() in {"movie", "tv", "anime"}
    }


def _discover_sibling_resolutions(
    registry_path: Path,
    report: dict[str, Any],
) -> dict[str, str]:
    """Return canonical IDs already solved by one fully proven sibling."""
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
        score = (
            int(result.get("score") or 0),
            playable,
            payloads,
        )
        current = choices.get(cid)
        if current is None or score > current[0]:
            choices[cid] = (score, key)
    return {cid: key for cid, (_score, key) in choices.items()}


def _sibling_aware_matching_profiles(
    candidate: dict[str, Any],
    result: dict[str, Any],
    source_text: str,
    config: dict[str, Any] | None = None,
) -> list[str]:
    cid = str(candidate.get("canonical_id") or candidate.get("upstream_id") or "").casefold()
    winner = _sibling_resolutions.get(cid)
    if winner and str(candidate.get("key") or "") != winner:
        return []
    return _base_matching_profiles(candidate, result, source_text, config)


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


def _quick_run_health(*, stage: Path, registry_path: Path, output_dir: Path, mode: str, health_check: Path = loop.HEALTH_CHECK) -> dict[str, Any]:
    report = _base_run_health(
        stage=stage,
        registry_path=registry_path,
        output_dir=output_dir,
        mode="deep",
        health_check=health_check,
    )
    # The first call is the complete baseline containing every sibling. Build
    # the canonical resolution map before the repair loop asks for profiles.
    if not _sibling_resolutions and registry_path.name == "candidates.json":
        _sibling_resolutions.update(_discover_sibling_resolutions(registry_path, report))
    return report


def _ensure_representative_fixture_categories(config: dict[str, Any], quick: dict[str, Any]) -> None:
    quick_fixtures = [
        copy.deepcopy(row)
        for row in quick.get("fixtures") or []
        if isinstance(row, dict)
    ]
    deep_fixtures = [
        row
        for row in ((config.get("modes", {}).get("deep", {}) or {}).get("fixtures") or [])
        if isinstance(row, dict)
    ]
    present = {str(row.get("category") or "") for row in quick_fixtures}
    for category in ("movie", "tv", "anime"):
        if category in present:
            continue
        source = next(
            (row for row in deep_fixtures if str(row.get("category") or "") == category),
            None,
        )
        if source is not None:
            quick_fixtures.append(copy.deepcopy(source))
            present.add(category)
    quick["fixtures"] = quick_fixtures


def _strengthen_quick_probe(config: dict[str, Any]) -> None:
    modes = config.setdefault("modes", {})
    original_deep = copy.deepcopy(modes.get("deep", {}) or {})
    quick = modes.setdefault("quick", {})
    _ensure_representative_fixture_categories(config, quick)
    quick["max_streams_to_probe"] = max(2, int(quick.get("max_streams_to_probe") or 1))
    quick["probe_best_variant"] = True
    quick["probe_first_segment"] = True
    quick["probe_streams_adaptively"] = True
    quick["fixture_limit_per_category"] = True
    quick["fallback_fixture_limit_per_category"] = 1
    quick["verify_fixture_duration_identity"] = True
    quick["minimum_fixture_duration_ratio"] = float(
        quick.get("minimum_fixture_duration_ratio")
        or original_deep.get("minimum_fixture_duration_ratio")
        or 0.55
    )
    quick["maximum_fixture_duration_ratio"] = float(
        quick.get("maximum_fixture_duration_ratio")
        or original_deep.get("maximum_fixture_duration_ratio")
        or 1.8
    )
    modes["deep"] = copy.deepcopy(quick)


def _rewrite_mode_metadata(stage: Path, output: Path) -> None:
    sibling_ids = sorted(_sibling_resolutions)
    registry_path = stage / "candidates.json"
    if registry_path.exists():
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        runtime = registry.setdefault("runtime_repair", {})
        runtime["validation_mode"] = "quick"
        runtime["profile_persistence"] = "deep_only"
        runtime["acceptance_policy"] = "healthy_sibling_then_repair"
        runtime["catalogue_fallbacks_per_category"] = 1
        runtime["sibling_resolved_provider_count"] = len(sibling_ids)
        runtime["sibling_resolved_provider_ids"] = sibling_ids
        registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    health_path = output / "health-results.json"
    if health_path.exists():
        health = json.loads(health_path.read_text(encoding="utf-8"))
        health["mode"] = "quick"
        runtime = health.setdefault("runtime_repair", {})
        runtime["validation_mode"] = "quick"
        runtime["profile_persistence"] = "deep_only"
        runtime["acceptance_policy"] = "healthy_sibling_then_repair"
        runtime["catalogue_fallbacks_per_category"] = 1
        runtime["sibling_resolved_provider_count"] = len(sibling_ids)
        runtime["sibling_resolved_provider_ids"] = sibling_ids
        health_path.write_text(json.dumps(health, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    report_path = output / "repair-report.json"
    if report_path.exists():
        report = json.loads(report_path.read_text(encoding="utf-8"))
        report["mode"] = "quick"
        report["profile_persistence"] = "deep_only"
        report["bounded_refresh_pass"] = True
        report["acceptance_policy"] = "healthy_sibling_then_repair"
        report["catalogue_fallbacks_per_category"] = 1
        report["sibling_resolved_provider_count"] = len(sibling_ids)
        report["sibling_resolved_provider_ids"] = sibling_ids
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", type=Path, default=ROOT / "staging")
    parser.add_argument("--output", type=Path, default=ROOT / "health-output")
    parser.add_argument("--max-rounds", type=int, default=1)
    args = parser.parse_args()

    stage = args.stage.resolve()
    output = args.output.resolve()
    max_rounds = max(1, min(2, int(args.max_rounds)))

    original_health_config = HEALTH_CONFIG.read_bytes()
    original_argv = list(sys.argv)
    original_compare = loop.compare_results
    original_run_health = loop.run_health
    original_persist = loop.persist_runtime_profiles
    original_matching = loop.matching_profiles

    try:
        _sibling_resolutions.clear()
        config = json.loads(original_health_config.decode("utf-8"))
        _strengthen_quick_probe(config)
        HEALTH_CONFIG.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        loop.compare_results = _quick_compare_results
        loop.run_health = _quick_run_health
        loop.matching_profiles = _sibling_aware_matching_profiles
        loop.persist_runtime_profiles = lambda _config, _assignments: []

        sys.argv = [
            str(SCRIPTS / "deep_repair_loop.py"),
            "--stage",
            str(stage),
            "--output",
            str(output),
            "--mode",
            "deep",
            "--max-rounds",
            str(max_rounds),
        ]
        rc = loop.main()
        _rewrite_mode_metadata(stage, output)
        return int(rc)
    finally:
        HEALTH_CONFIG.write_bytes(original_health_config)
        sys.argv = original_argv
        loop.compare_results = original_compare
        loop.run_health = original_run_health
        loop.matching_profiles = original_matching
        loop.persist_runtime_profiles = original_persist


if __name__ == "__main__":
    raise SystemExit(main())
