#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Run bounded deep repair under the ARCHI2 Brain control plane."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
ADAPTIVE = SCRIPTS / "adaptive_runtime"
HEALTH_CONFIG = ROOT / "health-config.json"
sys.path.insert(0, str(ADAPTIVE))
sys.path.insert(1, str(SCRIPTS))

import runtime_repair  # noqa: E402
import deep_repair_loop as loop  # noqa: E402
import brain_repair_runtime as brain  # noqa: E402
from provider_purification import purify_candidate, purify_registry  # noqa: E402
from repair_identity_gate import automatic_repair_identity_gate  # noqa: E402
from repair_profile_persistence import ensure_repair_profile  # noqa: E402

loaded = Path(runtime_repair.__file__).resolve()
expected = (ADAPTIVE / "runtime_repair.py").resolve()
if loaded != expected:
    raise SystemExit(f"adaptive runtime layer not loaded: {loaded} != {expected}")

_base_compare = loop.compare_results
_base_create = loop.create_repair_candidate
_base_run_health = loop.run_health
_base_matching = loop.matching_profiles


def _identity_safe_compare(parent: dict, repaired: dict) -> tuple[bool, str]:
    accepted, reason = _base_compare(parent, repaired)
    if not accepted:
        return accepted, reason
    identity_ok, identity_reason = automatic_repair_identity_gate(repaired)
    return (True, reason) if identity_ok else (False, identity_reason)


def _profiled_create(stage, candidate, profile_name, round_number):
    repaired, error = _base_create(stage, candidate, profile_name, round_number)
    if not isinstance(repaired, dict):
        return repaired, error
    # Any Brain/runtime mutation must immediately re-enter purification before its
    # strict deep retest. The deep result therefore proves the exact optimized bytes,
    # not the larger pre-purification candidate.
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
    return ensure_repair_profile(repaired, profile_name), error


def _brain_run_health(*, stage, registry_path, output_dir, mode, health_check=loop.HEALTH_CHECK):
    report = _base_run_health(
        stage=stage, registry_path=registry_path, output_dir=output_dir,
        mode="deep", health_check=health_check,
    )
    brain.update_plans(registry_path, report, "deep")
    return report


def _brain_matching(candidate, result, source_text, config=None):
    profiles = list(_base_matching(candidate, result, source_text, config))
    key = str(candidate.get("key") or "")
    parent_key = str((candidate.get("runtime_repair") or {}).get("parent_key") or "")
    plan = brain.PLANS.get(parent_key or key) or {}
    if str(plan.get("action") or "") != "probe-targeted-repair":
        return []
    allowed = {str(value) for value in plan.get("allowedProfiles") or [] if str(value)}
    return [profile for profile in profiles if profile in allowed]


def _argument_path(flag: str, default: Path) -> Path:
    if flag in sys.argv:
        try:
            return Path(sys.argv[sys.argv.index(flag) + 1]).resolve()
        except (ValueError, IndexError):
            pass
    return default.resolve()


def main() -> int:
    original_config = HEALTH_CONFIG.read_bytes()
    original_argv = list(sys.argv)
    try:
        brain.reset_runtime_state()
        health_config = json.loads(original_config.decode("utf-8"))
        deep_config = health_config.setdefault("modes", {}).setdefault("deep", {})
        deep_config["max_streams_to_probe"] = max(10, int(deep_config.get("max_streams_to_probe") or 1))
        deep_config["probe_streams_adaptively"] = True
        HEALTH_CONFIG.write_text(json.dumps(health_config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        # Deep is the authoritative purification phase: all effective staged bundles
        # are optimized after known patches/profiles, then that exact registry becomes
        # baseline input. Repairs generated later in this same loop are purified again
        # by _profiled_create before their own retest.
        stage = _argument_path("--stage", ROOT / "staging")
        output = _argument_path("--output", ROOT / "health-output")
        purification = purify_registry(stage, output / "provider-purification.json")
        print(
            "FIELD_PROVIDER_PURIFICATION_DEEP "
            f"candidates={purification['candidateCount']} applied={purification['appliedCount']} "
            f"bytes_saved={purification['bytesSaved']} saving_percent={purification['savingPercent']}"
        )

        loop.compare_results = _identity_safe_compare
        loop.create_repair_candidate = brain.wrap_create_repair_candidate(_profiled_create)
        loop.run_health = _brain_run_health
        loop.matching_profiles = _brain_matching
        sys.argv[0] = str(SCRIPTS / "deep_repair_loop.py")
        rc = loop.main()
        brain.annotate_and_learn(output, "deep")
        return int(rc)
    finally:
        HEALTH_CONFIG.write_bytes(original_config)
        sys.argv[:] = original_argv
        loop.compare_results = _base_compare
        loop.create_repair_candidate = _base_create
        loop.run_health = _base_run_health
        loop.matching_profiles = _base_matching


if __name__ == "__main__":
    raise SystemExit(main())
