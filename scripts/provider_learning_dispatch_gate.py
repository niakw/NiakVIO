#!/usr/bin/env python3
"""Gate automatic Repair -> Learning dispatches on materially new causal methods.

The gate is deliberately independent from Learning's experiment memory. Its job is
cheaper and earlier: do not start a Learning workflow at all when Repair is asking
to replay the same provider/signature/strategy tuple that was already dispatched.

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

PROVIDER_ID = re.compile(r"^[a-z0-9][a-z0-9-]{0,95}$")


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
        "experimentVariant": max(0, int(plan.get("experimentVariant") or 0)),
        "experimentGeneration": max(1, int(plan.get("experimentGeneration") or 1)),
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
        if str(prior.get("lastDispatchedFingerprint") or "").strip().casefold() == fingerprint:
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
        dispatches = max(0, min(int(prior.get("dispatchCount") or 0) + 1, 9999))
        providers[provider] = {
            "lastDispatchedFingerprint": fingerprint,
            "lastSignatureHash": str(row.get("signatureHash") or "")[:20],
            "lastRepairRunId": str(repair_run_id or "")[:32],
            "lastLearningRunId": str(learning_run_id or "")[:32],
            "dispatchCount": dispatches,
        }
    return {
        "schemaVersion": 1,
        "policy": (
            "sanitized automatic Learning dispatch ledger; identical provider causal "
            "fingerprints are never auto-dispatched twice"
        ),
        "providerCount": len(providers),
        "providers": dict(sorted(providers.items())),
        "privateContentRetained": False,
    }


def _requested(raw: str, brain: dict[str, Any]) -> list[str]:
    values = [safe_provider(value) for value in str(raw or "").split(",")]
    values = [value for value in values if value]
    if values:
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
