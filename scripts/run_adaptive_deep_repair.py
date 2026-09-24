#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Run bounded deep repair under the ARCHI2 Brain control plane."""
from __future__ import annotations

import json
import os
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
from guard_nuvio_client_brain_compat import guard as guard_nuvio_client_brain_compat  # noqa: E402
from provider_byte_stability import verify_candidate, verify_registry  # noqa: E402
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
_base_accepted_runtime_program = loop.accepted_runtime_program



def _accepted_runtime_program_with_winning_trace(candidate, result=None):
    program = _base_accepted_runtime_program(candidate, result)
    return runtime_repair.augment_accepted_runtime_program(candidate, result, program)


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
    # Any Brain/runtime mutation must immediately re-enter raw-byte validation before its
    # strict deep retest. The deep result therefore proves the exact raw bytes,
    # not the larger pre-validation candidate.
    try:
        repaired, _byte_stability = verify_candidate(Path(stage), repaired)
    except Exception as exc:
        try:
            target = (Path(stage).resolve() / str(repaired.get("local_path") or "")).resolve()
            target.relative_to((Path(stage).resolve() / "providers" / "runtime-repairs").resolve())
            target.unlink(missing_ok=True)
        except (ValueError, OSError):
            pass
        return None, f"byte_stability_failed:{type(exc).__name__}:{exc}"
    return ensure_repair_profile(repaired, profile_name), error


def _brain_run_health(*, stage, registry_path, output_dir, mode, health_check=loop.HEALTH_CHECK):
    report = _base_run_health(
        stage=stage, registry_path=registry_path, output_dir=output_dir,
        mode="deep", health_check=health_check,
    )
    brain.update_plans(registry_path, report, "deep")
    return report


def _brain_matching(candidate, result, source_text, config=None):
    key = str(candidate.get("key") or "")
    parent_key = str((candidate.get("runtime_repair") or {}).get("parent_key") or "")
    plan_key = parent_key or key
    if isinstance(candidate.get("brain_exploration_parent"), dict):
        # Deep already proved that these bytes made safe causal progress without
        # becoming publishable. Replan from the new observation before choosing
        # the next profile; never replay the stale parent hypothesis blindly.
        plan = brain.replan_observation(candidate, result, plan_key=plan_key, mode="deep")
        candidate.pop("brain_exploration_parent", None)
    else:
        plan = brain.PLANS.get(plan_key) or {}
    # The current run is the highest-authority provider-local evidence. Convert
    # only successful, sanitized, reusable request shapes into sandbox recipes
    # before consulting historical provider/peer/generic priors. Exploration
    # round N+1 therefore learns directly from the requests observed in round N.
    candidate["brain_observed_request_recipes"] = runtime_repair.observed_request_recipes(candidate, result)
    candidate["brain_repair_plan"] = brain._plan_snapshot(plan)
    profiles = list(_base_matching(candidate, result, source_text, config))
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
        # Brain program synthesis needs the worker's already-sanitized request
        # shape and response-value hints. Keep this opt-in to the bounded Deep
        # repair lane so normal health/parity reports remain unchanged.
        deep_config["route_proof_trace"] = True
        HEALTH_CONFIG.write_text(json.dumps(health_config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        stage = _argument_path("--stage", ROOT / "staging")
        output = _argument_path("--output", ROOT / "health-output")

        # Provider repair logic is valid only against a conclusively known official
        # Nuvio runtime contract. Safe unrelated client updates may proceed; hard or
        # semantic runtime drift and transport-inconclusive checks fail closed before
        # any provider JS mutation or raw-byte validation is attempted.
        guard_nuvio_client_brain_compat(output / "nuvio-client-upstream-status.json")

        # Deep is the authoritative raw-byte validation phase: all effective staged bundles
        # are validated byte-for-byte after known patches/profiles, then that exact registry becomes
        # baseline input. Repairs generated later in this same loop are validated again
        # by _profiled_create before their own retest.
        byte_stability = verify_registry(stage, output / "provider-byte-stability.json")
        print(
            "FIELD_PROVIDER_BYTE_STABILITY_DEEP "
            f"candidates={byte_stability['candidateCount']} applied={byte_stability['appliedCount']} "
            f"bytes_saved={byte_stability['bytesSaved']} saving_percent={byte_stability['savingPercent']}"
        )

        loop.compare_results = _identity_safe_compare
        loop.create_repair_candidate = brain.wrap_create_repair_candidate(_profiled_create)
        loop.run_health = _brain_run_health
        loop.matching_profiles = _brain_matching
        loop.accepted_runtime_program = _accepted_runtime_program_with_winning_trace
        sys.argv[0] = str(SCRIPTS / "deep_repair_loop.py")
        exploration_chain = str(os.environ.get("NUVIO_BRAIN_EXPLORATION_CHAIN") or "").strip() == "1"
        bounded_rounds = "3" if exploration_chain else "1"
        # An explicit caller budget is authoritative. The exploration-chain
        # default exists only for callers that do not provide --max-rounds.
        # Automatic Repair deliberately passes 1 after Learning; overriding it
        # here silently turned one-hypothesis validation back into three rounds.
        if "--max-rounds" not in sys.argv:
            sys.argv.extend(["--max-rounds", bounded_rounds])
        explicit_rounds = None
        if "--max-rounds" in sys.argv:
            try:
                explicit_rounds = int(sys.argv[sys.argv.index("--max-rounds") + 1])
            except (ValueError, IndexError):
                explicit_rounds = None
        if explicit_rounds == 1:
            # Single-hypothesis Repair is fail-closed: fewer transport/profile
            # retries can create false negatives, never a false positive. Bound
            # a slow provider so one dead candidate cannot hold the whole cohort.
            deep_config["provider_timeout_ms"] = min(
                int(deep_config.get("provider_timeout_ms") or 70000),
                45000,
            )
            deep_config["max_settings_profiles"] = min(
                int(deep_config.get("max_settings_profiles") or 4),
                2,
            )
            HEALTH_CONFIG.write_text(
                json.dumps(health_config, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            print(
                "FIELD_BRAIN_SINGLE_HYPOTHESIS_BOUNDS "
                f"provider_timeout_ms={deep_config['provider_timeout_ms']} "
                f"settings_profiles={deep_config['max_settings_profiles']}"
            )
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
        loop.accepted_runtime_program = _base_accepted_runtime_program


if __name__ == "__main__":
    raise SystemExit(main())
