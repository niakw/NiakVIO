#!/usr/bin/env python3
"""One-command intelligent repair over the unresolved NiakVIO provider portfolio.

This is the operator entrypoint for large catalogues. It never contains
provider-specific rules. It selects unresolved providers, keeps pure WAF/
environment cases out of code mutation by default, stages providers in bounded
batches, runs the ARCHI2 Brain deep sandbox, learns from strictly validated
improvements, materializes accepted reusable profiles, and lets later waves
reuse newly trusted skills.

Provider-local knowledge is evidence. Durable behavior remains Core/capability
profiles and validated learned skills.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
STATUS = ROOT / "automation" / "provider-census-status.json"
DEFAULT_OUTPUT = ROOT / "automation" / "provider-brain-repair-latest.json"
DEFAULT_WORK = ROOT / "automation" / ".provider-brain-repair-work"
EXPERIENCE = ROOT / "automation" / "brain-repair-experience.json"
BATCH_PLAN = ROOT / "automation" / "provider-repair-batch-plan-latest.json"
REPAIR_MEMORY = ROOT / "automation" / "brain-repair-memory.json"
BRAIN_POLICY = ROOT / "engine_v2" / "config" / "brain-policy.json"

GREEN = {"FULL OK", "PARTIAL OK"}
ENVIRONMENT = {"PROVIDER WAF/ANTIBOT"}


def load(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def cid(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def run(*args: str, env: dict[str, str] | None = None, timeout: int | None = None) -> None:
    print("FIELD_PROVIDER_BRAIN_REPAIR_CMD " + " ".join(args), flush=True)
    subprocess.run(
        list(args),
        cwd=ROOT,
        env=env or os.environ.copy(),
        check=True,
        timeout=timeout,
    )


def shard_for(provider: str, count: int) -> int:
    digest = hashlib.sha256(provider.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") % count


def status_payload() -> dict[str, Any]:
    value = load(STATUS, {})
    return value if isinstance(value, dict) else {}


def status_rows(payload: dict[str, Any] | None = None) -> dict[str, dict[str, Any]]:
    payload = payload or status_payload()
    return {
        cid(row.get("provider")): row
        for row in payload.get("providers") or []
        if isinstance(row, dict) and cid(row.get("provider"))
    }


def census_queue(payload: dict[str, Any], *, include_environment: bool) -> set[str]:
    key = "symptomaticProviders" if include_environment else "repairQueue"
    values = payload.get(key)
    if not isinstance(values, list):
        values = payload.get("brainQueue") or []
        if not include_environment:
            rows = status_rows(payload)
            values = [
                value for value in values
                if str((rows.get(cid(value)) or {}).get("status") or "") not in ENVIRONMENT
            ]
    return {cid(value) for value in values if cid(value)}


def select_targets(
    explicit: list[str],
    *,
    include_environment: bool,
    shard_count: int,
    shard_index: int,
) -> tuple[list[str], list[str], dict[str, dict[str, Any]]]:
    payload = status_payload()
    rows = status_rows(payload)
    allowed = census_queue(payload, include_environment=include_environment)
    requested = {cid(value) for value in explicit if cid(value)}
    if requested:
        candidates = sorted(requested & allowed)
    else:
        candidates = sorted(allowed)
    skipped_environment: list[str] = []
    selected: list[str] = []
    for provider in candidates:
        row = rows.get(provider) or {}
        state = str(row.get("status") or "")
        if not include_environment and state in ENVIRONMENT:
            skipped_environment.append(provider)
            continue
        if shard_for(provider, shard_count) != shard_index:
            continue
        selected.append(provider)
    return selected, sorted(skipped_environment), rows


def chunks(values: list[str], size: int) -> list[list[str]]:
    return [values[index:index + size] for index in range(0, len(values), size)]


def repair_batches(values: list[str], size: int) -> list[dict[str, Any]]:
    """Group current repair targets by census-derived family/signature plan.

    The batch plan is only a scheduling/transfer prior. A stale plan is ignored,
    and every candidate still passes the ordinary deep/identity/playback gates.
    """
    selected = {cid(value) for value in values if cid(value)}
    if not selected:
        return []
    status = status_payload()
    plan = load(BATCH_PLAN, {})
    if not isinstance(plan, dict) or str(plan.get("sourceRunId") or "") != str(status.get("runId") or ""):
        return [
            {"groupId": "fallback", "repairScope": "unknown", "providers": batch}
            for batch in chunks(sorted(selected), size)
        ]

    out: list[dict[str, Any]] = []
    assigned: set[str] = set()
    for group in plan.get("groups") or []:
        if not isinstance(group, dict):
            continue
        members = [
            cid(value) for value in group.get("providers") or []
            if cid(value) in selected and cid(value) not in assigned
        ]
        if not members:
            continue
        for batch in chunks(members, size):
            out.append({
                "groupId": str(group.get("groupId") or "unknown"),
                "repairScope": str(group.get("repairScope") or "unknown"),
                "capabilityStrategy": str(group.get("capabilityStrategy") or "unknown"),
                "providers": batch,
            })
            assigned.update(batch)

    leftovers = sorted(selected - assigned)
    for batch in chunks(leftovers, size):
        out.append({"groupId": "unplanned", "repairScope": "unknown", "providers": batch})
    return out


def repair_memory_fingerprint() -> str:
    try:
        return hashlib.sha256(REPAIR_MEMORY.read_bytes()).hexdigest()
    except OSError:
        return ""


def experiment_rotation_decision(
    *,
    accepted_count: int,
    remaining_count: int,
    wave: int,
    max_waves: int,
    memory_advanced: bool,
) -> str:
    if accepted_count > 0:
        return "materialize"
    if remaining_count > 0 and memory_advanced and wave < max_waves:
        return "rotate"
    return "exhausted" if memory_advanced else "stalled"


def exhausted_from_negative_memory(brain_summary: dict[str, Any]) -> set[str]:
    """Reclassify signatures that became exhausted during the just-finished wave."""
    policy = load(BRAIN_POLICY, {})
    production = policy.get("production") if isinstance(policy.get("production"), dict) else {}
    negative = production.get("negativeExperimentMemory") if isinstance(production.get("negativeExperimentMemory"), dict) else {}
    default_variants = max(1, int(negative.get("maxVariantsPerSignature") or 4))
    rotate_every = max(1, int(negative.get("rotateExperimentAfterFailures") or 1))
    memory = load(REPAIR_MEMORY, {})
    entries = [row for row in memory.get("entries") or [] if isinstance(row, dict)]
    out: set[str] = set()
    for plan in (brain_summary.get("plans") or {}).values():
        if not isinstance(plan, dict):
            continue
        provider = cid(plan.get("providerId"))
        signature = str(plan.get("signature") or "")
        failure_class = str(plan.get("failureClass") or "")
        if not provider or not signature:
            continue
        variant_count = max(1, int(plan.get("experimentVariantCount") or default_variants))
        allowed_profiles = {
            str(value) for value in plan.get("allowedProfiles") or []
            if str(value)
        }
        variants: set[int] = set()
        for row in entries:
            if cid(row.get("providerId")) != provider:
                continue
            if str(row.get("signature") or "") != signature:
                continue
            if failure_class and str(row.get("failureClass") or "") != failure_class:
                continue
            if allowed_profiles and str(row.get("profile") or "") not in allowed_profiles:
                continue
            if int(row.get("successes") or 0) > 0:
                continue
            if int(row.get("consecutiveFailures") or 0) < rotate_every:
                continue
            variants.add(max(0, min(variant_count - 1, int(row.get("experimentVariant") or 0))))
        if len(variants) >= variant_count:
            out.add(provider)
    return out


def playable_count(result: dict[str, Any]) -> int:
    evidence = result.get("evidence") if isinstance(result.get("evidence"), dict) else {}
    values = [int(evidence.get("streams_playable") or 0)]
    for test in result.get("tests") or []:
        if isinstance(test, dict):
            values.append(int(test.get("streams_playable") or 0))
    return max(values or [0])


def contradiction_count(result: dict[str, Any]) -> int:
    evidence = result.get("evidence") if isinstance(result.get("evidence"), dict) else {}
    return int(evidence.get("identity_contradiction_count") or 0) + int(
        evidence.get("duration_identity_mismatch_count") or 0
    )


def fixed_providers(health: dict[str, Any]) -> set[str]:
    out: set[str] = set()
    for result in health.get("results") or []:
        if not isinstance(result, dict):
            continue
        key = str(result.get("key") or "")
        provider = cid(key.split(":", 1)[-1].split("::", 1)[0])
        if not provider:
            continue
        if playable_count(result) > 0 and contradiction_count(result) == 0:
            out.add(provider)
    return out


def accepted_rows(report: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for round_row in report.get("rounds") or []:
        if not isinstance(round_row, dict):
            continue
        for accepted in round_row.get("accepted") or []:
            if not isinstance(accepted, dict):
                continue
            parent = str(accepted.get("parent_key") or "")
            provider = cid(parent.split(":", 1)[-1].split("::", 1)[0])
            out.append({
                "provider": provider,
                "profile": str(accepted.get("profile") or ""),
                "reason": str(accepted.get("reason") or ""),
                "statusBefore": accepted.get("status_before"),
                "statusAfter": accepted.get("status_after"),
                "playableBefore": int(accepted.get("streams_playable_before") or 0),
                "playableAfter": int(accepted.get("streams_playable_after") or 0),
            })
    return out


def sanitized_brain(report: dict[str, Any]) -> dict[str, Any]:
    brain = report.get("brain") if isinstance(report.get("brain"), dict) else {}
    plans = brain.get("plans") if isinstance(brain.get("plans"), dict) else {}
    return {
        "learnedEvents": int(brain.get("learnedEvents") or 0),
        "validatedRepairLearningExecuted": bool(brain.get("validatedRepairLearningExecuted")),
        "queuedForLearning": sorted({cid(x) for x in brain.get("queuedForLearning") or [] if cid(x)}),
        "plans": {
            str(key): {
                "providerId": row.get("providerId"),
                "failureClass": row.get("failureClass"),
                "signature": row.get("signature"),
                "action": row.get("action"),
                "exitReason": row.get("exitReason"),
                "repairScope": row.get("repairScope"),
                "repairType": row.get("repairType"),
                "learningDisposition": row.get("learningDisposition"),
                "allowedProfiles": row.get("allowedProfiles") or [],
                "experimentVariant": row.get("experimentVariant"),
                "experimentVariantCount": row.get("experimentVariantCount"),
                "experimentExhausted": row.get("experimentExhausted") is True,
                "negativeMemoryMatches": row.get("negativeMemoryMatches"),
                "hypotheses": row.get("hypotheses") or [],
            }
            for key, row in plans.items()
            if isinstance(row, dict)
        },
    }


def materialize() -> None:
    for command in (
        (sys.executable, "scripts/reconcile_provider_domain_metadata.py", "--rebuild"),
        (sys.executable, "scripts/materialize_provider_base_v3_store.py"),
        (sys.executable, "scripts/materialize_provider_v3_all.py"),
        (sys.executable, "scripts/validate_published_provider_config.py"),
    ):
        run(*command)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", action="append", default=[], help="Optional provider id; repeatable. Empty = current census repairQueue only.")
    parser.add_argument("--waves", type=int, default=4)
    parser.add_argument("--batch-size", type=int, default=48)
    parser.add_argument("--health-concurrency", type=int, default=0, help="0 = auto (6/8 depending on target count)")
    parser.add_argument("--include-environment", action="store_true", help="Include pure WAF/environment cases in code-repair staging.")
    parser.add_argument("--shard-count", type=int, default=1)
    parser.add_argument("--shard-index", type=int, default=0)
    parser.add_argument("--work-dir", type=Path, default=DEFAULT_WORK)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--keep-work", action="store_true")
    args = parser.parse_args()

    shard_count = max(1, min(int(args.shard_count), 64))
    shard_index = int(args.shard_index)
    if not 0 <= shard_index < shard_count:
        raise SystemExit("invalid shard index")
    waves = max(1, min(int(args.waves), 6))
    batch_size = max(4, min(int(args.batch_size), 96))

    # Rebuild structural prior memory from the exact current repo/census before
    # selecting experiments. This memory never grants acceptance authority; it
    # only supplies route/strategy priors to the adaptive sandbox.
    run(
        sys.executable,
        "scripts/build_brain_repair_experience.py",
        "--output", str(EXPERIENCE),
    )
    experience = load(EXPERIENCE, {})

    selected, skipped_environment, rows = select_targets(
        args.provider,
        include_environment=args.include_environment,
        shard_count=shard_count,
        shard_index=shard_index,
    )
    if not selected:
        payload = {
            "schemaVersion": 1,
            "selectedProviderCount": 0,
            "selectedProviders": [],
            "skippedEnvironmentProviders": skipped_environment,
            "waves": [],
            "remainingProviders": [],
            "message": "no repairable providers selected from current census queue",
            "selectionSource": "automation/provider-census-status.json:repairQueue",
            "experienceMemory": {
                "providerCount": int(experience.get("providerCount") or 0),
                "operationalProviderCount": int(experience.get("operationalProviderCount") or 0),
                "strategyCount": len(experience.get("strategyPatterns") or {}),
            },
        }
        write(args.output if args.output.is_absolute() else ROOT / args.output, payload)
        print("FIELD_PROVIDER_BRAIN_REPAIR_EMPTY")
        return 0

    work = args.work_dir if args.work_dir.is_absolute() else ROOT / args.work_dir
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    remaining = list(selected)
    wave_reports: list[dict[str, Any]] = []
    all_accepted: list[dict[str, Any]] = []
    all_fixed: set[str] = set()
    all_deferred: set[str] = set()
    no_progress_reason: str | None = None

    concurrency = int(args.health_concurrency)
    if concurrency <= 0:
        concurrency = 8 if len(selected) >= 48 else 6
    concurrency = max(1, min(concurrency, 8))

    try:
        for wave in range(1, waves + 1):
            if not remaining:
                break
            accepted_this_wave: list[dict[str, Any]] = []
            fixed_this_wave: set[str] = set()
            deferred_this_wave: set[str] = set()
            batch_reports: list[dict[str, Any]] = []
            memory_before = repair_memory_fingerprint()

            for batch_index, batch_plan in enumerate(repair_batches(remaining, batch_size), start=1):
                batch = list(batch_plan["providers"])
                batch_root = work / f"wave-{wave}" / f"batch-{batch_index}"
                stage = batch_root / "stage"
                output = batch_root / "output"
                targets_file = batch_root / "targets.json"
                batch_root.mkdir(parents=True, exist_ok=True)
                write(targets_file, {"targets": [{"id": provider} for provider in batch]})

                run(sys.executable, "scripts/stage_published.py", "--stage", str(stage), "--include-file", str(targets_file))
                env = os.environ.copy()
                env["NUVIO_HEALTH_CONCURRENCY"] = str(concurrency)
                env["NUVIO_BRAIN_REPAIR_WAVE"] = str(wave)
                run(
                    sys.executable,
                    "scripts/run_adaptive_deep_repair.py",
                    "--stage", str(stage),
                    "--registry", str(stage / "candidates.json"),
                    "--output", str(output),
                    "--max-rounds", "1",
                    env=env,
                    timeout=max(1800, len(batch) * 120),
                )

                repair_report = load(output / "repair-report.json", {})
                health = load(output / "health-results.json", {})
                accepted = accepted_rows(repair_report)
                fixed = fixed_providers(health)
                brain_summary = sanitized_brain(repair_report)
                deferred = {
                    cid(row.get("providerId"))
                    for row in (brain_summary.get("plans") or {}).values()
                    if isinstance(row, dict)
                    and row.get("experimentExhausted") is True
                    and cid(row.get("providerId"))
                }
                deferred.update(exhausted_from_negative_memory(brain_summary))
                accepted_this_wave.extend(accepted)
                fixed_this_wave.update(fixed)
                deferred_this_wave.update(deferred)
                batch_reports.append({
                    "batch": batch_index,
                    "groupId": batch_plan.get("groupId"),
                    "repairScope": batch_plan.get("repairScope"),
                    "capabilityStrategy": batch_plan.get("capabilityStrategy"),
                    "providerCount": len(batch),
                    "providers": batch,
                    "acceptedCount": len(accepted),
                    "accepted": accepted,
                    "fixedInLab": sorted(fixed),
                    "deferredToLearning": sorted(deferred),
                    "brain": brain_summary,
                })

            all_accepted.extend(accepted_this_wave)
            all_fixed.update(fixed_this_wave)
            all_deferred.update(deferred_this_wave)
            remaining = [
                provider for provider in remaining
                if provider not in fixed_this_wave and provider not in deferred_this_wave
            ]
            memory_after = repair_memory_fingerprint()
            experiment_memory_advanced = memory_after != memory_before
            wave_reports.append({
                "wave": wave,
                "inputProviderCount": sum(row["providerCount"] for row in batch_reports),
                "acceptedCount": len(accepted_this_wave),
                "fixedInLabCount": len(fixed_this_wave),
                "fixedInLab": sorted(fixed_this_wave),
                "deferredToLearningCount": len(deferred_this_wave),
                "deferredToLearning": sorted(deferred_this_wave),
                "remainingProviderCount": len(remaining),
                "experimentMemoryAdvanced": experiment_memory_advanced,
                "batches": batch_reports,
            })

            decision = experiment_rotation_decision(
                accepted_count=len(accepted_this_wave),
                remaining_count=len(remaining),
                wave=wave,
                max_waves=waves,
                memory_advanced=experiment_memory_advanced,
            )
            if decision == "rotate":
                # A rejected experiment is still useful evidence. Rotate to the
                # next bounded hypothesis immediately instead of aborting Repair.
                no_progress_reason = "rotating_rejected_experiment"
                continue
            if decision in {"exhausted", "stalled"}:
                no_progress_reason = (
                    "experiment_variants_exhausted"
                    if decision == "exhausted"
                    else "no_new_repair_experiment"
                )
                break

            # Accepted profile assignments and trusted skill memory are now in
            # provider-overrides.json. Materialize once per wave so the next wave
            # starts from the improved current bytes instead of replaying the same
            # parent candidate.
            materialize()

        payload = {
            "schemaVersion": 1,
            "executionModel": "family-batched-multi-wave-brain-repair",
            "providerSpecificRules": False,
            "sourceCensusRunId": status_payload().get("runId"),
            "selectionSource": "automation/provider-census-status.json:repairQueue",
            "experienceMemory": {
                "schemaVersion": experience.get("schemaVersion"),
                "sourceRunId": experience.get("sourceRunId"),
                "sourceSha": experience.get("sourceSha"),
                "providerCount": int(experience.get("providerCount") or 0),
                "operationalProviderCount": int(experience.get("operationalProviderCount") or 0),
                "strategyCount": len(experience.get("strategyPatterns") or {}),
            },
            "shardCount": shard_count,
            "shardIndex": shard_index,
            "healthConcurrency": concurrency,
            "batchSize": batch_size,
            "maxWaves": waves,
            "selectedProviderCount": len(selected),
            "selectedProviders": selected,
            "initialStatuses": {
                provider: str((rows.get(provider) or {}).get("status") or "unknown")
                for provider in selected
            },
            "skippedEnvironmentProviders": skipped_environment,
            "acceptedRepairCount": len(all_accepted),
            "acceptedRepairs": all_accepted,
            "fixedInLabProviders": sorted(all_fixed),
            "deferredLearningProviders": sorted(all_deferred),
            "remainingProviders": remaining,
            "noProgressReason": no_progress_reason,
            "waves": wave_reports,
            "safety": {
                "learnedSkillRole": "hypothesis-ordering-only",
                "directSkillApplication": False,
                "acceptedMutationRequiresStrictImprovement": True,
                "identityGateRequired": True,
                "currentByteRetestRequired": True,
                "wafEnvironmentExcludedByDefault": True,
                "experienceMemoryRole": "prior-only-no-acceptance-authority",
            },
        }
        output_path = args.output if args.output.is_absolute() else ROOT / args.output
        write(output_path, payload)
        print(
            "FIELD_PROVIDER_BRAIN_REPAIR "
            f"selected={len(selected)} accepted={len(all_accepted)} "
            f"fixed_lab={len(all_fixed)} deferred_learning={len(all_deferred)} "
            f"remaining={len(remaining)} waves={len(wave_reports)}"
        )
        return 0
    finally:
        if not args.keep_work:
            shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
