#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Run one bounded adaptive repair pass during routine provider refreshes.

This reuses the same provider-agnostic repair engine and strict content-identity
comparator as the deep harness, but executes health probes in ``quick`` mode
and never persists newly learned repair profiles. Deep remains authoritative
for broad catalogue proof, durable profile learning, and quarantine exit.
"""
from __future__ import annotations

import argparse
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
from repair_identity_gate import automatic_repair_identity_gate  # noqa: E402

_loaded = Path(runtime_repair.__file__).resolve()
_expected = (ADAPTIVE / "runtime_repair.py").resolve()
if _loaded != _expected:
    raise SystemExit(f"adaptive runtime layer not loaded: {_loaded} != {_expected}")

_base_compare_results = runtime_repair.compare_results
_base_run_health = loop.run_health


def _identity_safe_compare_results(parent: dict[str, Any], repaired: dict[str, Any]) -> tuple[bool, str]:
    accepted, reason = _base_compare_results(parent, repaired)
    if not accepted:
        return accepted, reason
    identity_ok, identity_reason = automatic_repair_identity_gate(repaired)
    if not identity_ok:
        return False, identity_reason
    return True, reason


def _quick_run_health(*, stage: Path, registry_path: Path, output_dir: Path, mode: str, health_check: Path = loop.HEALTH_CHECK) -> dict[str, Any]:
    return _base_run_health(
        stage=stage,
        registry_path=registry_path,
        output_dir=output_dir,
        mode="quick",
        health_check=health_check,
    )


def _strengthen_quick_probe(config: dict[str, Any]) -> None:
    """Keep refresh bounded while collecting enough evidence for safe repair."""
    quick = config.setdefault("modes", {}).setdefault("quick", {})
    quick["max_streams_to_probe"] = max(2, int(quick.get("max_streams_to_probe") or 1))
    quick["probe_best_variant"] = True
    quick["probe_first_segment"] = True
    quick["probe_streams_adaptively"] = True
    quick["fixture_limit_per_category"] = True
    quick["verify_fixture_duration_identity"] = True
    quick["minimum_fixture_duration_ratio"] = float(
        quick.get("minimum_fixture_duration_ratio")
        or (config.get("modes", {}).get("deep", {}) or {}).get("minimum_fixture_duration_ratio")
        or 0.55
    )
    quick["maximum_fixture_duration_ratio"] = float(
        quick.get("maximum_fixture_duration_ratio")
        or (config.get("modes", {}).get("deep", {}) or {}).get("maximum_fixture_duration_ratio")
        or 1.8
    )


def _rewrite_mode_metadata(stage: Path, output: Path) -> None:
    registry_path = stage / "candidates.json"
    if registry_path.exists():
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        runtime = registry.setdefault("runtime_repair", {})
        runtime["validation_mode"] = "quick"
        runtime["profile_persistence"] = "deep_only"
        registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    health_path = output / "health-results.json"
    if health_path.exists():
        health = json.loads(health_path.read_text(encoding="utf-8"))
        health["mode"] = "quick"
        runtime = health.setdefault("runtime_repair", {})
        runtime["validation_mode"] = "quick"
        runtime["profile_persistence"] = "deep_only"
        health_path.write_text(json.dumps(health, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    report_path = output / "repair-report.json"
    if report_path.exists():
        report = json.loads(report_path.read_text(encoding="utf-8"))
        report["mode"] = "quick"
        report["profile_persistence"] = "deep_only"
        report["bounded_refresh_pass"] = True
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

        loop.compare_results = _identity_safe_compare_results
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
