#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Run one bounded adaptive repair pass during routine provider refreshes.

Routine refresh is deliberately repair-first: a generated candidate may survive
when it restores playable coverage without introducing a runtime/category
regression or positive wrong-content evidence. Identity may remain unknown at
this bounded stage; the complete catalogue/media audit still runs before any
publication.

Deep remains stricter and authoritative for broad catalogue proof, durable
profile learning, new activation, and quarantine exit.
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


def _category_playable_totals(result: dict[str, Any]) -> dict[str, int]:
    """Return bounded playable evidence per catalogue category."""
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


def _quick_compare_results(parent: dict[str, Any], repaired: dict[str, Any]) -> tuple[bool, str]:
    """Keep safe incremental coverage gains for final catalogue classification.

    Unlike deep profile learning, quick repair does not require every supported
    category to become healthy in one pass. It requires:
      * no hard/runtime/malformed regression;
      * no positive wrong-content or duration contradiction;
      * no loss of a category that was already playable;
      * a strict coverage/runtime improvement.
    """
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
    # health_check.mjs currently enables its one-fixture-per-required-category
    # selector only for requestedMode=deep. Execute that selector with a
    # temporary deep config cloned from our bounded quick profile, then rewrite
    # the evidence to truthful mode=quick before publication.
    return _base_run_health(
        stage=stage,
        registry_path=registry_path,
        output_dir=output_dir,
        mode="deep",
        health_check=health_check,
    )


def _ensure_representative_fixture_categories(config: dict[str, Any], quick: dict[str, Any]) -> None:
    """Give routine repair one bounded fixture for movie, TV and anime."""
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
    """Keep refresh bounded while collecting enough evidence for safe repair."""
    modes = config.setdefault("modes", {})
    original_deep = copy.deepcopy(modes.get("deep", {}) or {})
    quick = modes.setdefault("quick", {})
    _ensure_representative_fixture_categories(config, quick)
    quick["max_streams_to_probe"] = max(2, int(quick.get("max_streams_to_probe") or 1))
    quick["probe_best_variant"] = True
    quick["probe_first_segment"] = True
    quick["probe_streams_adaptively"] = True
    quick["fixture_limit_per_category"] = True
    quick["fallback_fixture_limit_per_category"] = 0
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
    # The health harness gates per-category fixture selection on requestedMode
    # rather than solely on the mode config. Clone the bounded profile into the
    # temporary deep slot so calling --deep does not silently consume deep-sized
    # budgets or fallback fixtures.
    modes["deep"] = copy.deepcopy(quick)


def _rewrite_mode_metadata(stage: Path, output: Path) -> None:
    registry_path = stage / "candidates.json"
    if registry_path.exists():
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        runtime = registry.setdefault("runtime_repair", {})
        runtime["validation_mode"] = "quick"
        runtime["profile_persistence"] = "deep_only"
        runtime["acceptance_policy"] = "repair_first_no_contradiction"
        registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    health_path = output / "health-results.json"
    if health_path.exists():
        health = json.loads(health_path.read_text(encoding="utf-8"))
        health["mode"] = "quick"
        runtime = health.setdefault("runtime_repair", {})
        runtime["validation_mode"] = "quick"
        runtime["profile_persistence"] = "deep_only"
        runtime["acceptance_policy"] = "repair_first_no_contradiction"
        health_path.write_text(json.dumps(health, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    report_path = output / "repair-report.json"
    if report_path.exists():
        report = json.loads(report_path.read_text(encoding="utf-8"))
        report["mode"] = "quick"
        report["profile_persistence"] = "deep_only"
        report["bounded_refresh_pass"] = True
        report["acceptance_policy"] = "repair_first_no_contradiction"
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

    try:
        config = json.loads(original_health_config.decode("utf-8"))
        _strengthen_quick_probe(config)
        HEALTH_CONFIG.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        loop.compare_results = _quick_compare_results
        loop.run_health = _quick_run_health
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
        loop.persist_runtime_profiles = original_persist


if __name__ == "__main__":
    raise SystemExit(main())
