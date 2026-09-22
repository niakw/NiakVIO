#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
import math
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from brain_positive_program_memory import learned_skills as positive_program_learned_skills
PLAN_SCRIPT = ROOT / "engine_v2" / "scripts" / "plan-repairs.mjs"
POLICY_PATH = ROOT / "engine_v2" / "config" / "brain-policy.json"
OVERRIDES_PATH = ROOT / "provider-overrides.json"
CENSUS_STATUS_PATH = ROOT / "automation" / "provider-census-status.json"
REPAIR_MEMORY_PATH = ROOT / "automation" / "brain-repair-memory.json"
EXPERIENCE_PATH = ROOT / "automation" / "brain-repair-experience.json"
LEARNING_MEMORY_PATH = Path(os.environ.get("NIAKVIO_BRAIN_LEARNING_MEMORY", "")).resolve() if os.environ.get("NIAKVIO_BRAIN_LEARNING_MEMORY") else None

PLANS: dict[str, dict[str, Any]] = {}
RUNTIME_STATE: dict[str, dict[str, Any]] = {}

POST_EXHAUSTION_STRATEGY_PROFILES = {
    "transport_request_differential_v1",
    "route_transition_graph_v1",
    "route_peer_transition_replay_v1",
    "terminal_transition_graph_v1",
    "terminal_request_program_inference_v1",
    "candidate_divergence_trace_v1",
    "candidate_request_program_replay_v1",
    "player_protocol_family_replay_v1",
    "media_response_shape_inference_v1",
    "search_contract_inference_v1",
    "search_response_route_binding_v1",
}


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


def _census_prior(provider_id: str) -> dict[str, Any]:
    status = _load_json(CENSUS_STATUS_PATH, {})
    wanted = str(provider_id or "").strip().casefold()
    if not wanted or not isinstance(status, dict):
        return {}
    for row in status.get("providers") or []:
        if not isinstance(row, dict):
            continue
        if str(row.get("provider") or "").strip().casefold() != wanted:
            continue
        return {
            "status": _clip_text(row.get("status"), 80),
            "dominantIssue": _clip_text(row.get("dominantIssue"), 240),
            "evidenceDepth": [_clip_text(value, 120) for value in (row.get("evidenceDepth") or [])[:8]],
            "latestLaneVerdicts": [_clip_text(value, 180) for value in (row.get("latestLaneVerdicts") or [])[:8]],
            "routeProof": [_clip_text(value, 180) for value in (row.get("routeProof") or [])[:8]],
            "candidateProof": [_clip_text(value, 180) for value in (row.get("candidateProof") or [])[:8]],
            "currentVerifiedLanes": [_clip_text(value, 48) for value in (row.get("currentVerifiedLanes") or [])[:8]],
            "repairEligible": row.get("repairEligible") is True,
            "knowledgeRole": "monotonic-diagnostic-prior-only",
        }
    return {}


def _planner_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    metadata = candidate.get("metadata") if isinstance(candidate.get("metadata"), dict) else {}
    supported = metadata.get("supportedTypes")
    if isinstance(supported, list):
        supported_types = [_clip_text(item, 64) for item in supported if str(item or "")][:8]
    elif supported:
        supported_types = [_clip_text(supported, 64)]
    else:
        supported_types = []

    raw_model = candidate.get("clean_provider_model") if isinstance(candidate.get("clean_provider_model"), dict) else {}
    model = {
        "strategy": _clip_text(raw_model.get("strategy"), 80),
        "knownSite": _clip_text(raw_model.get("knownSite"), 240),
        "officialSite": _clip_text(raw_model.get("officialSite"), 240),
        "officialHub": _clip_text(raw_model.get("officialHub"), 240),
        "officialApi": _clip_text(raw_model.get("officialApi"), 240),
        "fixedApi": _clip_text(raw_model.get("fixedApi"), 240),
        "origins": [_clip_text(value, 240) for value in (raw_model.get("origins") or [])[:24]],
        "routes": [_clip_text(value, 240) for value in (raw_model.get("routes") or [])[:32]],
        "observedUrls": [_clip_text(value, 320) for value in (raw_model.get("observedUrls") or [])[:32]],
        "knowledgeRole": "structured-observation-only",
        "legacyCodeExecuted": False,
    }
    return {
        "canonical_id": _clip_text(candidate.get("canonical_id"), 160),
        "upstream_id": _clip_text(candidate.get("upstream_id"), 160),
        "metadata": {"supportedTypes": supported_types},
        "provider_base_reconstruction_required": candidate.get("provider_base_reconstruction_required") is True,
        "clean_reconstruction_mode": candidate.get("clean_reconstruction_mode") is True,
        "candidate_code_origin": _clip_text(candidate.get("candidate_code_origin"), 120),
        "clean_provider_model": model,
        "censusPrior": _census_prior(str(candidate.get("canonical_id") or candidate.get("upstream_id") or "")),
        "upstream_code_role": "knowledge-only",
        "upstream_code_executed": False,
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
            hint_keys = []
            for hint in raw_observation.get("response_value_hints") or []:
                if not isinstance(hint, dict):
                    continue
                key = _clip_text(hint.get("key"), 64).casefold()
                if key and key not in hint_keys:
                    hint_keys.append(key)
                if len(hint_keys) >= 24:
                    break
            body_fields = [
                _clip_text(value, 64)
                for value in (raw_observation.get("proof_body_fields") or [])[:24]
                if _clip_text(value, 64)
            ]
            observations.append({
                "status": raw_observation.get("status"),
                "ok": raw_observation.get("ok") is True,
                "infrastructure": raw_observation.get("infrastructure") is True,
                "stage": _clip_text(raw_observation.get("stage"), 64).casefold(),
                "method": _clip_text(raw_observation.get("method"), 16).upper(),
                "path_pattern": _clip_text(raw_observation.get("path_pattern"), 360),
                "content_type": _clip_text(raw_observation.get("content_type"), 120).casefold(),
                "proof_body_kind": _clip_text(raw_observation.get("proof_body_kind"), 24).casefold(),
                "proof_body_fields": body_fields,
                "response_hint_keys": hint_keys,
                "route_proof_trace": raw_observation.get("route_proof_trace") is True,
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


def _learning_memory_skills() -> dict[str, Any]:
    if LEARNING_MEMORY_PATH is None:
        return {}
    value = _load_json(LEARNING_MEMORY_PATH, {})
    if not isinstance(value, dict):
        return {}
    if value.get("publicationAllowed") is not False or value.get("productionWritesAllowed") is not False:
        return {}
    raw = value.get("learnedSkills")
    if not isinstance(raw, dict):
        return {}
    return {
        str(key): copy.deepcopy(skill)
        for key, skill in list(raw.items())[:400]
        if isinstance(skill, dict) and skill.get("validated") is True
    }


def learned_skills() -> dict[str, Any]:
    config = _load_json(OVERRIDES_PATH, {})
    runtime = config.get("runtime_repair") if isinstance(config.get("runtime_repair"), dict) else {}
    raw = runtime.get("learned_skills")
    merged = copy.deepcopy(raw) if isinstance(raw, dict) else {}
    # Persistent Learning memory is an input prior only. It has already been
    # sanitized by sanitize_brain_learning_memory.py and still passes the same
    # maturity/confidence/provider-diversity policy below before Repair can use it.
    for key, learned in _learning_memory_skills().items():
        current = merged.get(key)
        if not isinstance(current, dict):
            merged[key] = copy.deepcopy(learned)
            continue
        providers = sorted({
            str(value or "").strip().casefold()
            for value in [*(current.get("providers") or []), *(learned.get("providers") or [])]
            if str(value or "").strip()
        })
        current["providers"] = providers
        current["validated"] = current.get("validated") is True or learned.get("validated") is True
        current["successCount"] = max(int(current.get("successCount") or 0), int(learned.get("successCount") or 0))
        current["failureCount"] = max(int(current.get("failureCount") or 0), int(learned.get("failureCount") or 0))
        current["confidence"] = max(float(current.get("confidence") or 0.0), float(learned.get("confidence") or 0.0))
        maturity_rank = {"experimental": 0, "candidate": 1, "trusted": 2}
        if maturity_rank.get(str(learned.get("maturity") or "experimental"), 0) > maturity_rank.get(str(current.get("maturity") or "experimental"), 0):
            current["maturity"] = learned.get("maturity")
        current["autoApply"] = False
    # A globally rejected Repair publication must not erase a strictly validated
    # provider-local success. Positive-program memory is sanitized DATA/prior only;
    # it never grants publication authority or bypasses current-byte gates.
    for key, positive in positive_program_learned_skills().items():
        if not isinstance(positive, dict):
            continue
        current = merged.get(key)
        if not isinstance(current, dict):
            merged[key] = copy.deepcopy(positive)
            continue
        providers = sorted({
            str(value or "").strip().casefold()
            for value in [*(current.get("providers") or []), *(positive.get("providers") or [])]
            if str(value or "").strip()
        })
        signatures = sorted({
            str(value or "").strip()
            for value in [*(current.get("signatures") or []), *(positive.get("signatures") or [])]
            if str(value or "").strip()
        })
        current["providers"] = providers
        current["signatures"] = signatures
        current["validated"] = current.get("validated") is True or positive.get("validated") is True
        current["successCount"] = max(
            int(current.get("successCount") or 0),
            int(positive.get("successCount") or 0),
        )
        current["confidence"] = max(
            float(current.get("confidence") or 0.0),
            float(positive.get("confidence") or 0.0),
        )
    return merged


def planner_learned_skills(mode: str) -> dict[str, Any]:
    """Expose all skills to Learning, trusted transferable skills to Repair."""
    skills = learned_skills()
    if str(mode).casefold() == "learning":
        return skills
    cfg = policy()
    production = cfg.get("production") if isinstance(cfg.get("production"), dict) else {}
    if production.get("learnedSkillInputAllowed") is not True:
        return {}
    maturity = cfg.get("skillMaturity") if isinstance(cfg.get("skillMaturity"), dict) else {}
    transfer = production.get("learnedSkillTransferPolicy") if isinstance(production.get("learnedSkillTransferPolicy"), dict) else {}
    required_maturity = str(transfer.get("maturity") or "trusted")
    min_confidence = float(transfer.get("minimumConfidence") or maturity.get("minimumConfidence") or 0.8)
    min_providers = max(1, int(transfer.get("minimumDistinctProviders") or maturity.get("trustedProviders") or 2))
    out: dict[str, Any] = {}
    for key, raw in skills.items():
        if not isinstance(raw, dict) or raw.get("validated") is not True:
            continue
        if str(raw.get("maturity") or "experimental") != required_maturity:
            continue
        if float(raw.get("confidence") or 0.0) < min_confidence:
            continue
        providers = {
            str(value or "").strip().casefold()
            for value in raw.get("providers") or []
            if str(value or "").strip()
        }
        if len(providers) < min_providers:
            continue
        out[str(key)] = raw
    return out


def _memory_entry_key(row: dict[str, Any]) -> tuple[str, str, str, str, str, int, int]:
    return (
        _clip_text(row.get("providerId"), 160).casefold(),
        _clip_text(row.get("providerVersion") or "*", 64),
        _clip_text(row.get("failureClass"), 96),
        _clip_text(row.get("signature"), 160),
        _clip_text(row.get("profile"), 96),
        max(0, int(row.get("experimentVariant") or 0)),
        max(1, int(row.get("experimentGeneration") or 1)),
    )


def _learning_experiment_entries() -> list[dict[str, Any]]:
    if LEARNING_MEMORY_PATH is None:
        return []
    value = _load_json(LEARNING_MEMORY_PATH, {})
    if not isinstance(value, dict):
        return []
    if value.get("publicationAllowed") is not False or value.get("productionWritesAllowed") is not False:
        return []
    memory = value.get("experimentMemory") if isinstance(value.get("experimentMemory"), dict) else {}
    rows = memory.get("entries") if isinstance(memory.get("entries"), list) else []
    out: list[dict[str, Any]] = []
    for raw in rows[:1000]:
        if not isinstance(raw, dict):
            continue
        provider = _clip_text(raw.get("providerId"), 160).casefold()
        signature = _clip_text(raw.get("signature"), 160)
        profile = _clip_text(raw.get("profile"), 96)
        if not provider or not signature or not profile:
            continue
        last_outcome = _clip_text(raw.get("lastOutcome"), 48)
        execution_observed = raw.get("executionObserved") is True
        # Memory published before the exact-ledger fix could mark a newly
        # planned post-g5 strategy as profile_unavailable without ever running
        # it. Such rows are applicability noise, not executed negative evidence,
        # and must not exhaust the evolved-strategy family.
        if (
            profile in POST_EXHAUSTION_STRATEGY_PROFILES
            and last_outcome == "profile_unavailable"
            and not execution_observed
        ):
            continue
        out.append({
            "providerId": provider,
            "providerVersion": _clip_text(raw.get("providerVersion") or "*", 64),
            "failureClass": _clip_text(raw.get("failureClass"), 96),
            "signature": signature,
            "profile": profile,
            "experimentVariant": max(0, int(raw.get("experimentVariant") or 0)),
            "experimentGeneration": max(1, int(raw.get("experimentGeneration") or 1)),
            "capabilityStrategy": _clip_text(raw.get("capabilityStrategy"), 96).casefold(),
            "observedPipelineStage": _clip_text(raw.get("observedPipelineStage"), 64).casefold(),
            "attempts": max(0, int(raw.get("attempts") or 0)),
            "failures": max(0, int(raw.get("failures") or 0)),
            "consecutiveFailures": max(0, int(raw.get("consecutiveFailures") or 0)),
            "successes": max(0, int(raw.get("successes") or 0)),
            "progresses": max(0, int(raw.get("progresses") or 0)),
            "lastOutcome": last_outcome,
            "lastReason": _clip_text(raw.get("lastReason"), 240),
            "executionObserved": execution_observed,
        })
    return out


def repair_memory() -> dict[str, Any]:
    value = _load_json(REPAIR_MEMORY_PATH, {})
    if not isinstance(value, dict):
        value = {}
    entries = [row for row in (value.get("entries") or []) if isinstance(row, dict)][:1000]

    # Production Repair remains anchored to automation/brain-repair-memory.json.
    # Only the isolated Learning planner may overlay the read-only sanitized
    # experiment memory published by the previous Learning phase.
    if str(os.environ.get("NUVIO_BRAIN_PLANNER_MODE") or "").strip().casefold() == "learning":
        merged: dict[tuple[str, str, str, str, str, int, int], dict[str, Any]] = {
            _memory_entry_key(row): copy.deepcopy(row)
            for row in entries
        }
        for incoming in _learning_experiment_entries():
            key = _memory_entry_key(incoming)
            current = merged.get(key)
            if current is None:
                merged[key] = copy.deepcopy(incoming)
                continue
            next_row = copy.deepcopy(current)
            for field in (
                "attempts", "failures", "consecutiveFailures",
                "successes", "progresses",
            ):
                next_row[field] = max(
                    max(0, int(current.get(field) or 0)),
                    max(0, int(incoming.get(field) or 0)),
                )
            for field in (
                "failureClass", "capabilityStrategy", "observedPipelineStage",
                "lastOutcome", "lastReason",
            ):
                if str(incoming.get(field) or ""):
                    next_row[field] = incoming[field]
            next_row["experimentVariant"] = incoming["experimentVariant"]
            next_row["experimentGeneration"] = incoming["experimentGeneration"]
            merged[key] = next_row
        entries = list(merged.values())

    return {
        "schemaVersion": max(1, int(value.get("schemaVersion") or 1)),
        "entries": entries[:1000],
    }


def planner_historical_solutions() -> list[dict[str, Any]]:
    """Expose only sanitized NiakVIO historical solution classes to the planner.

    Historical cases are priors, never proof or mutation authority. The Node
    planner may only map whitelisted solutionClass values to repair profiles it
    already knows how to execute and every candidate still passes the ordinary
    current-byte/identity/playback gates.
    """
    value = _load_json(EXPERIENCE_PATH, {})
    if not isinstance(value, dict) or value.get("role") != "repair-prior-only":
        return []
    safety = value.get("safety") if isinstance(value.get("safety"), dict) else {}
    if safety.get("directMutationAuthority") is not False:
        return []
    out: list[dict[str, Any]] = []
    for raw in value.get("historicalCases") or []:
        if not isinstance(raw, dict):
            continue
        case_id = _clip_text(raw.get("id"), 160)
        failure = _clip_text(raw.get("failureClass"), 96).casefold()
        solution = _clip_text(raw.get("solutionClass"), 128).casefold()
        providers = [
            _clip_text(provider, 160).casefold()
            for provider in raw.get("providers") or []
            if str(provider or "").strip()
        ][:64]
        if not case_id or not failure or not solution:
            continue
        out.append({
            "id": case_id,
            "failureClass": failure,
            "solutionClass": solution,
            "providers": providers,
            "priorOnly": True,
        })
        if len(out) >= 512:
            break
    return out


def planner_negative_memory(_mode: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for raw in repair_memory().get("entries") or []:
        rows.append({
            "providerId": _clip_text(raw.get("providerId"), 160).casefold(),
            "providerVersion": _clip_text(raw.get("providerVersion") or "*", 64),
            "failureClass": _clip_text(raw.get("failureClass"), 96),
            "signature": _clip_text(raw.get("signature"), 96),
            "profile": _clip_text(raw.get("profile"), 96),
            "experimentVariant": max(0, int(raw.get("experimentVariant") or 0)),
            "experimentGeneration": max(1, int(raw.get("experimentGeneration") or 1)),
            "capabilityStrategy": _clip_text(raw.get("capabilityStrategy"), 96).casefold(),
            "observedPipelineStage": _clip_text(raw.get("observedPipelineStage"), 64).casefold(),
            "failures": max(0, int(raw.get("failures") or 0)),
            "consecutiveFailures": max(0, int(raw.get("consecutiveFailures") or 0)),
            "successes": max(0, int(raw.get("successes") or 0)),
            "executionObserved": raw.get("executionObserved") is True,
        })
    return rows


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


def _execute_planner(items: list[dict[str, Any]], mode: str) -> dict[str, dict[str, Any]]:
    if not items:
        return PLANS
    payload = {
        "mode": mode,
        "explorationChain": _exploration_chain_enabled(),
        "policy": policy(),
        "learnedSkills": planner_learned_skills(mode),
        "historicalSolutions": planner_historical_solutions(),
        "negativeMemory": planner_negative_memory(mode),
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


def replan_observation(
    candidate: dict[str, Any],
    result: dict[str, Any],
    *,
    plan_key: str | None = None,
    mode: str = "deep",
) -> dict[str, Any]:
    """Replan one exploration-only parent from its newly observed runtime state."""
    key = str(plan_key or candidate.get("key") or "")
    if not key:
        return {}
    _execute_planner(
        [{
            "key": key,
            "candidate": _planner_candidate(candidate),
            "result": _planner_result(result),
            "state": _public_state(candidate, key),
        }],
        mode,
    )
    return PLANS.get(key) or {}


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
        # Child retests remain outcome evidence for their original causal plan.
        # Exploration-only parents are replanned explicitly by _brain_matching
        # after Deep has proven that the child made safe diagnostic progress.
        if parent_key and plan_key in PLANS:
            continue
        items.append({
            "key": plan_key,
            "candidate": _planner_candidate(candidate),
            "result": _planner_result(result),
            "state": _public_state(candidate, plan_key),
        })
    return _execute_planner(items, mode)


def wrap_run_health(base_run_health: Callable[..., dict[str, Any]], mode: str) -> Callable[..., dict[str, Any]]:
    def _run_health(*, stage: Path, registry_path: Path, output_dir: Path, mode: str = mode, health_check: Path):
        report = base_run_health(stage=stage, registry_path=registry_path, output_dir=output_dir, mode=mode, health_check=health_check)
        update_plans(registry_path, report, mode)
        return report
    return _run_health


def wrap_matching_profiles(base_matching: Callable[..., list[str]]) -> Callable[..., list[str]]:
    def _matching(candidate: dict[str, Any], result: dict[str, Any], source_text: str, config: dict[str, Any] | None = None) -> list[str]:
        key = str(candidate.get("key") or "")
        plan = PLANS.get(key) or {}
        action = str(plan.get("action") or "")
        if action in {"none", "deferred_retry", "collect-more-evidence", "hold-or-quarantine-pending-proof"}:
            return []
        # Matching must see the same causal experiment snapshot as candidate
        # creation. Otherwise final named strategy profiles are invisible during
        # applicability filtering and become profile_unavailable before they can
        # execute.
        candidate["brain_repair_plan"] = copy.deepcopy(_plan_snapshot(plan))
        profiles = list(base_matching(candidate, result, source_text, config))
        allowed_order = [str(value) for value in plan.get("allowedProfiles") or [] if str(value)]
        allowed = set(allowed_order)
        order = {profile: index for index, profile in enumerate(allowed_order)}
        selected = [profile for profile in profiles if profile in allowed]
        return sorted(selected, key=lambda profile: (order.get(profile, len(order)), profiles.index(profile)))
    return _matching


def _exploration_chain_enabled() -> bool:
    return (
        str(__import__("os").environ.get("NUVIO_BRAIN_EXPLORATION_CHAIN") or "").strip() == "1"
        and str(__import__("os").environ.get("NUVIO_BRAIN_PLANNER_MODE") or "").strip().casefold() != "learning"
    )


def _production_budget() -> dict[str, int]:
    current_policy = policy()
    production = current_policy.get("production") if isinstance(current_policy.get("production"), dict) else {}
    selected = production
    if _exploration_chain_enabled():
        raw = production.get("explorationChainBudget")
        if isinstance(raw, dict):
            selected = {**production, **raw}
    return {
        "maxMutationsPerProvider": int(selected.get("maxMutationsPerProvider") or 2),
        "maxRepeatedSignature": int(selected.get("maxRepeatedSignature") or 2),
        "maxGeneratedBytesPerProvider": int(selected.get("maxGeneratedBytesPerProvider") or 180000),
        "maxElapsedMsPerProvider": int(selected.get("maxElapsedMsPerProvider") or 45000),
    }


def _budget_error(candidate: dict[str, Any], plan_key: str, plan: dict[str, Any]) -> str | None:
    state = _public_state(candidate, plan_key)
    current_policy = policy()
    learning_mode = str(__import__("os").environ.get("NUVIO_BRAIN_PLANNER_MODE") or "").strip().casefold() == "learning"
    if learning_mode:
        deadline_raw = str(__import__("os").environ.get("NUVIO_BRAIN_DEADLINE_EPOCH_MS") or "").strip()
        if deadline_raw:
            try:
                if int(time.time() * 1000) >= int(deadline_raw):
                    return "brain_learning_time_budget_exhausted"
            except ValueError:
                pass
        return None

    budget = _production_budget()
    if state["mutationCount"] >= budget["maxMutationsPerProvider"]:
        return "brain_mutation_budget_exhausted"
    signature = str(plan.get("signature") or "")
    repeats = int((state.get("signatureCounts") or {}).get(signature) or 0) if signature else 0
    if repeats >= budget["maxRepeatedSignature"]:
        return "brain_repair_loop_detected"
    if state["generatedBytes"] >= budget["maxGeneratedBytesPerProvider"]:
        return "brain_generated_code_budget_exhausted"
    if state["elapsedMs"] >= budget["maxElapsedMsPerProvider"]:
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


def _plan_snapshot(plan: dict[str, Any]) -> dict[str, Any]:
    """Freeze the causal planner decision attached to one concrete experiment."""
    return {
        "providerId": str(plan.get("providerId") or ""),
        "failureClass": str(plan.get("failureClass") or ""),
        "signature": str(plan.get("signature") or ""),
        "experimentVariant": max(0, int(plan.get("experimentVariant") or 0)),
        "experimentGeneration": max(1, int(plan.get("experimentGeneration") or 1)),
        "negativeMemoryMatches": max(0, int(plan.get("negativeMemoryMatches") or 0)),
        "observedPipelineStage": str(plan.get("observedPipelineStage") or ""),
        "censusStatus": str(plan.get("censusStatus") or ""),
        "capabilityStrategy": str(plan.get("capabilityStrategy") or ""),
        "action": str(plan.get("action") or ""),
        "allowedProfiles": [str(value) for value in plan.get("allowedProfiles") or [] if str(value)],
        "historicalStrategyProfile": str(plan.get("historicalStrategyProfile") or ""),
        "historicalStrategyCase": str(plan.get("historicalStrategyCase") or ""),
        # These fields are executable planner intent, not presentation metadata.
        # Dropping them makes the runtime recompute the final g5 family and
        # silently prevents post-exhaustion strategies from materializing.
        "postExhaustionStrategyProfile": str(plan.get("postExhaustionStrategyProfile") or ""),
        "postExhaustionStrategyMethod": str(plan.get("postExhaustionStrategyMethod") or ""),
        "repairType": str(plan.get("repairType") or ""),
        "learningDisposition": str(plan.get("learningDisposition") or ""),
        "experimentGenerationLimit": max(0, int(plan.get("experimentGenerationLimit") or 0)),
        "strategyEscalated": plan.get("strategyEscalated") is True,
        "baseExperimentExhausted": plan.get("baseExperimentExhausted") is True,
        "hypotheses": copy.deepcopy([row for row in plan.get("hypotheses") or [] if isinstance(row, dict)]),
    }


def wrap_create_repair_candidate(base_create: Callable[..., tuple[dict[str, Any] | None, str | None]]) -> Callable[..., tuple[dict[str, Any] | None, str | None]]:
    """Enforce strict production budgets while keeping Learning time-budgeted.

    Production remains bounded by mutation/size/time limits. Learning ignores
    those per-provider production limits and instead follows the global sandbox
    deadline, while duplicate/repeated experiments are still suppressed by
    cross-day negative memory.
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

        plan_snapshot = _plan_snapshot(plan)
        # Mutate only metadata on the in-memory sandbox parent so a failed
        # candidate generation still carries the exact causal plan that caused
        # the attempt. A later exploration replan must not rewrite this round's
        # historical attribution.
        candidate["brain_repair_plan"] = copy.deepcopy(plan_snapshot)
        candidate_for_create = copy.deepcopy(candidate)
        candidate_for_create["brain_repair_plan"] = copy.deepcopy(plan_snapshot)
        repaired, create_error = base_create(stage, candidate_for_create, profile_name, round_number)
        if not isinstance(repaired, dict):
            return repaired, create_error
        repaired["brain_repair_plan"] = copy.deepcopy(plan_snapshot)

        parent_bytes = max(0, int(candidate.get("bytes") or 0))
        repaired_bytes = max(0, int(repaired.get("bytes") or 0))
        generated_delta = max(0, repaired_bytes - parent_bytes)
        state["generatedBytes"] = int(state.get("generatedBytes") or 0) + generated_delta

        learning_mode = str(__import__("os").environ.get("NUVIO_BRAIN_PLANNER_MODE") or "").strip().casefold() == "learning"
        if not learning_mode:
            budget = _production_budget()
            if int(state["generatedBytes"]) > budget["maxGeneratedBytesPerProvider"]:
                _discard_generated_candidate(stage, repaired)
                return None, "brain_generated_code_budget_exhausted"
            if _public_state(candidate, plan_key)["elapsedMs"] > budget["maxElapsedMsPerProvider"]:
                _discard_generated_candidate(stage, repaired)
                return None, "brain_time_budget_exhausted"
        return repaired, create_error
    return _create


def annotate_and_learn(output_dir: Path, mode: str) -> dict[str, Any]:
    report_path = output_dir / "repair-report.json"
    report = _load_json(report_path, {})
    learning_mode = str(mode).casefold() == "learning"
    current_policy = policy()
    production = current_policy.get("production") if isinstance(current_policy.get("production"), dict) else {}
    learn_from_validated_repair = production.get("learningOnValidatedRepair") is True
    validated_repair_mode = str(mode).casefold() == "deep"
    record_skill_memory = learning_mode or (learn_from_validated_repair and validated_repair_mode)
    config = _load_json(OVERRIDES_PATH, {}) if record_skill_memory else {}
    runtime = config.setdefault("runtime_repair", {}) if record_skill_memory else {}
    skills = runtime.setdefault("learned_skills", {}) if record_skill_memory else {}
    if record_skill_memory and not isinstance(skills, dict):
        skills = {}
        runtime["learned_skills"] = skills
    maturity = current_policy.get("skillMaturity") or {}
    memory_policy = production.get("negativeExperimentMemory") if isinstance(production.get("negativeExperimentMemory"), dict) else {}
    memory = repair_memory()
    memory_entries = memory.setdefault("entries", [])
    max_memory_entries = max(1, int(memory_policy.get("maxEntries") or 1000))

    def memory_entry(plan: dict[str, Any], profile: str) -> dict[str, Any]:
        provider_id = str(plan.get("providerId") or "").strip().casefold()
        signature = str(plan.get("signature") or "").strip()
        failure_class = str(plan.get("failureClass") or "").strip()
        for row in memory_entries:
            if not isinstance(row, dict):
                continue
            if (
                str(row.get("providerId") or "").casefold() == provider_id
                and str(row.get("signature") or "") == signature
                and str(row.get("profile") or "") == profile
                and int(row.get("experimentVariant") or 0) == max(0, int(plan.get("experimentVariant") or 0))
                and max(1, int(row.get("experimentGeneration") or 1)) == max(1, int(plan.get("experimentGeneration") or 1))
            ):
                return row
        row = {
            "providerId": provider_id,
            "providerVersion": "*",
            "failureClass": failure_class,
            "signature": signature,
            "profile": profile,
            "experimentVariant": max(0, int(plan.get("experimentVariant") or 0)),
            "experimentGeneration": max(1, int(plan.get("experimentGeneration") or 1)),
            "capabilityStrategy": str(plan.get("capabilityStrategy") or "").casefold(),
            "observedPipelineStage": str(plan.get("observedPipelineStage") or "").casefold(),
            "failures": 0,
            "consecutiveFailures": 0,
            "successes": 0,
        }
        memory_entries.append(row)
        return row

    def event_plan(event: dict[str, Any], parent_key: str) -> dict[str, Any]:
        """Prefer immutable per-attempt causal metadata over mutable PLANS."""
        snapshot = event.get("brain_plan") if isinstance(event.get("brain_plan"), dict) else {}
        plan = copy.deepcopy(snapshot) if snapshot else copy.deepcopy(PLANS.get(parent_key) or {})
        if not plan.get("providerId"):
            fallback = PLANS.get(parent_key) or {}
            plan["providerId"] = str(fallback.get("providerId") or parent_key.split(":")[-1]).casefold()
        return plan

    accepted_count = 0
    negative_experiment_events = 0
    if record_skill_memory:
        for round_row in report.get("rounds") or []:
            attempts_by_parent: dict[str, list[dict[str, Any]]] = {}
            for attempt in round_row.get("attempts") or []:
                if isinstance(attempt, dict):
                    attempts_by_parent.setdefault(str(attempt.get("parent_key") or ""), []).append(attempt)
            for accepted in round_row.get("accepted") or []:
                if not isinstance(accepted, dict):
                    continue
                parent_key = str(accepted.get("parent_key") or "")
                plan = event_plan(accepted, parent_key)
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
                    "actions": [f"reproduce and evaluate validated {profile} strategy for {failure_class}"],
                    "capabilities": sorted({cap for hyp in plan.get("hypotheses") or [] for cap in hyp.get("capabilities") or []}),
                    "providers": [],
                    "signatures": [],
                    "capabilityStrategies": [],
                    "observedPipelineStages": [],
                    "successBySignature": {},
                    "failureBySignature": {},
                    "successCount": 0,
                    "failureCount": 0,
                    "validated": True,
                })
                providers = {str(value).casefold() for value in skill.get("providers") or [] if str(value)}
                if provider_id:
                    providers.add(provider_id)
                signature = str(plan.get("signature") or "").strip()
                strategy = str(plan.get("capabilityStrategy") or "").strip().casefold()
                observed_stage = str(plan.get("observedPipelineStage") or "").strip().casefold()
                signatures = {str(value) for value in skill.get("signatures") or [] if str(value)}
                strategies = {str(value).casefold() for value in skill.get("capabilityStrategies") or [] if str(value)}
                stages = {str(value).casefold() for value in skill.get("observedPipelineStages") or [] if str(value)}
                if signature:
                    signatures.add(signature)
                if strategy:
                    strategies.add(strategy)
                if observed_stage:
                    stages.add(observed_stage)
                skill["providers"] = sorted(providers)
                skill["signatures"] = sorted(signatures)
                skill["capabilityStrategies"] = sorted(strategies)
                skill["observedPipelineStages"] = sorted(stages)
                if signature:
                    per_signature = skill.setdefault("successBySignature", {})
                    if not isinstance(per_signature, dict):
                        per_signature = {}
                        skill["successBySignature"] = per_signature
                    per_signature[signature] = int(per_signature.get(signature) or 0) + 1
                skill["successCount"] = int(skill.get("successCount") or 0) + 1
                skill["lastValidatedMode"] = mode
                skill["lastValidatedProvider"] = provider_id or None
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
                skill["autoApply"] = False
                skill["proposalEligible"] = trusted
                if memory_policy.get("enabled") is True and profile:
                    mem = memory_entry(plan, profile)
                    mem["successes"] = int(mem.get("successes") or 0) + 1
                    mem["consecutiveFailures"] = 0
                    mem["lastOutcome"] = "accepted"
                accepted_count += 1

        # A planner-selected profile can also be structurally unavailable on
        # the current bytes: matching_profiles() then yields no attempt at all.
        # That is still a bounded failed experiment, not "no evidence". Record
        # the missing planned profile so the next wave rotates instead of
        # pinning Showbox/Yflix-style cases to variant 0 forever.
        if memory_policy.get("enabled") is True:
            attempted_profiles_by_parent: dict[str, set[str]] = {}
            for round_row in report.get("rounds") or []:
                for attempt in round_row.get("attempts") or []:
                    if not isinstance(attempt, dict):
                        continue
                    parent_key = str(attempt.get("parent_key") or "")
                    profile = str(attempt.get("profile") or "")
                    if parent_key and profile:
                        attempted_profiles_by_parent.setdefault(parent_key, set()).add(profile)
            for parent_key, plan in PLANS.items():
                if not isinstance(plan, dict):
                    continue
                if str(plan.get("action") or "") != "probe-targeted-repair":
                    continue
                attempted = attempted_profiles_by_parent.get(str(parent_key), set())
                for profile in {
                    str(value) for value in plan.get("allowedProfiles") or []
                    if str(value).strip()
                }:
                    if profile in attempted:
                        continue
                    mem = memory_entry(plan, profile)
                    mem["failures"] = int(mem.get("failures") or 0) + 1
                    mem["consecutiveFailures"] = int(mem.get("consecutiveFailures") or 0) + 1
                    mem["lastOutcome"] = "profile_unavailable"
                    mem["lastReason"] = "planned_profile_not_applicable_to_current_bytes"
                    negative_experiment_events += 1

        # Candidate-generation failures are real negative experiments too.
        # If matching selected a repair profile but create_repair_candidate()
        # could not produce executable bytes, record that bounded hypothesis as
        # failed so the next wave rotates instead of retrying variant 0 forever.
        for round_row in report.get("rounds") or []:
            for attempt in round_row.get("attempts") or []:
                if not isinstance(attempt, dict) or str(attempt.get("status") or "") != "not_generated":
                    continue
                parent_key = str(attempt.get("parent_key") or "")
                plan = event_plan(attempt, parent_key)
                profile = str(attempt.get("profile") or "")
                if memory_policy.get("enabled") is not True or not profile:
                    continue
                mem = memory_entry(plan, profile)
                mem["failures"] = int(mem.get("failures") or 0) + 1
                mem["consecutiveFailures"] = int(mem.get("consecutiveFailures") or 0) + 1
                mem["lastOutcome"] = "not_generated"
                mem["lastReason"] = _clip_text(attempt.get("reason"), 160)
                negative_experiment_events += 1

        # Sandbox progress is deliberately non-publishable. If a bounded Deep
        # invocation ends without any accepted repair for that provider, every
        # exploration strategy consumed on the path must still become durable
        # experiment memory. Otherwise the next outer wave restages published
        # bytes, forgets that the strategy already plateaued below the strict
        # playable gate, and regenerates the exact same candidate forever.
        #
        # Do not penalize exploration steps that led to an accepted repair in
        # this same invocation: those were useful causal stepping stones.
        accepted_parent_keys = {
            str(accepted.get("parent_key") or "")
            for round_row in report.get("rounds") or []
            for accepted in round_row.get("accepted") or []
            if isinstance(accepted, dict) and str(accepted.get("parent_key") or "")
        }
        if memory_policy.get("enabled") is True:
            for round_row in report.get("rounds") or []:
                for progress in round_row.get("exploration_progress") or []:
                    if not isinstance(progress, dict):
                        continue
                    parent_key = str(progress.get("parent_key") or "")
                    if not parent_key or parent_key in accepted_parent_keys:
                        continue
                    plan = event_plan(progress, parent_key)
                    profile = str(progress.get("profile") or "")
                    if not profile:
                        continue
                    mem = memory_entry(plan, profile)
                    mem["failures"] = int(mem.get("failures") or 0) + 1
                    mem["consecutiveFailures"] = int(mem.get("consecutiveFailures") or 0) + 1
                    mem["progresses"] = int(mem.get("progresses") or 0) + 1
                    mem["lastOutcome"] = "exploration_progress_nonpublishable"
                    mem["lastReason"] = _clip_text(progress.get("reason"), 160)
                    negative_experiment_events += 1

        for round_row in report.get("rounds") or []:
            for rejected in round_row.get("rejected") or []:
                if not isinstance(rejected, dict):
                    continue
                parent_key = str(rejected.get("parent_key") or "")
                plan = event_plan(rejected, parent_key)
                profile = str(rejected.get("profile") or "")
                if not profile:
                    repair_key = str(rejected.get("repair_key") or "")
                    candidates = [
                        row for row in round_row.get("attempts") or []
                        if isinstance(row, dict)
                        and str(row.get("parent_key") or "") == parent_key
                        and str(row.get("profile") or "")
                        and (not repair_key or str(row.get("repair_key") or "") == repair_key)
                    ]
                    if candidates:
                        profile = str(candidates[0].get("profile") or "")
                failure_class = str(plan.get("failureClass") or "")
                if memory_policy.get("enabled") is True and profile:
                    mem = memory_entry(plan, profile)
                    mem["failures"] = int(mem.get("failures") or 0) + 1
                    mem["consecutiveFailures"] = int(mem.get("consecutiveFailures") or 0) + 1
                    mem["lastOutcome"] = "rejected"
                    mem["lastReason"] = _clip_text(rejected.get("reason"), 160)
                    negative_experiment_events += 1
                skill_id = f"{failure_class}:{profile}"
                skill = skills.get(skill_id)
                if not isinstance(skill, dict) or not profile:
                    continue
                skill["failureCount"] = int(skill.get("failureCount") or 0) + 1
                signature = str(plan.get("signature") or "").strip()
                if signature:
                    per_signature = skill.setdefault("failureBySignature", {})
                    if not isinstance(per_signature, dict):
                        per_signature = {}
                        skill["failureBySignature"] = per_signature
                    per_signature[signature] = int(per_signature.get(signature) or 0) + 1
                successes = int(skill.get("successCount") or 0)
                failures = int(skill["failureCount"])
                skill["confidence"] = round(successes / max(1, successes + failures), 4)
                if skill["confidence"] < float(maturity.get("minimumConfidence") or 0.8):
                    skill["autoApply"] = False
                    if skill.get("maturity") == "trusted":
                        skill["maturity"] = "candidate"

    brain_versions = [int(row.get("brainVersion") or 0) for row in PLANS.values() if isinstance(row, dict)]
    if record_skill_memory:
        runtime["brain"] = {
            "name": str((policy().get("identity") or {}).get("name") or "NiakVIO Brain"),
            "controlPlaneVersion": max(brain_versions, default=0),
            "learningOnValidatedRepair": learn_from_validated_repair,
            "lastMode": mode,
            "fallbackPolicy": "lkg_only_after_repair_budget",
            "coreMutationPolicy": "proposal_only",
        }
        _write_json(OVERRIDES_PATH, config)
        if memory_policy.get("enabled") is True:
            memory["schemaVersion"] = 1
            memory["entries"] = sorted(
                [row for row in memory_entries if isinstance(row, dict)],
                key=lambda row: (
                    -int(row.get("consecutiveFailures") or 0),
                    -int(row.get("failures") or 0),
                    str(row.get("providerId") or ""),
                    str(row.get("signature") or ""),
                    str(row.get("profile") or ""),
                    int(row.get("experimentVariant") or 0),
                    max(1, int(row.get("experimentGeneration") or 1)),
                ),
            )[:max_memory_entries]
            REPAIR_MEMORY_PATH.parent.mkdir(parents=True, exist_ok=True)
            _write_json(REPAIR_MEMORY_PATH, memory)

    sanitized_plans = {
        key: {
            "providerId": row.get("providerId"), "failureClass": row.get("failureClass"),
            "brainVersion": row.get("brainVersion"),
            "signature": row.get("signature"), "action": row.get("action"),
            "exitReason": row.get("exitReason"),
            "repairScope": row.get("repairScope"),
            "repairType": row.get("repairType"),
            "learningDisposition": row.get("learningDisposition"),
            "experimentVariant": row.get("experimentVariant"),
            "experimentGeneration": row.get("experimentGeneration"),
            "experimentVariantCount": row.get("experimentVariantCount"),
            "experimentExhausted": row.get("experimentExhausted") is True,
            "negativeMemoryMatches": row.get("negativeMemoryMatches"),
            "censusStatus": row.get("censusStatus"),
            "censusPriorApplied": row.get("censusPriorApplied"),
            "hypotheses": [
                {
                    "id": hyp.get("id"),
                    "profile": hyp.get("profile"),
                    "learned": hyp.get("learned") is True,
                    "maturity": hyp.get("maturity"),
                    "transferScore": hyp.get("transferScore"),
                    "confidence": hyp.get("confidence"),
                }
                for hyp in row.get("hypotheses") or []
                if isinstance(hyp, dict)
            ],
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
        "learnedEvents": accepted_count if record_skill_memory else 0,
        "negativeExperimentEvents": negative_experiment_events if record_skill_memory else 0,
        "learningExecuted": learning_mode,
        "validatedRepairLearningExecuted": bool(record_skill_memory and not learning_mode),
        "learningLane": "independent_daily_lab" if learning_mode else ("validated_repair_skill_memory" if record_skill_memory else "none"),
        "queuedForLearning": sorted({
            str(row.get("providerId") or key)
            for key, row in PLANS.items()
            if isinstance(row, dict) and str(row.get("repairScope") or "") in {"learning", "deferred"}
        }),
        "privacy": "sanitized-no-raw-endpoints-tokens-header-values-private-notes",
    }
    _write_json(report_path, report)
    return report["brain"]
