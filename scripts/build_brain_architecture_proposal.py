#!/usr/bin/env python3
"""Build a review-only Brain self-architecture proposal from Learning evidence."""
from __future__ import annotations

import argparse
import copy
import json
import re
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected object")
    return value


def load_optional(path: Path | None) -> dict[str, Any]:
    if path is None or not path.is_file():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def safe(value: Any, limit: int = 300) -> str:
    text = re.sub(r"https?://\S+", "<url>", str(value or ""))
    text = re.sub(r"(?i)(token|authorization|cookie|secret)\s*[:=]\s*\S+", r"\1=<redacted>", text)
    return " ".join(text.split())[:limit]


def get_path(root: dict[str, Any], dotted: str, default: Any = None) -> Any:
    current: Any = root
    for part in dotted.split("."):
        if not isinstance(current, dict) or part not in current:
            return default
        current = current[part]
    return current


def set_path(root: dict[str, Any], dotted: str, value: Any) -> None:
    current = root
    parts = dotted.split(".")
    for part in parts[:-1]:
        child = current.get(part)
        if not isinstance(child, dict):
            child = {}
            current[part] = child
        current = child
    current[parts[-1]] = value


def allowed_target(target: str, allowed: list[str]) -> bool:
    return target in allowed or any(
        target.startswith(prefix.rstrip("*"))
        for prefix in allowed
        if prefix.endswith("*")
    )


def route_evidence_count(value: Any) -> int:
    if isinstance(value, list):
        return sum(route_evidence_count(item) for item in value)
    if not isinstance(value, dict):
        return 0
    count = 0
    for key, child in value.items():
        lowered = str(key).casefold()
        if lowered in {
            "official_site", "site_final_url", "validated_api",
            "terminal_url", "resolved_domain",
        } and child:
            count += 1
        elif lowered in {"site_candidates", "api_candidates", "terminal_candidates"} and isinstance(child, list):
            count += len(child)
        if isinstance(child, (dict, list)):
            count += route_evidence_count(child)
    return count


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--learning-state", type=Path, required=True)
    p.add_argument("--policy", type=Path, required=True)
    p.add_argument("--self-config", type=Path, required=True)
    p.add_argument("--workflow", type=Path, required=True)
    p.add_argument("--targeted-lab", type=Path)
    p.add_argument("--target-selection", type=Path)
    p.add_argument("--route-report", type=Path)
    p.add_argument("--route-fallback", type=Path)
    p.add_argument("--queue-summary", type=Path)
    p.add_argument("--queue-state", type=Path)
    p.add_argument("--output-policy", type=Path, required=True)
    p.add_argument("--summary", type=Path, required=True)
    p.add_argument("--markdown", type=Path, required=True)
    a = p.parse_args()

    state = load_json(a.learning_state)
    policy = load_json(a.policy)
    self_config = load_json(a.self_config)
    targeted = load_optional(a.targeted_lab)
    targeted_rows = (
        [row for row in targeted.get("providers") or [] if isinstance(row, dict)]
        if isinstance(targeted.get("providers"), list)
        else ([targeted] if targeted else [])
    )
    queue_summary = load_optional(a.queue_summary)
    queue_state = load_optional(a.queue_state)
    selection = queue_summary or load_optional(a.target_selection)
    route_report = load_optional(a.route_report)
    route_fallback = load_optional(a.route_fallback)
    workflow = a.workflow.read_text(encoding="utf-8")

    proposed = copy.deepcopy(policy)
    lab = proposed.setdefault("learningLab", {})
    if not isinstance(lab, dict):
        raise ValueError("learningLab must be object")

    allowed = [str(x) for x in lab.get("selfArchitectureAllowedTargets") or [] if str(x)]
    patch_allow = self_config.get("autoPatchAllowlist") if isinstance(self_config.get("autoPatchAllowlist"), dict) else {}
    thresholds = self_config.get("thresholds") if isinstance(self_config.get("thresholds"), dict) else {}

    proposals: list[dict[str, Any]] = []
    changes: list[dict[str, Any]] = []

    def add(kind: str, reason: str, targets: list[str], recommendation: str, priority: str = "high", evidence: dict[str, Any] | None = None) -> None:
        proposals.append({
            "type": "brain_architecture_evolution",
            "evolutionKind": kind,
            "priority": priority,
            "reason": safe(reason),
            "targets": [x for x in targets if allowed_target(x, allowed)],
            "recommendation": safe(recommendation, 800),
            "evidence": evidence or {},
            "requiresHumanMerge": True,
            "productionWritesAllowed": False,
            "publicationAllowed": False,
        })

    def patch_number(dotted: str, next_value: int, reason: str) -> None:
        current = int(get_path(proposed, dotted, 0) or 0)
        rule = patch_allow.get(dotted) if isinstance(patch_allow.get(dotted), dict) else {}
        maximum = int(rule.get("max") or next_value)
        minimum = int(rule.get("min") or 0)
        bounded = max(minimum, min(maximum, int(next_value)))
        if bounded <= current:
            return
        set_path(proposed, dotted, bounded)
        changes.append({
            "path": "engine_v2/config/brain-policy.json",
            "field": dotted,
            "from": current,
            "to": bounded,
            "reason": safe(reason, 500),
        })

    unresolved = state.get("unresolvedFailureCounts") if isinstance(state.get("unresolvedFailureCounts"), dict) else {}
    unknown = int(unresolved.get("unknown_failure") or 0)
    source_proposals = state.get("proposals") if isinstance(state.get("proposals"), list) else []

    if unknown >= int(thresholds.get("repeatedUnknownFailures") or 2):
        add(
            "missing_repair_capability",
            f"{unknown} unresolved observations still have no causal classification.",
            ["engine_v2/src/repair-brain.mjs", "scripts/run_brain_learning_sandbox.py", "engine_v2/scripts/learning-lab.mjs", "tests/brain_*"],
            "Design a new or evolved repair/evidence capability instead of forcing an existing type to explain an unknown case.",
            evidence={"unknownFailureCount": unknown},
        )

    all_client_rows = [
        client
        for lab_row in targeted_rows
        for client in ((lab_row.get("clients") or {}).values() if isinstance(lab_row.get("clients"), dict) else [])
        if isinstance(client, dict)
    ]
    runtime_streams = max((int(row.get("runtimeStreams") or 0) for row in all_client_rows), default=0)
    probed_streams = max((int(row.get("probedStreams") or 0) for row in all_client_rows), default=0)
    complete = all(bool(row.get("probeCoverageComplete", True)) for row in all_client_rows) if all_client_rows else True
    current_cap = int(lab.get("allStreamsSafetyCap") or 40)
    if all_client_rows and not complete and probed_streams >= current_cap:
        rule = patch_allow.get("learningLab.allStreamsSafetyCap") if isinstance(patch_allow.get("learningLab.allStreamsSafetyCap"), dict) else {}
        step = max(1, int(rule.get("step") or 20))
        patch_number(
            "learningLab.allStreamsSafetyCap",
            current_cap + step,
            "The independent Lab reached its own stream safety cap before covering every returned stream.",
        )
        add(
            "lab_self_limit",
            "The Learning Lab was unable to inspect every returned stream because its own safety cap was reached.",
            ["scripts/nuvio_client_lab.cjs", "engine_v2/config/brain-policy.json", "tests/brain_*"],
            "Increase the bounded Lab cap in review-only policy, then re-run the same provider/work before changing provider logic.",
            evidence={"runtimeStreams": runtime_streams, "probedStreams": probed_streams, "currentCap": current_cap},
        )

    queue_results = selection.get("results") if isinstance(selection.get("results"), list) else []
    blind_spots = []
    for row in queue_results:
        if not isinstance(row, dict):
            continue
        core_status = str((row.get("coreHypothesis") or {}).get("status") or "").strip().casefold()
        lab_status = str((row.get("finalLab") or {}).get("status") or "").strip().casefold()
        if core_status in {"healthy", "reachable"} and lab_status and lab_status != "playable":
            blind_spots.append({"provider": row.get("provider"), "coreStatus": core_status, "labStatus": lab_status})
    if blind_spots:
        add(
            "core_sampling_blind_spot",
            f"{len(blind_spots)} provider(s) looked healthy/reachable to Core but failed independent Learning Lab coverage.",
            ["scripts/nuvio_client_lab.cjs", "scripts/run_brain_learning_queue.py", "engine_v2/scripts/learning-lab.mjs", "tests/brain_*"],
            "Keep Core evidence non-authoritative and evolve Learning sampling/fixtures or causal classification before trusting the healthy sample.",
            evidence={"providers": blind_spots[:24]},
        )

    repeated = [
        row for row in source_proposals
        if isinstance(row, dict) and str(row.get("type") or "") in {
            "avoid_failed_profile", "native_reader_repeated_signature", "skill_candidate"
        }
    ]
    memory = state.get("experimentMemory") if isinstance(state.get("experimentMemory"), dict) else {}
    entries = [row for row in memory.get("entries") or [] if isinstance(row, dict)]
    target_provider = str(
        (targeted_rows[-1].get("providerId") if targeted_rows else "")
        or selection.get("provider")
        or ""
    ).strip().casefold()
    repeated_profiles = {
        str(row.get("profile") or "")
        for row in entries
        if str(row.get("providerId") or "").strip().casefold() == target_provider
        and int(row.get("successes") or 0) == 0
        and int(row.get("consecutiveFailures") or 0) >= int(thresholds.get("repeatedProfileFailures") or 2)
        and str(row.get("profile") or "")
    }
    if repeated_profiles:
        add(
            "method_exhaustion",
            f"{len(repeated_profiles)} repeatedly failing repair profile(s) show that known methods are not solving the provider.",
            ["scripts/run_brain_learning_sandbox.py", "engine_v2/src/repair-brain.mjs", "tests/brain_*"],
            "Propose a genuinely different repair/evidence capability or compose existing capabilities differently; do not widen an arbitrary retry counter.",
            evidence={"providerId": target_provider, "failedProfiles": sorted(repeated_profiles)},
        )
    elif len(repeated) >= 2:
        add(
            "method_exhaustion",
            f"{len(repeated)} repeated failed method/signature observations indicate the current toolbox may be too narrow.",
            ["scripts/run_brain_learning_sandbox.py", "engine_v2/src/repair-brain.mjs", "tests/brain_*"],
            "Propose a different method or capability type instead of repeating a known failed method.",
            evidence={"repeatedMethodSignals": len(repeated)},
        )

    route_blind_spots = []
    for row in queue_results:
        if not isinstance(row, dict):
            continue
        core_hypothesis = row.get("coreHypothesis") if isinstance(row.get("coreHypothesis"), dict) else {}
        route = row.get("routeSearch") if isinstance(row.get("routeSearch"), dict) else {}
        if core_hypothesis.get("needs_route_search") and int(route.get("routeEvidenceCount") or 0) < int(thresholds.get("routeDiscoveryEmptyEvidence") or 1):
            route_blind_spots.append(str(row.get("provider") or ""))
    if route_blind_spots:
        add(
            "route_discovery_blind_spot",
            f"{len(route_blind_spots)} access-failure provider(s) produced no usable route evidence with the current search chain.",
            ["scripts/resolve_provider_hubs.py", "scripts/resolve_provider_hub_search_fallback.py", "scripts/run_brain_learning_queue.py", "tests/brain_*"],
            "Evolve route discovery with a new evidence source or extraction method before mutating provider code.",
            evidence={"providers": route_blind_spots[:24]},
        )

    architecture_checks = {
        "coreEvidenceIsHypothesis": lab.get("coreEvidenceAuthority") == "hypothesis_only",
        "timeBudgetedProviderQueue": lab.get("targetProvidersPerRun") == "time_budgeted_queue",
        "deadlineDrivenRepair": "maxRepairRounds" not in lab and "deadline" in str(lab.get("retryPolicy") or ""),
        "multiDeviceLab": "tv_desktop_mobile" in str(lab.get("clientSelection") or ""),
        "allStreamsLab": "all_returned_streams" in str(lab.get("streamSampling") or "") or "--stream-safety-cap 40" in workflow,
        "persistentQueue": "run_brain_learning_queue.py" in workflow,
        "crossDayScheduler": "--learning-queue-state" in workflow,
        "conditionalRouteSearch": "run_brain_learning_queue.py" in workflow,
        "selfArchitecturePr": "publish-architecture-proposal:" in workflow,
    }
    missing = sorted(key for key, ok in architecture_checks.items() if not ok)
    if missing:
        add(
            "brain_contract_drift",
            "The current Brain implementation drifted away from its declared adaptive Learning contract.",
            [".github/workflows/brain-learning-lab.yml", "engine_v2/config/brain-policy.json", "scripts/run_brain_learning_sandbox.py", "tests/brain_*"],
            "Restore the missing contract before trusting further Learning conclusions.",
            priority="critical",
            evidence={"missingCapabilities": missing},
        )

    policy_changed = proposed != policy
    write_json(a.output_policy, proposed)
    summary = {
        "schemaVersion": 2,
        "proposalCount": len(proposals),
        "policyChanged": policy_changed,
        "policyChanges": changes,
        "proposals": proposals,
        "allowedTargets": allowed,
        "architectureChecks": architecture_checks,
        "targetProvider": target_provider or None,
        "providersObserved": int(selection.get("processedProviderCount") or 0),
        "pendingProviders": int(queue_state.get("remainingProviderCount") or 0),
        "policy": {
            "publicationAllowed": False,
            "productionWritesAllowed": False,
            "pullRequestOnly": True,
            "requiresFreshCi": True,
            "requiresHumanMerge": True,
        },
    }
    write_json(a.summary, summary)

    lines = [
        "# NiakVIO Brain architecture evolution",
        "",
        "Review-only self-evolution proposal generated from sanitized Learning evidence.",
        "",
        f"- Proposals: {len(proposals)}",
        f"- Policy changed: {str(policy_changed).lower()}",
        f"- Human merge required: true",
        "",
    ]
    for row in proposals:
        lines.extend([
            f"## {row.get('evolutionKind')}",
            "",
            f"Priority: {row.get('priority')}",
            "",
            str(row.get("reason") or ""),
            "",
            "Recommendation:",
            str(row.get("recommendation") or ""),
            "",
            "Targets: " + ", ".join(row.get("targets") or []),
            "",
        ])
    a.markdown.parent.mkdir(parents=True, exist_ok=True)
    a.markdown.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")

    print(
        f"FIELD_BRAIN_ARCHITECTURE_PROPOSAL proposals={len(proposals)} "
        f"policy_changed={str(policy_changed).lower()} target={target_provider or 'none'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
