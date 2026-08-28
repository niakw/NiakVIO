#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import re
import subprocess
import time
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
PLAN_SCRIPT = ROOT / "engine_v2" / "scripts" / "plan-repairs.mjs"
POLICY_PATH = ROOT / "engine_v2" / "config" / "brain-policy.json"
OVERRIDES_PATH = ROOT / "provider-overrides.json"

PLANS: dict[str, dict[str, Any]] = {}
RUNTIME_STATE: dict[str, dict[str, Any]] = {}


def _load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def _strict_json_value(value: Any) -> Any:
    """Normalize Python-only JSON values before crossing the Node planner boundary.

    Python deliberately accepts/emits NaN and infinities by default while
    JavaScript JSON.parse rejects them. Runtime/network evidence can also carry
    malformed Unicode from remote pages. The planner transport is therefore
    ASCII-escaped JSON, so one upstream value can never corrupt the batch.
    """
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, dict):
        return {str(key): _strict_json_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_strict_json_value(item) for item in value]
    if isinstance(value, tuple):
        return [_strict_json_value(item) for item in value]
    return value


def _strict_json_dumps(value: Any, *, indent: int | None = None) -> str:
    return json.dumps(
        _strict_json_value(value),
        ensure_ascii=True,
        allow_nan=False,
        indent=indent,
    )


def _write_json(path: Path, value: Any) -> None:
    path.write_text(_strict_json_dumps(value, indent=2) + "\n", encoding="utf-8")


def _clip_text(value: Any, limit: int = 600) -> str:
    text = str(value or "")
    return text[:limit]


def _planner_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    metadata = candidate.get("metadata") if isinstance(candidate.get("metadata"), dict) else {}
    supported = metadata.get("supportedTypes")
    if isinstance(supported, list):
        supported_types = [_clip_text(item, 64) for item in supported if str(item or "")][:8]
    elif supported:
        supported_types = [_clip_text(supported, 64)]
    else:
        supported_types = []
    return {
        "canonical_id": _clip_text(candidate.get("canonical_id"), 160),
        "upstream_id": _clip_text(candidate.get("upstream_id"), 160),
        "metadata": {"supportedTypes": supported_types},
    }


def _planner_result(result: dict[str, Any]) -> dict[str, Any]:
    evidence = result.get("evidence") if isinstance(result.get("evidence"), dict) else {}
    safe_evidence = {
        key: evidence.get(key)
        for key in (
            "streams_playable",
            "streams_returned",
            "identity_contradiction_count",
            "duration_identity_mismatch_count",
        )
        if key in evidence
    }
    safe_tests: list[dict[str, Any]] = []
    for raw_test in result.get("tests") or []:
        if not isinstance(raw_test, dict):
            continue
        details = raw_test.get("error_details") if isinstance(raw_test.get("error_details"), dict) else {}
        fixture = raw_test.get("fixture") if isinstance(raw_test.get("fixture"), dict) else {}
        observations = []
        for raw_observation in raw_test.get("network_observations") or []:
            if not isinstance(raw_observation, dict):
                continue
            observations.append({
                "status": raw_observation.get("status"),
                "infrastructure": raw_observation.get("infrastructure") is True,
            })
            if len(observations) >= 96:
                break
        safe_tests.append({
            "failure_class": _clip_text(raw_test.get("failure_class"), 160),
            "status": _clip_text(raw_test.get("status"), 160),
            "error_details": {
                "code": _clip_text(details.get("code"), 160),
                "message": _clip_text(details.get("message"), 600),
            },
            "network_observations": observations,
            "fixture": {
                "category": _clip_text(fixture.get("category"), 64),
                "mediaType": _clip_text(fixture.get("mediaType"), 64),
            },
            "streams_playable": raw_test.get("streams_playable"),
            "stream_count": raw_test.get("stream_count"),
            "streams_returned": raw_test.get("streams_returned"),
        })
        if len(safe_tests) >= 12:
            break
    return {
        "status": _clip_text(result.get("status"), 160),
        "evidence": safe_evidence,
        "tests": safe_tests,
    }


def policy() -> dict[str, Any]:
    return _load_json(POLICY_PATH, {})


def learned_skills() -> dict[str, Any]:
    config = _load_json(OVERRIDES_PATH, {})
    runtime = config.get("runtime_repair") if isinstance(config.get("runtime_repair"), dict) else {}
    skills = runtime.get("learned_skills")
    return skills if isinstance(skills, dict) else {}


def reset_runtime_state() -> None:
    PLANS.clear()
    RUNTIME_STATE.clear()


def _provider_state_key(candidate: dict[str, Any], fallback_key: str) -> str:
    provider_id = str(candidate.get("canonical_id") or candidate.get("upstream_id") or "").casefold().strip()
    return provider_id or fallback_key.casefold()


def _ensure_state(candidate: dict[str, Any], plan_key: str) -> dict[str, Any]:
    provider_key = _provider_state_key(candidate, plan_key)
    state = RUNTIME_STATE.setdefault(provider_key, {
        "providerId": provider_key,
        "mutationCount": 0,
        "generatedBytes": 0,
        "signatureCounts": {},
        "firstSeenMonotonic": time.monotonic(),
    })
    return state


def _public_state(candidate: dict[str, Any], plan_key: str) -> dict[str, Any]:
    state = _ensure_state(candidate, plan_key)
    elapsed_ms = max(0, int((time.monotonic() - float(state["firstSeenMonotonic"])) * 1000))
    signature_counts = {
        str(key): int(value)
        for key, value in (state.get("signatureCounts") or {}).items()
        if str(key) and int(value) >= 0
    }
    return {
        "mutationCount": int(state.get("mutationCount") or 0),
        "generatedBytes": int(state.get("generatedBytes") or 0),
        "elapsedMs": elapsed_ms,
        "signatureCounts": signature_counts,
        "repeatedSignatureCount": max(signature_counts.values(), default=0),
        "coreMutationRequested": bool(state.get("coreMutationRequested")),
    }


def runtime_state_snapshot() -> dict[str, dict[str, Any]]:
    snapshot: dict[str, dict[str, Any]] = {}
    for key, state in sorted(RUNTIME_STATE.items()):
        elapsed_ms = max(0, int((time.monotonic() - float(state["firstSeenMonotonic"])) * 1000))
        snapshot[key] = {
            "mutationCount": int(state.get("mutationCount") or 0),
            "generatedBytes": int(state.get("generatedBytes") or 0),
            "elapsedMs": elapsed_ms,
            "signatureCounts": {
                str(signature): int(count)
                for signature, count in sorted((state.get("signatureCounts") or {}).items())
            },
        }
    return snapshot


def _safe_planner_stderr(value: Any) -> str:
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="replace")
    text = re.sub(r"https?://\S+", "<url>", str(value or ""))
    text = re.sub(r"(?i)(token|authorization|cookie|secret)\s*[:=]\s*\S+", r"\1=<redacted>", text)
    return " ".join(text.split())[:600]


def update_plans(registry_path: Path, report: dict[str, Any], mode: str) -> dict[str, dict[str, Any]]:
    registry = _load_json(registry_path, {})
    candidates = {
        str(row.get("key")): row
        for row in registry.get("candidates") or []
        if isinstance(row, dict) and row.get("key")
    }
    items = []
    for result in report.get("results") or []:
        if not isinstance(result, dict) or not result.get("key"):
            continue
        raw_key = str(result["key"])
        candidate = candidates.get(raw_key)
        if not candidate:
            continue
        parent_key = str((candidate.get("runtime_repair") or {}).get("parent_key") or "")
        plan_key = parent_key or raw_key
        # A child retest is outcome evidence for the original causal plan. Do not
        # overwrite that diagnosis with "healthy" after the repair succeeds.
        if parent_key and plan_key in PLANS:
            continue
        items.append({
            "key": plan_key,
            "candidate": _planner_candidate(candidate),
            "result": _planner_result(result),
            "state": _public_state(candidate, plan_key),
        })
    if not items:
        return PLANS
    payload = {
        "mode": mode,
        "policy": policy(),
        "learnedSkills": learned_skills() if str(mode).casefold() == "learning" else {},
        "items": items,
    }
    planner_input = _strict_json_dumps(payload).encode("ascii")
    try:
        completed = subprocess.run(
            ["node", str(PLAN_SCRIPT)], cwd=ROOT,
            input=planner_input,
            capture_output=True, check=True, timeout=30,
        )
    except subprocess.CalledProcessError as exc:
        detail = _safe_planner_stderr(exc.stderr)
        raise RuntimeError(f"ARCHI2 Brain planner failed (exit={exc.returncode}; stderr={detail or 'empty'}; bytes={len(planner_input)})") from exc
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("ARCHI2 Brain planner exceeded its 30s control-plane timeout") from exc
    try:
        parsed = json.loads((completed.stdout or b"{}").decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("ARCHI2 Brain planner returned invalid JSON") from exc
    for key, row in (parsed.get("plans") or {}).items():
        if isinstance(row, dict):
            PLANS[str(key)] = row
    return PLANS


def wrap_run_health(base_run_health: Callable[..., dict[str, Any]], mode: str) -> Callable[..., dict[str, Any]]:
    def _run_health(*, stage: Path, registry_path: Path, output_dir: Path, mode: str = mode, health_check: Path):
        report = base_run_health(stage=stage, registry_path=registry_path, output_dir=output_dir, mode=mode, health_check=health_check)
        update_plans(registry_path, report, mode)
        return report
    return _run_health


def wrap_matching_profiles(base_matching: Callable[..., list[str]]) -> Callable[..., list[str]]:
    def _matching(candidate: dict[str, Any], result: dict[str, Any], source_text: str, config: dict[str, Any] | None = None) -> list[str]:
        profiles = list(base_matching(candidate, result, source_text, config))
        key = str(candidate.get("key") or "")
        plan = PLANS.get(key) or {}
        action = str(plan.get("action") or "")
        if action in {"none", "deferred_retry", "collect-more-evidence", "hold-or-quarantine-pending-proof"}:
            return []
        allowed = {str(value) for value in plan.get("allowedProfiles") or [] if str(value)}
        return [profile for profile in profiles if profile in allowed]
    return _matching


def _budget_error(candidate: dict[str, Any], plan_key: str, plan: dict[str, Any]) -> str | None:
    state = _public_state(candidate, plan_key)
    production = policy().get("production") if isinstance(policy().get("production"), dict) else {}
    if state["mutationCount"] >= int(production.get("maxMutationsPerProvider") or 2):
        return "brain_mutation_budget_exhausted"
    signature = str(plan.get("signature") or "")
    repeats = int((state.get("signatureCounts") or {}).get(signature) or 0) if signature else 0
    if repeats >= int(production.get("maxRepeatedSignature") or 2):
        return "brain_repair_loop_detected"
    if state["generatedBytes"] >= int(production.get("maxGeneratedBytesPerProvider") or 180000):
        return "brain_generated_code_budget_exhausted"
    if state["elapsedMs"] >= int(production.get("maxElapsedMsPerProvider") or 45000):
        return "brain_time_budget_exhausted"
    return None


def _discard_generated_candidate(stage: Path, repaired: dict[str, Any] | None) -> None:
    if not isinstance(repaired, dict) or not repaired.get("local_path"):
        return
    path = (stage / str(repaired["local_path"])).resolve()
    root = (stage / "providers" / "runtime-repairs").resolve()
    try:
        path.relative_to(root)
    except ValueError:
        return
    path.unlink(missing_ok=True)


def wrap_create_repair_candidate(base_create: Callable[..., tuple[dict[str, Any] | None, str | None]]) -> Callable[..., tuple[dict[str, Any] | None, str | None]]:
    """Enforce production Brain budgets around actual code mutation attempts.

    Budgets are shared by canonical provider family, not by upstream variant, so
    three siblings cannot each consume a fresh mutation/loop allowance.
    """
    def _create(stage: Path, candidate: dict[str, Any], profile_name: str, round_number: int):
        parent_key = str((candidate.get("runtime_repair") or {}).get("parent_key") or "")
        plan_key = parent_key or str(candidate.get("key") or "")
        plan = PLANS.get(plan_key) or {}
        if str(plan.get("action") or "") != "probe-targeted-repair":
            return None, "brain_not_repairing"
        error = _budget_error(candidate, plan_key, plan)
        if error:
            return None, error

        state = _ensure_state(candidate, plan_key)
        signature = str(plan.get("signature") or plan.get("failureClass") or "unknown_failure")
        state["mutationCount"] = int(state.get("mutationCount") or 0) + 1
        signature_counts = state.setdefault("signatureCounts", {})
        signature_counts[signature] = int(signature_counts.get(signature) or 0) + 1

        repaired, create_error = base_create(stage, candidate, profile_name, round_number)
        if not isinstance(repaired, dict):
            return repaired, create_error

        parent_bytes = max(0, int(candidate.get("bytes") or 0))
        repaired_bytes = max(0, int(repaired.get("bytes") or 0))
        generated_delta = max(0, repaired_bytes - parent_bytes)
        state["generatedBytes"] = int(state.get("generatedBytes") or 0) + generated_delta

        production = policy().get("production") if isinstance(policy().get("production"), dict) else {}
        if int(state["generatedBytes"]) > int(production.get("maxGeneratedBytesPerProvider") or 180000):
            _discard_generated_candidate(stage, repaired)
            return None, "brain_generated_code_budget_exhausted"
        if _public_state(candidate, plan_key)["elapsedMs"] > int(production.get("maxElapsedMsPerProvider") or 45000):
            _discard_generated_candidate(stage, repaired)
            return None, "brain_time_budget_exhausted"
        return repaired, create_error
    return _create


def annotate_and_learn(output_dir: Path, mode: str) -> dict[str, Any]:
    report_path = output_dir / "repair-report.json"
    report = _load_json(report_path, {})
    learning_mode = str(mode).casefold() == "learning"
    config = _load_json(OVERRIDES_PATH, {}) if learning_mode else {}
    runtime = config.setdefault("runtime_repair", {}) if learning_mode else {}
    skills = runtime.setdefault("learned_skills", {}) if learning_mode else {}
    if learning_mode and not isinstance(skills, dict):
        skills = {}
        runtime["learned_skills"] = skills
    maturity = policy().get("skillMaturity") or {}

    accepted_count = 0
    if learning_mode:
        for round_row in report.get("rounds") or []:
            attempts_by_parent: dict[str, list[dict[str, Any]]] = {}
            for attempt in round_row.get("attempts") or []:
                if isinstance(attempt, dict):
                    attempts_by_parent.setdefault(str(attempt.get("parent_key") or ""), []).append(attempt)
            for accepted in round_row.get("accepted") or []:
                if not isinstance(accepted, dict):
                    continue
                parent_key = str(accepted.get("parent_key") or "")
                plan = PLANS.get(parent_key) or {}
                provider_id = str(plan.get("providerId") or parent_key.split(":")[-1]).casefold()
                profile = str(accepted.get("profile") or "")
                if not profile:
                    generated = [row for row in attempts_by_parent.get(parent_key, []) if row.get("status") == "generated" and row.get("profile")]
                    if generated:
                        profile = str(generated[0]["profile"])
                failure_class = str(plan.get("failureClass") or "unknown_failure")
                if not profile or failure_class in {"healthy", "identity_mismatch"}:
                    continue
                skill_id = f"{failure_class}:{profile}"
                skill = skills.setdefault(skill_id, {
                    "id": skill_id,
                    "failureClass": failure_class,
                    "profile": profile,
                    "actions": [f"apply validated {profile} strategy for {failure_class}"],
                    "capabilities": sorted({cap for hyp in plan.get("hypotheses") or [] for cap in hyp.get("capabilities") or []}),
                    "providers": [], "successCount": 0, "failureCount": 0, "validated": True,
                })
                providers = {str(value).casefold() for value in skill.get("providers") or [] if str(value)}
                if provider_id:
                    providers.add(provider_id)
                skill["providers"] = sorted(providers)
                skill["successCount"] = int(skill.get("successCount") or 0) + 1
                skill["lastValidatedMode"] = mode
                successes = int(skill["successCount"])
                failures = int(skill.get("failureCount") or 0)
                confidence = successes / max(1, successes + failures)
                trusted = (
                    successes >= int(maturity.get("trustedSuccesses") or 3)
                    and len(providers) >= int(maturity.get("trustedProviders") or 2)
                    and confidence >= float(maturity.get("minimumConfidence") or 0.8)
                )
                skill["confidence"] = round(confidence, 4)
                skill["maturity"] = "trusted" if trusted else ("candidate" if successes >= int(maturity.get("candidateSuccesses") or 2) else "experimental")
                skill["autoApply"] = trusted
                accepted_count += 1

        for round_row in report.get("rounds") or []:
            for rejected in round_row.get("rejected") or []:
                if not isinstance(rejected, dict):
                    continue
                parent_key = str(rejected.get("parent_key") or "")
                plan = PLANS.get(parent_key) or {}
                profile = str(rejected.get("profile") or "")
                failure_class = str(plan.get("failureClass") or "")
                skill_id = f"{failure_class}:{profile}"
                skill = skills.get(skill_id)
                if not isinstance(skill, dict) or not profile:
                    continue
                skill["failureCount"] = int(skill.get("failureCount") or 0) + 1
                successes = int(skill.get("successCount") or 0)
                failures = int(skill["failureCount"])
                skill["confidence"] = round(successes / max(1, successes + failures), 4)
                if skill["confidence"] < float(maturity.get("minimumConfidence") or 0.8):
                    skill["autoApply"] = False
                    if skill.get("maturity") == "trusted":
                        skill["maturity"] = "candidate"

    brain_versions = [int(row.get("brainVersion") or 0) for row in PLANS.values() if isinstance(row, dict)]
    if learning_mode:
        runtime["brain"] = {
            "name": str((policy().get("identity") or {}).get("name") or "NiakVIO Brain"),
            "controlPlaneVersion": max(brain_versions, default=0),
            "learningOnValidatedRepair": True,
            "lastMode": mode,
            "fallbackPolicy": "lkg_only_after_repair_budget",
            "coreMutationPolicy": "proposal_only",
        }
        _write_json(OVERRIDES_PATH, config)

    sanitized_plans = {
        key: {
            "providerId": row.get("providerId"), "failureClass": row.get("failureClass"),
            "brainVersion": row.get("brainVersion"),
            "signature": row.get("signature"), "action": row.get("action"),
            "exitReason": row.get("exitReason"),
            "hypotheses": [hyp.get("id") for hyp in row.get("hypotheses") or []],
            "allowedProfiles": row.get("allowedProfiles") or [],
            "plannerErrorClass": row.get("plannerErrorClass"),
        }
        for key, row in sorted(PLANS.items())
    }
    report["brain"] = {
        "name": str((policy().get("identity") or {}).get("name") or "NiakVIO Brain"),
        "mode": mode,
        "plans": sanitized_plans,
        "budgetState": runtime_state_snapshot(),
        "learnedEvents": accepted_count if learning_mode else 0,
        "learningExecuted": learning_mode,
        "learningLane": "independent_daily_lab" if learning_mode else "none_core_repair_only",
        "queuedForLearning": sorted({
            str(row.get("providerId") or key)
            for key, row in PLANS.items()
            if isinstance(row, dict) and str(row.get("repairScope") or "") in {"learning", "deferred"}
        }),
        "privacy": "sanitized-no-raw-endpoints-tokens-header-values-private-notes",
    }
    _write_json(report_path, report)
    return report["brain"]
