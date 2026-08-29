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
    p.add_argument("--output-policy", type=Path, required=True)
    p.add_argument("--summary", type=Path, required=True)
    p.add_argument("--markdown", type=Path, required=True)
    a = p.parse_args()

    state = load_json(a.learning_state)
    policy = load_json(a.policy)
    self_config = load_json(a.self_config)
    targeted = load_optional(a.targeted_lab)
    selection = load_optional(a.target_selection)
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

    client_rows = targeted.get("clients") if isinstance(targeted.get("clients"), dict) else {}
    runtime_streams = max((int(row.get("runtimeStreams") or 0) for row in client_rows.values() if isinstance(row, dict)), default=0)
    probed_streams = max((int(row.get("probedStreams") or 0) for row in client_rows.values() if isinstance(row, dict)), default=0)
    complete = all(bool(row.get("probeCoverageComplete", True)) for row in client_rows.values() if isinstance(row, dict)) if client_rows else True
    current_cap = int(lab.get("allStreamsSafetyCap") or 40)
    if client_rows and not complete and probed_streams >= current_cap:
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

    targeted_status = str(targeted.get("status") or "").strip().casefold()
    target_status = str(selection.get("status") or "").strip().casefold()
    if targeted_status == "partial_failure" and target_status in {"healthy", "reachable"}:
        add(
            "core_sampling_blind_spot",
            f"Core status={target_status} but the independent all-stream Learning Lab found partial playback failure.",
            ["scripts/nuvio_client_lab.cjs", "scripts/select_brain_learning_target.py", "engine_v2/scripts/learning-lab.mjs", "tests/brain_*"],
            "Keep Core evidence non-authoritative and evolve Learning sampling/fixtures or causal classification before trusting the healthy sample.",
            evidence={"coreStatus": target_status, "labStatus": targeted_status},
        )

    repeated = [
        row for row in source_proposals
        if isinstance(row, dict) and str(row.get("type") or "") in {
            "avoid_failed_profile", "native_reader_repeated_signature", "skill_candidate"
        }
    ]
    memory = state.get("experimentMemory") if isinstance(state.get("experimentMemory"), dict) else {}
    entries = [row for row in memory.get("entries") or [] if isinstance(row, dict)]
    target_provider = str(targeted.get("providerId") or selection.get("provider") or "").strip().casefold()
    repeated_profiles = {
        str(row.get("profile") or "")
        for row in entries
        if str(row.get("providerId") or "").strip().casefold() == target_provider
        and int(row.get("successes") or 0) == 0
        and int(row.get("consecutiveFailures") or 0) >= int(thresholds.get("repeatedProfileFailures") or 2)
        and str(row.get("profile") or "")
    }
    current_profiles = int(lab.get("maxExploratoryProfilesPerProvider") or 3)
    if len(repeated_profiles) >= current_profiles:
        rule = patch_allow.get("learningLab.maxExploratoryProfilesPerProvider") if isinstance(patch_allow.get("learningLab.maxExploratoryProfilesPerProvider"), dict) else {}
        step = max(1, int(rule.get("step") or 1))
        patch_number(
            "learningLab.maxExploratoryProfilesPerProvider",
            current_profiles + step,
            "The selected provider exhausted all currently available exploratory profiles without a successful method.",
        )
        add(
            "method_exhaustion",
            f"{len(repeated_profiles)} repeatedly failing repair profiles exhausted the current exploration width.",
            ["scripts/run_brain_learning_sandbox.py", "engine_v2/src/repair-brain.mjs", "engine_v2/config/brain-policy.json", "tests/brain_*"],
            "Allow one more bounded hypothesis family or define a new repair capability; do not start a second repair round in the same run.",
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

    if bool(selection.get("needs_route_search")):
        route_count = route_evidence_count(route_report) + route_evidence_count(route_fallback)
        if route_count < int(thresholds.get("routeDiscoveryEmptyEvidence") or 1):
            add(
                "route_discovery_blind_spot",
                "The selected provider has an access failure but the current hub/history/Telegram/Yandex/DDG chain produced no usable route evidence.",
                ["scripts/resolve_provider_hubs.py", "scripts/resolve_provider_hub_search_fallback.py", ".github/workflows/brain-learning-lab.yml", "tests/brain_*"],
                "Evolve route discovery with a new evidence source or extraction method before mutating provider code.",
                evidence={"providerId": target_provider, "routeEvidenceCount": route_count},
            )

    architecture_checks = {
        "coreEvidenceIsHypothesis": lab.get("coreEvidenceAuthority") == "hypothesis_only",
        "singleTargetProvider": lab.get("targetProvidersPerRun") == 1,
        "singleRepairRound": int(lab.get("maxRepairRounds") or 0) == 1,
        "oneClientLab": str(lab.get("clientSelection") or "").startswith("one_client"),
        "allStreamsLab": "--all-streams" in workflow,
        "targetedMutation": "NUVIO_BRAIN_TARGET_PROVIDER" in workflow,
        "conditionalRouteSearch": "needs_route_search" in workflow,
        "externalLabMemory": "--targeted-lab-summary" in workflow,
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
