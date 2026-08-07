#!/usr/bin/env python3
"""Prevent automated releases from silently shrinking the provider set.

The activation LKG is a *preservation* guard, not an instruction to override the
current strict publication gates. Historical providers therefore have two valid
outcomes in a deep publication:

* they stay enabled; or
* the same deep promotion report records an explicit, conclusive reason for
  disabling/removing them (for example P2P evidence or a failed strict quality
  gate).

CI-inconclusive results are deliberately not accepted as disablement proof. In
that case the promoter must preserve the last published active artifact, and
this validator continues to block any silent shrink.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "provider-activation-lkg.json"
MAIN = ROOT / "manifest.json"
VF = ROOT / "vf" / "manifest.json"
REPORT = ROOT / "health-report.json"

# These actions are emitted by promote_candidates.py only after current deep
# evidence made a deterministic decision. The inconclusive-disabled action is
# intentionally absent: an old active provider may not disappear merely because
# CI could not prove it during this run.
CONCLUSIVE_DISABLE_ACTIONS = {
    "published-disabled-failed-gates",
    "published-disabled-probation-or-performance",
    "disabled-sustained-outage",
}
P2P_REMOVAL_ACTION = "removed-disallowed-p2p"
INCONCLUSIVE_DISABLE_ACTION = "published-disabled-ci-inconclusive-no-valid-runtime-evidence"


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def rows(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(row.get("id") or "").casefold(): row
        for row in data.get("scrapers") or []
        if isinstance(row, dict) and str(row.get("id") or "").strip()
    }


def report_rows(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(row.get("id") or "").casefold(): row
        for row in data.get("providers") or []
        if isinstance(row, dict) and str(row.get("id") or "").strip()
    }


def conclusive_disablement(record: dict[str, Any] | None, *, missing: bool) -> tuple[bool, str]:
    """Return whether one deep report row explicitly justifies losing activation."""
    if not isinstance(record, dict):
        return False, "missing_deep_promotion_record"
    action = str(record.get("action") or "")
    failed = {str(value) for value in record.get("failed_gates") or [] if str(value)}
    enabled = record.get("enabled") is True

    if enabled:
        return False, "promotion_report_still_marks_provider_enabled"
    if action == INCONCLUSIVE_DISABLE_ACTION:
        return False, "ci_inconclusive_is_not_disablement_proof"
    if action == P2P_REMOVAL_ACTION:
        if "01_policy_safe_no_p2p" not in failed:
            return False, "p2p_removal_missing_policy_gate_evidence"
        return True, action
    if missing:
        # The complete catalogue publishes failed providers disabled. Absence is
        # allowed only for a hard policy exclusion such as P2P/torrent output.
        return False, f"missing_provider_not_justified_by_{action or 'unknown_action'}"
    if action in CONCLUSIVE_DISABLE_ACTIONS:
        if not failed and action != "disabled-sustained-outage":
            return False, "conclusive_disable_action_has_no_failed_gate"
        return True, action
    return False, f"non_conclusive_disable_action:{action or 'missing'}"


def validate() -> list[str]:
    policy = load(POLICY)
    main_rows = rows(load(MAIN))
    vf_rows = rows(load(VF))
    report = load(REPORT)
    report_by_id = report_rows(report)
    expected = {str(value).casefold() for value in policy.get("active_ids") or []}
    minimum = int(policy.get("minimum_enabled_count") or len(expected))
    active = {provider_id for provider_id, row in main_rows.items() if row.get("enabled") is True}

    errors: list[str] = []
    if str(report.get("test_mode") or "") != "deep":
        errors.append("activation preservation requires the current deep promotion report")

    justified: dict[str, str] = {}
    for provider_id in sorted(expected):
        manifest_row = main_rows.get(provider_id)
        is_missing = manifest_row is None
        if not is_missing and manifest_row.get("enabled") is True:
            continue
        accepted, reason = conclusive_disablement(report_by_id.get(provider_id), missing=is_missing)
        if accepted:
            justified[provider_id] = reason
            continue
        if is_missing:
            errors.append(f"activation LKG provider missing without conclusive proof: {provider_id} ({reason})")
        else:
            errors.append(f"activation LKG provider disabled without conclusive proof: {provider_id} ({reason})")

    # Preserve the original anti-shrink invariant, but count a historical member
    # as accounted for when this exact deep run conclusively disqualified it.
    # This catches silent mass disablement while allowing the strict gates to do
    # their job instead of forcing stale providers active forever.
    accounted_for = len(active) + len(justified)
    if accounted_for < minimum:
        errors.append(
            f"enabled-or-conclusively-disqualified provider count regressed: {accounted_for} < {minimum}"
        )

    mismatched = sorted(
        provider_id
        for provider_id in set(main_rows) & set(vf_rows)
        if bool(main_rows[provider_id].get("enabled")) != bool(vf_rows[provider_id].get("enabled"))
    )
    if mismatched:
        errors.append("main/VF activation mismatch: " + ", ".join(mismatched))

    return errors


def main() -> int:
    errors = validate()
    if errors:
        raise SystemExit("provider activation preservation failed:\n- " + "\n- ".join(errors))
    active_count = sum(1 for row in rows(load(MAIN)).values() if row.get("enabled") is True)
    print(f"provider activation preservation passed ({active_count} enabled; evidence-backed shrink guarded)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
