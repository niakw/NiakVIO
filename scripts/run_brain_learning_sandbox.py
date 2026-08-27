#!/usr/bin/env python3
"""Run the daily Brain learning sandbox.

Routine provider workflows stay conservative and reuse known, validated skills.
The Learning window is intentionally broader: it restores sanitized positive and
negative cross-day memory, rotates bounded exploratory profiles across the whole
catalogue, learns from accepted/rejected experiments, and never publishes directly.

After the bounded repair pass, Learning may run one lightweight targeted Nuvio
client-runtime Lab for a single provider. The fixture is chosen from the first
media type declared by that provider. Only a sanitized summary is attached to
the repair report and may enter persistent learning state.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
OVERRIDES = ROOT / "provider-overrides.json"
MANIFEST = ROOT / "manifest.json"
FIXTURES = ROOT / ".github" / "triggers" / "nuvio-client-lab.json"
sys.path.insert(0, str(SCRIPTS))

import run_adaptive_quick_repair as quick  # noqa: E402

FORBIDDEN_EXPLORATION_FAILURES = {
    "healthy",
    "identity_mismatch",
    "runtime_contract_drift",
    "playback_runtime_setup",
    "playback_player_error",
}


def _load_state() -> dict[str, Any]:
    raw = str(os.environ.get("NUVIO_BRAIN_LEARNING_STATE") or "").strip()
    if not raw:
        return {}
    path = Path(raw).resolve()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _negative_entries(state: dict[str, Any]) -> list[dict[str, Any]]:
    memory = state.get("experimentMemory") if isinstance(state.get("experimentMemory"), dict) else {}
    rows = memory.get("entries") if isinstance(memory.get("entries"), list) else []
    return [row for row in rows if isinstance(row, dict)]


def _norm(value: Any) -> str:
    return str(value or "").strip().casefold()


def _version(candidate: dict[str, Any]) -> str:
    metadata = candidate.get("metadata") if isinstance(candidate.get("metadata"), dict) else {}
    return str(metadata.get("version") or candidate.get("version") or "*").strip() or "*"


def _matches(row: dict[str, Any], *, provider_id: str, provider_version: str, signature: str, profile: str) -> bool:
    row_provider = _norm(row.get("providerId"))
    if row_provider != provider_id:
        return False
    row_version = str(row.get("providerVersion") or "*").strip() or "*"
    if row_version not in {"*", provider_version}:
        return False
    if str(row.get("signature") or "") != signature:
        return False
    if str(row.get("profile") or "") != profile:
        return False
    return int(row.get("successes") or 0) == 0


def _safe_text(value: Any, limit: int) -> str:
    text = re.sub(r"https?://\S+", "<url>", str(value or ""))
    text = re.sub(
        r"(?i)(token|authorization|cookie|secret)\s*[:=]\s*\S+",
        r"\1=<redacted>",
        text,
    )
    return " ".join(text.split())[:limit]


def _sanitize_skill(raw: Any) -> dict[str, Any] | None:
    if not isinstance(raw, dict):
        return None
    skill_id = _safe_text(raw.get("id"), 160)
    profile = _safe_text(raw.get("profile"), 96)
    failure_class = _safe_text(raw.get("failureClass") or raw.get("failure_class"), 96)
    if not skill_id or not profile or not failure_class or raw.get("validated") is not True:
        return None
    providers = sorted({
        _norm(value)[:128]
        for value in raw.get("providers") or []
        if _norm(value)
    })[:96]
    actions = [_safe_text(value, 240) for value in raw.get("actions") or [] if _safe_text(value, 240)][:12]
    capabilities = sorted({
        _safe_text(value, 64)
        for value in raw.get("capabilities") or []
        if _safe_text(value, 64)
    })[:24]
    success_count = max(0, int(raw.get("successCount") or 0))
    failure_count = max(0, int(raw.get("failureCount") or 0))
    confidence = float(raw.get("confidence") or 0.0)
    maturity = _safe_text(raw.get("maturity") or "experimental", 32)
    return {
        "id": skill_id,
        "failureClass": failure_class,
        "profile": profile,
        "actions": actions,
        "capabilities": capabilities,
        "providers": providers,
        "successCount": success_count,
        "failureCount": failure_count,
        "validated": True,
        "confidence": max(0.0, min(1.0, confidence)),
        "maturity": maturity if maturity in {"experimental", "candidate", "trusted"} else "experimental",
        "autoApply": bool(raw.get("autoApply")) and maturity == "trusted",
        "lastValidatedMode": _safe_text(raw.get("lastValidatedMode"), 32),
    }


def _restore_positive_skills(state: dict[str, Any]) -> int:
    raw_skills = state.get("learnedSkills")
    if not isinstance(raw_skills, dict) or not OVERRIDES.is_file():
        return 0
    config = json.loads(OVERRIDES.read_text(encoding="utf-8"))
    runtime = config.setdefault("runtime_repair", {})
    current = runtime.setdefault("learned_skills", {})
    if not isinstance(current, dict):
        current = {}
        runtime["learned_skills"] = current
    restored = 0
    rank = {"experimental": 0, "candidate": 1, "trusted": 2}
    for key, raw in raw_skills.items():
        incoming = _sanitize_skill(raw)
        if incoming is None:
            continue
        skill_key = str(key or incoming["id"]).strip()[:192]
        existing = _sanitize_skill(current.get(skill_key))
        if existing is None:
            current[skill_key] = incoming
            restored += 1
            continue
        merged = dict(existing)
        merged["providers"] = sorted(set(existing["providers"]) | set(incoming["providers"]))[:96]
        merged["successCount"] = max(existing["successCount"], incoming["successCount"])
        merged["failureCount"] = max(existing["failureCount"], incoming["failureCount"])
        merged["confidence"] = max(existing["confidence"], incoming["confidence"])
        if rank.get(incoming["maturity"], 0) > rank.get(existing["maturity"], 0):
            merged["maturity"] = incoming["maturity"]
        merged["autoApply"] = bool(
            merged["maturity"] == "trusted"
            and (existing.get("autoApply") or incoming.get("autoApply"))
        )
        if incoming.get("actions"):
            merged["actions"] = incoming["actions"]
        if incoming.get("capabilities"):
            merged["capabilities"] = incoming["capabilities"]
        current[skill_key] = merged
        restored += 1
    OVERRIDES.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return restored


def _exploration_gate(day: str, provider_id: str, signature: str, share: float) -> bool:
    if share <= 0:
        return False
    if share >= 1:
        return True
    token = f"{day}|{provider_id}|{signature}".encode("utf-8")
    bucket = int(hashlib.sha256(token).hexdigest()[:8], 16) / 0xFFFFFFFF
    return bucket < share


def _choose_exploratory_profiles(
    profiles: list[str],
    *,
    day: str,
    provider_id: str,
    signature: str,
    limit: int,
) -> list[str]:
    unique = sorted({str(value) for value in profiles if str(value)})
    ranked = sorted(
        unique,
        key=lambda value: hashlib.sha256(
            f"{day}|{provider_id}|{signature}|{value}".encode("utf-8")
        ).hexdigest(),
    )
    return ranked[:max(0, limit)]


def _arg_value(name: str, default: str = "") -> str:
    args = sys.argv[1:]
    try:
        index = args.index(name)
    except ValueError:
        return default
    if index + 1 >= len(args):
        return default
    return str(args[index + 1])


def _load_json_file(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _provider_from_parent_key(value: Any) -> str:
    raw = str(value or "").strip()
    if ":" in raw:
        return raw.split(":", 1)[1].split("::", 1)[0].strip()
    return raw.split("::", 1)[0].strip()


def _select_targeted_provider(repair: dict[str, Any], manifest: dict[str, Any]) -> dict[str, Any] | None:
    rows = [row for row in manifest.get("scrapers") or [] if isinstance(row, dict)]
    by_id: dict[str, dict[str, Any]] = {}
    for row in rows:
        for value in (row.get("id"), row.get("name")):
            if _norm(value):
                by_id[_norm(value)] = row

    forced = _norm(os.environ.get("NUVIO_BRAIN_TARGET_PROVIDER"))
    if forced:
        return by_id.get(forced)

    candidates: list[str] = []
    for round_row in repair.get("rounds") or []:
        if not isinstance(round_row, dict):
            continue
        for bucket in ("accepted", "rejected", "attempts"):
            for row in round_row.get(bucket) or []:
                if not isinstance(row, dict):
                    continue
                candidate = _provider_from_parent_key(row.get("parent_key"))
                if candidate:
                    candidates.append(candidate)
    plans = repair.get("brain", {}).get("plans", {}) if isinstance(repair.get("brain"), dict) else {}
    if isinstance(plans, dict):
        for row in plans.values():
            if isinstance(row, dict) and row.get("providerId"):
                candidates.append(str(row.get("providerId")))
    for candidate in candidates:
        match = by_id.get(_norm(candidate))
        if match is not None:
            return match
    return None


def _first_declared_type(provider: dict[str, Any]) -> str:
    raw = provider.get("supportedTypes") or []
    if isinstance(raw, str):
        raw = [raw]
    for value in raw if isinstance(raw, list) else []:
        normalized = _norm(value)
        if normalized in {"movie", "tv", "anime"}:
            return normalized
        if normalized in {"series", "show"}:
            return "tv"
    return "movie"


def _fixture_for_type(media_type: str) -> tuple[str, dict[str, Any]] | None:
    preferred = {
        "movie": "sinners-2025",
        "tv": "breaking-bad-s01e01",
        "anime": "jujutsu-kaisen-s01e01",
    }
    data = _load_json_file(FIXTURES)
    target = preferred.get(media_type, "sinners-2025")
    for row in data.get("fixtures") or []:
        if isinstance(row, dict) and str(row.get("slug") or "") == target and isinstance(row.get("fixture"), dict):
            return target, dict(row["fixture"])
    return None


def _run_targeted_client_lab() -> None:
    output_dir = Path(_arg_value("--output", str(ROOT / "health-output"))).resolve()
    repair_path = output_dir / "repair-report.json"
    repair = _load_json_file(repair_path)
    manifest = _load_json_file(MANIFEST)
    provider = _select_targeted_provider(repair, manifest)
    if provider is None:
        print("FIELD_BRAIN_TARGETED_LAB status=skipped reason=no_provider_target", file=sys.stderr)
        return

    media_type = _first_declared_type(provider)
    selected_fixture = _fixture_for_type(media_type)
    if selected_fixture is None:
        print("FIELD_BRAIN_TARGETED_LAB status=skipped reason=no_fixture", file=sys.stderr)
        return
    fixture_slug, fixture = selected_fixture
    provider_id = str(provider.get("id") or provider.get("name") or "").strip()
    clients_raw = str(os.environ.get("NUVIO_BRAIN_TARGET_CLIENTS") or "tv,desktop,mobile")
    clients = [value.strip().casefold() for value in clients_raw.split(",") if value.strip()]
    clients = [value for value in clients if value in {"tv", "desktop", "mobile"}] or ["tv", "desktop", "mobile"]

    config = {
        "providers": [provider_id],
        "fixture": fixture,
        "clients": clients,
        "manifest": "manifest.json",
        "provider_concurrency": 1,
        "provider_timeout_ms": 25000,
        "retry_provider_timeouts": False,
        "playback_timeout_ms": 8000,
        "max_streams_per_runtime": 1,
        "enforce_policy": False,
    }
    config_path = output_dir / "brain-targeted-lab-config.json"
    report_path = output_dir / "brain-targeted-lab.json"
    markdown_path = output_dir / "brain-targeted-lab.md"
    output_dir.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    status = "inconclusive"
    error = ""
    try:
        completed = subprocess.run(
            [
                "node",
                str(ROOT / "scripts" / "nuvio_client_lab.cjs"),
                "--config",
                str(config_path),
                "--out",
                str(report_path),
                "--markdown",
                str(markdown_path),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=90,
            check=False,
        )
        status = "completed" if report_path.is_file() else "inconclusive"
        if completed.returncode not in {0, 2}:
            error = _safe_text(completed.stderr or completed.stdout, 240)
    except (OSError, subprocess.TimeoutExpired) as exc:
        error = _safe_text(exc, 240)

    lab = _load_json_file(report_path)
    provider_report = next(
        (row for row in lab.get("providers") or [] if isinstance(row, dict)),
        {},
    )
    client_summary: dict[str, Any] = {}
    for client in clients:
        row = provider_report.get("clients", {}).get(client, {}) if isinstance(provider_report.get("clients"), dict) else {}
        if not isinstance(row, dict):
            row = {}
        client_summary[client] = {
            "verdict": _safe_text(row.get("verdict") or "unknown", 40),
            "identityStatus": _safe_text(row.get("identity_status") or "unknown", 40),
            "runtimeStreams": max(0, int(row.get("runtime_stream_count") or 0)),
            "playableProbes": max(0, int(row.get("playable_probe_count") or 0)),
        }
    policy = lab.get("policy") if isinstance(lab.get("policy"), dict) else {}
    repair["targetedLab"] = {
        "status": status,
        "providerId": _norm(provider_id),
        "firstDeclaredType": media_type,
        "fixtureSlug": fixture_slug,
        "clients": client_summary,
        "safetyStatus": _safe_text(policy.get("safety_status") or "unknown", 40),
        "error": error or None,
        "bounded": True,
        "maxProviders": 1,
        "maxStreamsPerRuntime": 1,
    }
    repair_path.write_text(json.dumps(repair, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        "FIELD_BRAIN_TARGETED_LAB "
        f"status={status} provider={_norm(provider_id)} first_type={media_type} fixture={fixture_slug} "
        f"clients={','.join(clients)}",
        file=sys.stderr,
    )


def main() -> int:
    state = _load_state()
    negative = _negative_entries(state)
    restored_skills = _restore_positive_skills(state)
    policy = quick.brain.policy()
    lab = policy.get("learningLab") if isinstance(policy.get("learningLab"), dict) else {}
    threshold = max(1, int(lab.get("maxRepeatedFailedProfile") or 2))
    exploration_share = max(0.0, min(1.0, float(lab.get("explorationShare") or 0.35)))
    exploration_limit = max(1, min(3, int(lab.get("maxExploratoryProfilesPerProvider") or 1)))
    day = datetime.now(timezone.utc).date().isoformat()
    routine_matcher = quick._brain_matching_profiles
    broad_matcher = quick._sibling_aware_matching_profiles
    counters = {"exploredProviders": 0, "exploratoryProfiles": 0, "suppressedProfiles": 0}

    def learning_matching(candidate: dict[str, Any], result: dict[str, Any], source_text: str, config: dict[str, Any] | None = None) -> list[str]:
        routine = list(routine_matcher(candidate, result, source_text, config))
        broad = list(broad_matcher(candidate, result, source_text, config))
        key = str(candidate.get("key") or "")
        parent_key = str((candidate.get("runtime_repair") or {}).get("parent_key") or "")
        plan_key = parent_key or key
        plan = quick.brain.PLANS.get(plan_key) or {}
        provider_id = _norm(plan.get("providerId") or candidate.get("canonical_id") or candidate.get("upstream_id"))
        provider_version = _version(candidate)
        signature = str(plan.get("signature") or plan.get("failureClass") or "unknown_failure")
        failure_class = str(plan.get("failureClass") or "unknown_failure")
        suppressed: set[str] = set()

        for profile in sorted(set(routine + broad)):
            failures = max(
                [int(row.get("consecutiveFailures") or row.get("failures") or 0) for row in negative if _matches(
                    row,
                    provider_id=provider_id,
                    provider_version=provider_version,
                    signature=signature,
                    profile=profile,
                )] or [0]
            )
            if failures >= threshold:
                suppressed.add(profile)

        kept = [profile for profile in routine if profile not in suppressed]
        if suppressed:
            counters["suppressedProfiles"] += len(suppressed)
            plan["suppressedProfiles"] = sorted(set([*(plan.get("suppressedProfiles") or []), *suppressed]))
            plan["negativeMemoryApplied"] = True

        exploratory_pool = [
            profile for profile in broad
            if profile not in set(routine) and profile not in suppressed
        ]
        can_explore = (
            failure_class not in FORBIDDEN_EXPLORATION_FAILURES
            and bool(exploratory_pool)
            and _exploration_gate(day, provider_id, signature, exploration_share)
        )
        if can_explore:
            chosen = _choose_exploratory_profiles(
                exploratory_pool,
                day=day,
                provider_id=provider_id,
                signature=signature,
                limit=exploration_limit,
            )
            if chosen:
                kept.extend(chosen)
                counters["exploredProviders"] += 1
                counters["exploratoryProfiles"] += len(chosen)
                plan["learningExplorationApplied"] = True
                plan["learningExploratoryProfiles"] = chosen
                plan["learningExplorationDay"] = day

        if routine and not kept:
            plan["action"] = "collect-more-evidence"
            plan["exitReason"] = "sandbox_repeated_failed_profile"
        return list(dict.fromkeys(kept))

    quick._brain_matching_profiles = learning_matching
    os.environ["NUVIO_BRAIN_PLANNER_MODE"] = "learning"
    print(
        "FIELD_BRAIN_LEARNING_MODE "
        f"negative_entries={len(negative)} restored_skills={restored_skills} "
        f"exploration_share={exploration_share:.2f} exploration_limit={exploration_limit} day={day}",
        file=sys.stderr,
    )
    try:
        rc = int(quick.main())
    finally:
        quick._brain_matching_profiles = routine_matcher
    print(
        "FIELD_BRAIN_EXPLORATION "
        f"providers={counters['exploredProviders']} profiles={counters['exploratoryProfiles']} "
        f"suppressed={counters['suppressedProfiles']}",
        file=sys.stderr,
    )
    if rc == 0:
        _run_targeted_client_lab()
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
