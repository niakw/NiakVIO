#!/usr/bin/env python3
"""Gate automatic Repair -> Learning dispatches on materially new causal methods.

The gate is deliberately cheaper and earlier than Learning execution. It reads only
sanitized durable experiment identity so it can advance a provider after a genuinely
new executed method, while refusing retry-counter churn and exhausted method families.

Only sanitized provider ids and deterministic hashes are persisted. No routes,
URLs, headers, bodies, source code, credentials, titles or private notes enter the
ledger.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PROVIDER_ID = re.compile(r"^[a-z0-9][a-z0-9-]{0,95}$")
FINGERPRINT = re.compile(r"^[0-9a-f]{64}$")


def cid(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def safe_provider(value: object) -> str:
    provider = cid(value)
    return provider if PROVIDER_ID.fullmatch(provider) else ""


def load(path: Path, default: dict[str, Any] | None = None) -> dict[str, Any]:
    if not path.is_file():
        return dict(default or {})
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: JSON object required")
    return value


def write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _stable_text(value: object, limit: int = 160) -> str:
    return str(value or "").strip().casefold()[:limit]


def _plan_payload(provider: str, plan: dict[str, Any]) -> dict[str, Any]:
    return {
        "provider": provider,
        "failureClass": _stable_text(plan.get("failureClass"), 96),
        "signature": _stable_text(plan.get("signature"), 160),
        "repairScope": _stable_text(plan.get("repairScope"), 64),
        "repairType": _stable_text(plan.get("repairType"), 96),
        "learningDisposition": _stable_text(plan.get("learningDisposition"), 120),
        "allowedProfiles": sorted({
            _stable_text(value, 96)
            for value in plan.get("allowedProfiles") or []
            if _stable_text(value, 96)
        }),
        # Ordinal retry counters do not identify a new causal method.
        # Keep them out of the durable dispatch fingerprint.
        "llmAdvisorStrategy": _stable_text(plan.get("llmAdvisorStrategy"), 160),
        "llmAdvisorProfile": _stable_text(plan.get("llmAdvisorProfile"), 96),
        "llmAdvisorExperimentFingerprint": _stable_text(
            plan.get("llmAdvisorExperimentFingerprint"), 128
        ),
    }


def plan_fingerprint(provider: str, plan: dict[str, Any]) -> str:
    payload = _plan_payload(provider, plan)
    # A provider with no causal identity/method is not safe for automatic Learning:
    # dispatching it would recreate the historical "deferred => run Learning" loop.
    has_cause = bool(payload["signature"] or payload["failureClass"])
    has_method = bool(
        payload["allowedProfiles"]
        or payload["llmAdvisorStrategy"]
        or payload["llmAdvisorProfile"]
        or payload["llmAdvisorExperimentFingerprint"]
    )
    if not (has_cause and has_method):
        return ""
    raw = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def dispatched_fingerprints(prior: dict[str, Any]) -> list[str]:
    """Return bounded unique dispatch history, including legacy last-only ledgers."""
    values: list[str] = []
    for raw in [
        *(prior.get("dispatchedFingerprints") or []),
        prior.get("lastDispatchedFingerprint"),
    ]:
        value = str(raw or "").strip().casefold()
        if FINGERPRINT.fullmatch(value) and value not in values:
            values.append(value)
    return values


def learning_experiment_epoch(memory: dict[str, Any], provider: str) -> str:
    """Hash distinct executable Learning methods, never retry counters."""
    provider = safe_provider(provider)
    experiment = memory.get("experimentMemory") if isinstance(memory, dict) else {}
    entries = (
        experiment.get("entries") or []
        if isinstance(experiment, dict)
        else (memory.get("entries") or [] if isinstance(memory, dict) else [])
    )
    identities: dict[str, dict[str, Any]] = {}
    for row in entries:
        if not isinstance(row, dict) or safe_provider(row.get("providerId")) != provider:
            continue
        if row.get("executionObserved") is not True:
            continue
        outcome = _stable_text(row.get("lastOutcome"), 64).replace("-", "_")
        if outcome in {"profile_unavailable", "not_generated"}:
            continue
        profile = _stable_text(row.get("profile"), 96)
        implementation = _stable_text(row.get("strategyImplementationFingerprint"), 128)
        positive = _stable_text(row.get("positiveProgramFingerprint"), 128)
        if not (profile or implementation or positive):
            continue
        identity = {
            "failureClass": _stable_text(row.get("failureClass"), 96),
            "signature": _stable_text(row.get("signature"), 160),
            "profile": profile,
            "experimentVariant": max(0, int(row.get("experimentVariant") or 0)),
            "experimentGeneration": max(1, int(row.get("experimentGeneration") or 1)),
            "capabilityStrategy": _stable_text(row.get("capabilityStrategy"), 120),
            "strategyImplementationFingerprint": implementation,
            "positiveProgramFingerprint": positive,
        }
        encoded = json.dumps(
            identity, ensure_ascii=True, sort_keys=True, separators=(",", ":")
        )
        identities[encoded] = identity
    if not identities:
        return ""
    raw = json.dumps(
        [identities[key] for key in sorted(identities)],
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _safe_int(value: object, default: int = 0) -> int:
    try:
        return int(value or default)
    except (TypeError, ValueError):
        return default


def exhausted_learning_providers(
    memory: dict[str, Any],
    policy: dict[str, Any],
) -> set[str]:
    """Return providers whose newest executed causal group exhausted bounded variants."""
    production = policy.get("production") if isinstance(policy.get("production"), dict) else {}
    negative = (
        production.get("negativeExperimentMemory")
        if isinstance(production.get("negativeExperimentMemory"), dict)
        else {}
    )
    max_variants = max(1, _safe_int(negative.get("maxVariantsPerSignature"), 5))
    rotate_every = max(1, _safe_int(negative.get("rotateExperimentAfterFailures"), 1))
    final_variant = max_variants - 1
    first_final_generation = max(
        1, _safe_int(negative.get("finalVariantGeneration"), 1)
    )
    max_learning_generation = max(
        first_final_generation,
        _safe_int(
            negative.get("maxLearningGenerationsPerSignature"),
            first_final_generation,
        ),
    )
    experiment = memory.get("experimentMemory") if isinstance(memory, dict) else {}
    entries = (
        experiment.get("entries") or []
        if isinstance(experiment, dict)
        else (memory.get("entries") or [] if isinstance(memory, dict) else [])
    )
    groups: dict[tuple[str, str, str], dict[str, Any]] = {}
    for index, row in enumerate(entries):
        if not isinstance(row, dict):
            continue
        provider = safe_provider(row.get("providerId"))
        if not provider or _safe_int(row.get("successes"), 0) > 0:
            continue
        if _safe_int(row.get("consecutiveFailures"), 0) < rotate_every:
            continue
        outcome = _stable_text(row.get("lastOutcome"), 64).replace("-", "_")
        if outcome in {"profile_unavailable", "not_generated", "executed_inconclusive"}:
            continue
        if row.get("executionObserved") is not True:
            continue
        if row.get("causalExerciseObserved") is False:
            continue
        key = (
            provider,
            _stable_text(row.get("failureClass"), 96),
            _stable_text(row.get("signature"), 160),
        )
        state = groups.setdefault(
            key,
            {
                "baseVariants": set(),
                "finalGenerations": set(),
                "latestSeen": "",
                "latestIndex": -1,
            },
        )
        variant = max(0, min(final_variant, _safe_int(row.get("experimentVariant"), 0)))
        if variant < final_variant:
            state["baseVariants"].add(variant)
        else:
            generation = max(1, _safe_int(row.get("experimentGeneration"), 1))
            if first_final_generation <= generation <= max_learning_generation:
                state["finalGenerations"].add(generation)
        seen = str(row.get("lastSeenAt") or "").strip()
        if seen > str(state["latestSeen"]) or (
            seen == str(state["latestSeen"]) and index > int(state["latestIndex"])
        ):
            state["latestSeen"] = seen
            state["latestIndex"] = index

    expected_base = set(range(final_variant))
    expected_generations = set(
        range(first_final_generation, max_learning_generation + 1)
    )
    newest_by_provider: dict[str, tuple[tuple[str, str, str], dict[str, Any]]] = {}
    for key, state in groups.items():
        provider = key[0]
        prior = newest_by_provider.get(provider)
        rank = (str(state["latestSeen"]), int(state["latestIndex"]))
        if prior is None:
            newest_by_provider[provider] = (key, state)
            continue
        prior_state = prior[1]
        prior_rank = (str(prior_state["latestSeen"]), int(prior_state["latestIndex"]))
        if rank >= prior_rank:
            newest_by_provider[provider] = (key, state)

    return {
        provider
        for provider, (_key, state) in newest_by_provider.items()
        if expected_base.issubset(state["baseVariants"])
        and expected_generations.issubset(state["finalGenerations"])
    }


def _execution_plan_payload(
    provider: str,
    row: dict[str, Any],
    learning_epoch: str = "",
) -> dict[str, Any]:
    lane = _stable_text(row.get("lane"), 64)
    strategy = _stable_text(row.get("strategyBlueprint"), 160)
    if not strategy and lane == "brain_learning":
        strategy = "brain_learning_strategy_discovery_v1"
    payload = {
        "source": "execution-plan",
        "provider": provider,
        "lane": lane,
        "owner": _stable_text(row.get("owner"), 96),
        "repairScope": _stable_text(row.get("repairScope"), 96),
        "capabilityStrategy": _stable_text(row.get("capabilityStrategy"), 120),
        "transportSignature": _stable_text(row.get("transportSignature"), 160),
        "strategyBlueprint": strategy,
        "fallbackLane": _stable_text(row.get("fallbackLane"), 64),
    }
    if lane == "brain_learning" and FINGERPRINT.fullmatch(
        str(learning_epoch or "").strip().casefold()
    ):
        payload["learningExperimentEpoch"] = str(learning_epoch).strip().casefold()
    return payload


def execution_plan_fingerprint(
    provider: str,
    row: dict[str, Any],
    learning_memory: dict[str, Any] | None = None,
) -> str:
    learning_epoch = (
        learning_experiment_epoch(learning_memory or {}, provider)
        if _stable_text(row.get("lane"), 64) == "brain_learning"
        else ""
    )
    payload = _execution_plan_payload(provider, row, learning_epoch)
    if payload["lane"] not in {"brain_learning", "core_client_learning"}:
        return ""
    has_cause = bool(
        payload["repairScope"]
        or payload["capabilityStrategy"]
        or (
            payload["transportSignature"]
            and payload["transportSignature"] != "not-applicable"
        )
    )
    if not (has_cause and payload["strategyBlueprint"]):
        return ""
    raw = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def select_execution_plan(
    plan: dict[str, Any],
    ledger: dict[str, Any],
    *,
    lane: str,
    requested: list[str] | None = None,
    learning_memory: dict[str, Any] | None = None,
    learning_policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    wanted = {
        safe_provider(value)
        for value in (requested or [])
        if safe_provider(value)
    }
    # None means no filter; an explicitly supplied empty/invalid filter must
    # never broaden a targeted dispatch into the entire Learning lane.
    restrict_to_requested = requested is not None
    rows = ledger.get("providers") if isinstance(ledger.get("providers"), dict) else {}
    eligible: list[dict[str, str]] = []
    repeats: list[str] = []
    missing: list[str] = []
    exhausted = (
        exhausted_learning_providers(learning_memory or {}, learning_policy or {})
        if lane == "BRAIN_LEARNING"
        else set()
    )
    exhausted_rows: list[str] = []

    for execution in plan.get("executions") or []:
        if not isinstance(execution, dict):
            continue
        if str(execution.get("lane") or "") != lane:
            continue
        if execution.get("dispatchAllowed") is not True:
            continue
        for raw_provider in execution.get("providers") or []:
            provider = safe_provider(raw_provider)
            if not provider or (restrict_to_requested and provider not in wanted):
                continue
            if provider in exhausted:
                exhausted_rows.append(provider)
                continue
            learning_epoch = (
                learning_experiment_epoch(learning_memory or {}, provider)
                if lane == "BRAIN_LEARNING"
                else ""
            )
            fingerprint = execution_plan_fingerprint(
                provider, execution, learning_memory=learning_memory
            )
            if not fingerprint:
                missing.append(provider)
                continue
            prior = rows.get(provider) if isinstance(rows.get(provider), dict) else {}
            if fingerprint in dispatched_fingerprints(prior):
                repeats.append(provider)
                continue
            payload = _execution_plan_payload(provider, execution, learning_epoch)
            eligible.append({
                "provider": provider,
                "fingerprint": fingerprint,
                "signatureHash": hashlib.sha256(
                    json.dumps(
                        payload,
                        ensure_ascii=True,
                        sort_keys=True,
                        separators=(",", ":"),
                    ).encode("utf-8")
                ).hexdigest()[:20],
                "learningExperimentEpochHash": learning_epoch[:20],
            })

    # A provider can belong to only one causal lane by execution-plan contract,
    # but de-duplicate defensively without losing stable order.
    seen: set[str] = set()
    deduped: list[dict[str, str]] = []
    for row in eligible:
        provider = row["provider"]
        if provider in seen:
            continue
        seen.add(provider)
        deduped.append(row)
    providers = [row["provider"] for row in deduped]
    return {
        "schemaVersion": 1,
        "source": "execution-plan",
        "lane": lane,
        "eligibleProviderCount": len(providers),
        "eligibleProviders": providers,
        "providerFilter": ",".join(providers),
        "eligible": deduped,
        "suppressedRepeatProviders": sorted(set(repeats)),
        "suppressedMissingFingerprintProviders": sorted(set(missing)),
        "suppressedExhaustedProviders": sorted(set(exhausted_rows)),
        "harnessDifferentialExcludedProviders": [],
        "policy": (
            "autopilot Learning requires a new stable execution-plan cause/method fingerprint; "
            "BRAIN_LEARNING may advance only when durable executed experiment identity changes; "
            "the newest fully exhausted causal group is suppressed; historically dispatched fingerprints are suppressed"
        ),
    }


def latest_plans(brain: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Return the last sanitized plan observed for each provider."""
    out: dict[str, dict[str, Any]] = {}
    for wave in brain.get("waves") or []:
        if not isinstance(wave, dict):
            continue
        for batch in wave.get("batches") or []:
            if not isinstance(batch, dict):
                continue
            summary = batch.get("brain") if isinstance(batch.get("brain"), dict) else {}
            plans = summary.get("plans") if isinstance(summary.get("plans"), dict) else {}
            for plan in plans.values():
                if not isinstance(plan, dict):
                    continue
                provider = safe_provider(plan.get("providerId"))
                if provider:
                    out[provider] = plan
    return out


def select(
    brain: dict[str, Any],
    ledger: dict[str, Any],
    requested: list[str],
) -> dict[str, Any]:
    plans = latest_plans(brain)
    rows = ledger.get("providers") if isinstance(ledger.get("providers"), dict) else {}
    eligible: list[dict[str, str]] = []
    repeats: list[str] = []
    missing: list[str] = []
    harness = {
        safe_provider(value)
        for value in brain.get("harnessDifferentialProviders") or []
        if safe_provider(value)
    }

    for provider in sorted({safe_provider(value) for value in requested if safe_provider(value)}):
        if provider in harness:
            continue
        plan = plans.get(provider)
        if not isinstance(plan, dict):
            missing.append(provider)
            continue
        fingerprint = plan_fingerprint(provider, plan)
        if not fingerprint:
            missing.append(provider)
            continue
        prior = rows.get(provider) if isinstance(rows.get(provider), dict) else {}
        if fingerprint in dispatched_fingerprints(prior):
            repeats.append(provider)
            continue
        eligible.append({
            "provider": provider,
            "fingerprint": fingerprint,
            "signatureHash": hashlib.sha256(
                _stable_text(plan.get("signature"), 160).encode("utf-8")
            ).hexdigest()[:20],
        })

    providers = [row["provider"] for row in eligible]
    return {
        "schemaVersion": 1,
        "eligibleProviderCount": len(providers),
        "eligibleProviders": providers,
        "providerFilter": ",".join(providers),
        "eligible": eligible,
        "suppressedRepeatProviders": repeats,
        "suppressedMissingFingerprintProviders": missing,
        "harnessDifferentialExcludedProviders": sorted(harness & set(requested)),
        "policy": (
            "automatic Learning requires a materially new sanitized provider cause/method "
            "fingerprint; repeats and missing causal fingerprints fail closed"
        ),
    }


def mark_dispatched(
    ledger: dict[str, Any],
    selection: dict[str, Any],
    *,
    repair_run_id: str = "",
    learning_run_id: str = "",
) -> dict[str, Any]:
    providers = ledger.get("providers") if isinstance(ledger.get("providers"), dict) else {}
    providers = {
        safe_provider(key): dict(value)
        for key, value in providers.items()
        if safe_provider(key) and isinstance(value, dict)
    }
    for row in selection.get("eligible") or []:
        if not isinstance(row, dict):
            continue
        provider = safe_provider(row.get("provider"))
        fingerprint = str(row.get("fingerprint") or "").strip().casefold()
        if not provider or not re.fullmatch(r"[0-9a-f]{64}", fingerprint):
            continue
        prior = providers.get(provider, {})
        history = dispatched_fingerprints(prior)
        # A retried mark for an already recorded causal fingerprint is not a
        # second dispatch. Preserve its original run provenance and count.
        if fingerprint in history:
            continue
        history.append(fingerprint)
        dispatches = max(0, min(int(prior.get("dispatchCount") or 0) + 1, 9999))
        providers[provider] = {
            "lastDispatchedFingerprint": fingerprint,
            "dispatchedFingerprints": history,
            "lastSignatureHash": str(row.get("signatureHash") or "")[:20],
            "lastRepairRunId": str(repair_run_id or "")[:32],
            "lastLearningRunId": str(learning_run_id or "")[:32],
            "dispatchCount": dispatches,
        }
    return {
        "schemaVersion": 2,
        "policy": (
            "sanitized automatic Learning dispatch ledger; complete deduplicated per-provider "
            "fingerprint history prevents any previously dispatched causal method from automatic replay"
        ),
        "providerCount": len(providers),
        "providers": dict(sorted(providers.items())),
        "privateContentRetained": False,
    }


def _requested(raw: str, brain: dict[str, Any]) -> list[str]:
    values = [safe_provider(value) for value in str(raw or "").split(",")]
    values = [value for value in values if value]
    # A supplied but invalid target is not permission to select the whole
    # deferred cohort. Only an omitted filter invokes the default cohort.
    if str(raw or "").strip():
        return values
    return [
        safe_provider(value)
        for value in brain.get("deferredLearningProviders") or []
        if safe_provider(value)
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    choose = sub.add_parser("select")
    choose.add_argument("--brain", type=Path, required=True)
    choose.add_argument("--ledger", type=Path, required=True)
    choose.add_argument("--providers", default="")
    choose.add_argument("--output", type=Path, required=True)

    choose_plan = sub.add_parser("select-plan")
    choose_plan.add_argument("--plan", type=Path, required=True)
    choose_plan.add_argument("--ledger", type=Path, required=True)
    choose_plan.add_argument(
        "--lane",
        choices=["BRAIN_LEARNING", "CORE_CLIENT_LEARNING"],
        required=True,
    )
    choose_plan.add_argument("--providers", default="")
    choose_plan.add_argument("--learning-memory", type=Path, default=None)
    choose_plan.add_argument(
        "--brain-policy",
        type=Path,
        default=ROOT / "engine_v2" / "config" / "brain-policy.json",
    )
    choose_plan.add_argument("--output", type=Path, required=True)

    mark = sub.add_parser("mark")
    mark.add_argument("--ledger", type=Path, required=True)
    mark.add_argument("--selection", type=Path, required=True)
    mark.add_argument("--repair-run-id", default="")
    mark.add_argument("--learning-run-id", default="")

    args = parser.parse_args()
    if args.command == "select":
        brain = load(args.brain)
        payload = select(
            brain,
            load(args.ledger, {"schemaVersion": 1, "providers": {}}),
            _requested(args.providers, brain),
        )
        write(args.output, payload)
        print(
            "FIELD_PROVIDER_LEARNING_DISPATCH_GATE "
            f"eligible={payload['eligibleProviderCount']} "
            f"repeat={len(payload['suppressedRepeatProviders'])} "
            f"missing={len(payload['suppressedMissingFingerprintProviders'])} "
            f"harness={len(payload['harnessDifferentialExcludedProviders'])} "
            f"providers={payload['providerFilter'] or 'none'}"
        )
        return 0

    if args.command == "select-plan":
        raw_requested = str(args.providers or "")
        requested = [safe_provider(value) for value in raw_requested.split(",")]
        payload = select_execution_plan(
            load(args.plan),
            load(args.ledger, {"schemaVersion": 2, "providers": {}}),
            lane=args.lane,
            requested=[value for value in requested if value] if raw_requested.strip() else None,
            learning_memory=(
                load(args.learning_memory)
                if args.learning_memory is not None and args.learning_memory.is_file()
                else {}
            ),
            learning_policy=load(args.brain_policy, {}),
        )
        write(args.output, payload)
        print(
            "FIELD_PROVIDER_AUTOPILOT_LEARNING_GATE "
            f"lane={args.lane} eligible={payload['eligibleProviderCount']} "
            f"repeat={len(payload['suppressedRepeatProviders'])} "
            f"missing={len(payload['suppressedMissingFingerprintProviders'])} "
            f"exhausted={len(payload['suppressedExhaustedProviders'])} "
            f"providers={payload['providerFilter'] or 'none'}"
        )
        return 0

    selection = load(args.selection)
    updated = mark_dispatched(
        load(args.ledger, {"schemaVersion": 1, "providers": {}}),
        selection,
        repair_run_id=args.repair_run_id,
        learning_run_id=args.learning_run_id,
    )
    write(args.ledger, updated)
    print(
        "FIELD_PROVIDER_LEARNING_DISPATCH_MARK "
        f"providers={updated['providerCount']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
