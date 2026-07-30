#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Run deep validation, diagnose common failures, repair and retest.

The loop is deliberately bounded and provider-agnostic:

baseline deep check -> runtime signature classification -> structural profile
application -> exact generated artifact validation -> deep retest -> strict
before/after comparison.

A repair is retained only when the generated JavaScript improves runtime
observations and does not introduce a hard failure. Otherwise the parent file
and parent health result remain authoritative.
"""
from __future__ import annotations

import argparse
import copy
import json
import os
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from apply_provider_overrides import load_overrides
from runtime_repair import (
    compare_results,
    create_repair_candidate,
    health_counts,
    matching_profiles,
    quality_vector,
    result_with_parent_key,
)

ROOT = Path(__file__).resolve().parents[1]
HEALTH_CHECK = ROOT / "scripts" / "health_check.mjs"


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def persist_runtime_profiles(config: dict[str, Any], assignments: dict[str, set[str]]) -> list[dict[str, Any]]:
    """Persist only profiles already accepted by a strict real deep retest."""
    provider_patches = config.setdefault("provider_patches", {})
    if not isinstance(provider_patches, dict):
        raise ValueError("provider_patches must be an object")
    records: list[dict[str, Any]] = []
    for provider_id, profile_names in sorted(assignments.items()):
        if not provider_id or not profile_names:
            continue
        current = provider_patches.setdefault(provider_id.casefold(), {})
        if not isinstance(current, dict):
            raise ValueError(f"provider_patches.{provider_id} must be an object")
        profiles = [str(value) for value in current.get("profiles") or [] if str(value).strip()]
        before = set(profiles)
        for profile_name in sorted(profile_names):
            if profile_name not in before:
                profiles.append(profile_name)
                records.append({"provider_id": provider_id.casefold(), "profile": profile_name})
        if profiles:
            current["profiles"] = profiles
    return records


def run_health(
    *,
    stage: Path,
    registry_path: Path,
    output_dir: Path,
    mode: str,
    health_check: Path = HEALTH_CHECK,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env.update(
        {
            "NUVIO_STAGE": str(stage),
            "NUVIO_CANDIDATES_PATH": str(registry_path),
            "NUVIO_HEALTH_OUTPUT": str(output_dir),
            "NUVIO_HEALTH_RESULTS_FILENAME": "health-results.json",
            "NUVIO_DNS_PREFLIGHT_RESULTS": os.environ.get(
                "NUVIO_DNS_PREFLIGHT_RESULTS",
                str(output_dir.parent / "dns-preflight-report.json"),
            ),
        }
    )
    command = ["node", str(health_check), f"--{mode}"]
    subprocess.run(command, cwd=ROOT, env=env, check=True)
    return load_json(output_dir / "health-results.json")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", type=Path, default=ROOT / "staging")
    parser.add_argument("--output", type=Path, default=ROOT / "health-output")
    parser.add_argument("--mode", choices=["deep"], default="deep")
    parser.add_argument("--max-rounds", type=int)
    parser.add_argument("--health-check", type=Path, default=HEALTH_CHECK, help=argparse.SUPPRESS)
    args = parser.parse_args()

    stage = args.stage.resolve()
    output = args.output.resolve()
    registry_path = stage / "candidates.json"
    if not registry_path.exists():
        raise SystemExit(f"missing candidate registry: {registry_path}")
    output.mkdir(parents=True, exist_ok=True)

    config = load_overrides()
    repair_config = config.get("runtime_repair") or {}
    max_rounds = max(0, min(5, int(args.max_rounds if args.max_rounds is not None else repair_config.get("max_rounds", 3))))
    started = time.monotonic()

    registry = load_json(registry_path)
    original_candidates = [item for item in registry.get("candidates") or [] if isinstance(item, dict)]
    candidate_order = [str(item.get("key")) for item in original_candidates]
    current_candidates = {str(item.get("key")): copy.deepcopy(item) for item in original_candidates}

    baseline_dir = output / "repair-round-0-baseline"
    health_check_path = args.health_check.resolve()
    if not health_check_path.is_file():
        raise SystemExit(f"missing health-check script: {health_check_path}")
    baseline = run_health(stage=stage, registry_path=registry_path, output_dir=baseline_dir, mode=args.mode, health_check=health_check_path)
    current_results = {
        str(item.get("key")): copy.deepcopy(item)
        for item in baseline.get("results") or []
        if isinstance(item, dict) and item.get("key")
    }
    missing = [key for key in candidate_order if key not in current_results]
    if missing:
        raise RuntimeError("baseline health check omitted candidates: " + ", ".join(missing[:20]))

    audit: dict[str, Any] = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": args.mode,
        "provider_specific_rules": False,
        "max_rounds": max_rounds,
        "rounds": [],
    }

    accepted_total = 0
    accepted_profile_assignments: dict[str, set[str]] = {}
    for round_number in range(1, max_rounds + 1):
        attempts: list[dict[str, Any]] = []
        repair_candidates: list[dict[str, Any]] = []

        for parent_key in candidate_order:
            candidate = current_candidates[parent_key]
            result = current_results[parent_key]
            source_path = (stage / str(candidate.get("local_path") or "")).resolve()
            if not source_path.is_file():
                attempts.append({"parent_key": parent_key, "status": "skipped", "reason": "missing_parent_artifact"})
                continue
            source_text = source_path.read_text(encoding="utf-8", errors="strict")
            profiles = matching_profiles(candidate, result, source_text, config)
            for profile_name in profiles:
                repaired, error = create_repair_candidate(stage, candidate, profile_name, round_number)
                row = {
                    "parent_key": parent_key,
                    "parent_sha256": candidate.get("sha256"),
                    "profile": profile_name,
                    "baseline_status": result.get("status"),
                    "baseline_score": result.get("score"),
                }
                if repaired is None:
                    row.update({"status": "not_generated", "reason": error})
                else:
                    row.update(
                        {
                            "status": "generated",
                            "repair_key": repaired["key"],
                            "repair_sha256": repaired["sha256"],
                        }
                    )
                    repair_candidates.append(repaired)
                attempts.append(row)

        round_audit: dict[str, Any] = {
            "round": round_number,
            "generated_candidates": len(repair_candidates),
            "attempts": attempts,
            "accepted": [],
            "rejected": [],
        }
        audit["rounds"].append(round_audit)
        if not repair_candidates:
            break

        round_registry = copy.deepcopy(registry)
        round_registry["candidates"] = repair_candidates
        round_registry["candidate_count"] = len(repair_candidates)
        round_registry["canonical_provider_count"] = len(
            {item.get("canonical_id") for item in repair_candidates}
        )
        round_registry_path = stage / f"repair-round-{round_number}-candidates.json"
        write_json(round_registry_path, round_registry)

        round_output = output / f"repair-round-{round_number}"
        repaired_report = run_health(
            stage=stage,
            registry_path=round_registry_path,
            output_dir=round_output,
            mode=args.mode,
            health_check=health_check_path,
        )
        repaired_results = {
            str(item.get("key")): item
            for item in repaired_report.get("results") or []
            if isinstance(item, dict) and item.get("key")
        }

        variants_by_parent: dict[str, list[tuple[dict[str, Any], dict[str, Any]]]] = {}
        for repaired in repair_candidates:
            result = repaired_results.get(str(repaired.get("key")))
            parent_key = str((repaired.get("runtime_repair") or {}).get("parent_key") or "")
            if not result or not parent_key:
                round_audit["rejected"].append(
                    {
                        "repair_key": repaired.get("key"),
                        "parent_key": parent_key,
                        "reason": "missing_retest_result",
                    }
                )
                (stage / repaired["local_path"]).unlink(missing_ok=True)
                continue
            variants_by_parent.setdefault(parent_key, []).append((repaired, result))

        accepted_this_round = 0
        for parent_key, variants in variants_by_parent.items():
            parent_result = current_results[parent_key]
            ranked = sorted(variants, key=lambda pair: quality_vector(pair[1]), reverse=True)
            selected_candidate, selected_result = ranked[0]
            accepted, reason = compare_results(parent_result, selected_result)

            for candidate_variant, result_variant in variants:
                is_selected = candidate_variant["key"] == selected_candidate["key"]
                if accepted and is_selected:
                    updated_candidate = copy.deepcopy(candidate_variant)
                    repair_event = copy.deepcopy(updated_candidate.pop("runtime_repair", {}))
                    history = list(current_candidates[parent_key].get("repair_history") or [])
                    repair_event.update(
                        {
                            "accepted": True,
                            "result_status": selected_result.get("status"),
                            "result_score": selected_result.get("score"),
                            "reason": reason,
                        }
                    )
                    history.append(repair_event)
                    updated_candidate["repair_history"] = history
                    updated_candidate["key"] = parent_key
                    current_candidates[parent_key] = updated_candidate
                    current_results[parent_key] = result_with_parent_key(
                        selected_result,
                        parent_key,
                        updated_candidate.get("sha256"),
                    )
                    accepted_this_round += 1
                    accepted_total += 1
                    accepted_provider_id = str(updated_candidate.get("canonical_id") or updated_candidate.get("upstream_id") or "").casefold()
                    accepted_profile = str(repair_event.get("profile") or "")
                    if accepted_provider_id and accepted_profile:
                        accepted_profile_assignments.setdefault(accepted_provider_id, set()).add(accepted_profile)
                    round_audit["accepted"].append(
                        {
                            "parent_key": parent_key,
                            "profile": repair_event.get("profile"),
                            "sha256": updated_candidate.get("sha256"),
                            "status_before": parent_result.get("status"),
                            "status_after": selected_result.get("status"),
                            "score_before": parent_result.get("score"),
                            "score_after": selected_result.get("score"),
                            "reason": reason,
                        }
                    )
                else:
                    rejection_reason = reason if is_selected else "inferior_to_selected_variant"
                    round_audit["rejected"].append(
                        {
                            "parent_key": parent_key,
                            "repair_key": candidate_variant.get("key"),
                            "profile": (candidate_variant.get("runtime_repair") or {}).get("profile"),
                            "status": result_variant.get("status"),
                            "score": result_variant.get("score"),
                            "reason": rejection_reason,
                        }
                    )
                    (stage / candidate_variant["local_path"]).unlink(missing_ok=True)

        if accepted_this_round == 0:
            break

    final_candidates = [current_candidates[key] for key in candidate_order]
    registry["candidates"] = final_candidates
    registry["candidate_count"] = len(final_candidates)
    registry["canonical_provider_count"] = len(
        {item.get("canonical_id") for item in final_candidates}
    )
    registry["runtime_repair"] = {
        "enabled": True,
        "provider_specific_rules": False,
        "rounds_executed": len(audit["rounds"]),
        "accepted_repairs": accepted_total,
    }
    write_json(registry_path, registry)

    final_results = [current_results[key] for key in candidate_order]
    final_report = copy.deepcopy(baseline)
    final_report["schema_version"] = max(64, int(final_report.get("schema_version") or 0))
    final_report["generated_at"] = datetime.now(timezone.utc).isoformat()
    final_report["duration_seconds"] = round(time.monotonic() - started)
    final_report["candidate_count"] = len(final_results)
    final_report["counts"] = health_counts(final_results)
    final_report["results"] = final_results
    final_report["runtime_repair"] = registry["runtime_repair"]
    write_json(output / "health-results.json", final_report)

    persisted_profiles: list[dict[str, Any]] = []
    if health_check_path == HEALTH_CHECK.resolve() and accepted_profile_assignments:
        persisted_profiles = persist_runtime_profiles(config, accepted_profile_assignments)
        if persisted_profiles:
            write_json(ROOT / "provider-overrides.json", config)

    audit["completed_at"] = datetime.now(timezone.utc).isoformat()
    audit["accepted_repairs"] = accepted_total
    audit["persisted_runtime_profiles"] = persisted_profiles
    audit["final_counts"] = final_report["counts"]
    write_json(output / "repair-report.json", audit)

    # The per-round registries are implementation details and must not be used by
    # promotion. Keeping only their reports makes the final artifact unambiguous.
    for path in stage.glob("repair-round-*-candidates.json"):
        path.unlink(missing_ok=True)

    print(
        f"Deep repair loop complete: {accepted_total} validated repair(s) accepted "
        f"across {len(audit['rounds'])} round(s)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
