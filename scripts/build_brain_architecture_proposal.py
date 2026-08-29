#!/usr/bin/env python3
"""Build a review-only Brain self-architecture proposal from Learning evidence."""
from __future__ import annotations

import argparse
import copy
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected object")
    return value

def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def safe(value: Any, limit: int = 300) -> str:
    text = re.sub(r"https?://\S+", "<url>", str(value or ""))
    text = re.sub(r"(?i)(token|authorization|cookie|secret)\s*[:=]\s*\S+", r"\1=<redacted>", text)
    return " ".join(text.split())[:limit]

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--learning-state", type=Path, required=True)
    p.add_argument("--policy", type=Path, required=True)
    p.add_argument("--output-policy", type=Path, required=True)
    p.add_argument("--summary", type=Path, required=True)
    a = p.parse_args()

    state = load_json(a.learning_state)
    policy = load_json(a.policy)
    proposed = copy.deepcopy(policy)
    lab = proposed.setdefault("learningLab", {})
    if not isinstance(lab, dict):
        raise ValueError("learningLab must be object")

    allowed = [str(x) for x in lab.get("selfArchitectureAllowedTargets") or [] if str(x)]
    proposals: list[dict[str, Any]] = []
    changes: list[dict[str, Any]] = []

    unresolved = state.get("unresolvedFailureCounts") if isinstance(state.get("unresolvedFailureCounts"), dict) else {}
    unknown = int(unresolved.get("unknown_failure") or 0)
    source_proposals = state.get("proposals") if isinstance(state.get("proposals"), list) else []

    def add(kind: str, reason: str, targets: list[str], recommendation: str, priority: str = "high") -> None:
        proposals.append({
            "type": "brain_architecture_evolution",
            "evolutionKind": kind,
            "priority": priority,
            "reason": safe(reason),
            "targets": [x for x in targets if x in allowed or any(x.startswith(prefix.rstrip("*")) for prefix in allowed if prefix.endswith("*"))],
            "recommendation": safe(recommendation, 600),
            "requiresHumanMerge": True,
            "productionWritesAllowed": False,
        })

    if unknown >= 3 or any(str(x.get("type") or "") == "instrumentation_proposal" for x in source_proposals if isinstance(x, dict)):
        if lab.get("instrumentationEscalation") != "add_evidence_stage_before_new_mutation":
            lab["instrumentationEscalation"] = "add_evidence_stage_before_new_mutation"
            changes.append({"path": "engine_v2/config/brain-policy.json", "field": "learningLab.instrumentationEscalation"})
        add(
            "diagnostic_instrumentation_gap",
            f"{unknown} unresolved observation(s) still have no causal classification.",
            ["engine_v2/scripts/learning-lab.mjs", "scripts/run_brain_learning_sandbox.py", "tests/brain_*"],
            "Add or evolve evidence stages before adding more repair mutations; Learning may challenge Core classifications.",
        )

    targeted = ((state.get("nativeFeedback") or {}).get("targetedLab") or {}) if isinstance(state.get("nativeFeedback"), dict) else {}
    targeted_status = str(targeted.get("status") or "")
    if targeted_status in {"partial_failure", "unresolved", "no_report"}:
        if lab.get("hiddenFailureEscalation") != "rotate_fixture_device_and_stream_sampling":
            lab["hiddenFailureEscalation"] = "rotate_fixture_device_and_stream_sampling"
            changes.append({"path": "engine_v2/config/brain-policy.json", "field": "learningLab.hiddenFailureEscalation"})
        add(
            "hidden_playback_gap",
            f"Targeted Lab status={targeted_status}; Core evidence may have missed a playback/client-specific failure.",
            ["scripts/select_brain_targeted_probe.py", "scripts/run_brain_learning_sandbox.py", "engine_v2/scripts/learning-lab.mjs", "tests/brain_*"],
            "Rotate fixtures, clients and returned-stream positions before trusting a healthy Core sample.",
        )

    repeated = [
        x for x in source_proposals
        if isinstance(x, dict) and str(x.get("type") or "") in {"avoid_failed_profile", "native_reader_repeated_signature"}
    ]
    if len(repeated) >= 2:
        add(
            "method_exhaustion",
            f"{len(repeated)} repeated failed method/signature observation(s) indicate the current repair toolbox may be too narrow.",
            ["scripts/run_brain_learning_sandbox.py", "engine_v2/scripts/learning-lab.mjs", "tests/brain_*"],
            "Permit a new diagnostic/repair method proposal rather than repeating a known failed method.",
        )

    policy_changed = proposed != policy
    write_json(a.output_policy, proposed)
    summary = {
        "schemaVersion": 1,
        "proposalCount": len(proposals),
        "policyChanged": policy_changed,
        "policyChanges": changes,
        "proposals": proposals,
        "allowedTargets": allowed,
        "policy": {
            "publicationAllowed": False,
            "productionWritesAllowed": False,
            "pullRequestOnly": True,
            "requiresFreshCi": True,
            "requiresHumanMerge": True,
        },
    }
    write_json(a.summary, summary)
    print(f"FIELD_BRAIN_ARCHITECTURE_PROPOSAL proposals={len(proposals)} policy_changed={str(policy_changed).lower()}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
