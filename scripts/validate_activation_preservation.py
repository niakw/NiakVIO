#!/usr/bin/env python3
"""Prevent automated releases from silently shrinking the provider set.

The activation LKG is a *preservation* guard, not an instruction to override the
current strict publication gates. Historical providers therefore have two valid
outcomes in a deep publication:

* they stay enabled; or
* the same deep promotion report records an explicit, conclusive reason for
  disabling/removing them (for example P2P evidence or a failed strict quality
  gate); or
* an immutable client-lab finding records playable wrong-content evidence and
  the currently published artifact is a matching, inert safety quarantine.

CI-inconclusive results are deliberately not accepted as disablement proof. In
that case the promoter must preserve the last published active artifact, and
this validator continues to block any silent shrink.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "provider-activation-lkg.json"
MAIN = ROOT / "manifest.json"
VF = ROOT / "vf" / "manifest.json"
REPORT = ROOT / "health-report.json"
OVERRIDES = ROOT / "provider-overrides.json"
PROVENANCE = ROOT / "PROVENANCE.json"
SAFETY_FINDINGS = ROOT / "automation" / "nuvio-client-safety-findings.json"
QUARANTINE_PATCH = "scripts/provider_patches/quarantine_provider_v1.py"
QUARANTINE_MARKER = "NUVIO_PROVIDER_QUARANTINE_V1"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")

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


def load_optional(path: Path) -> dict[str, Any]:
    return load(path) if path.is_file() else {}


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


def provider_patch_rows(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    value = data.get("provider_patches") or {}
    if not isinstance(value, dict):
        return {}
    result: dict[str, dict[str, Any]] = {}
    for key, row in value.items():
        if not isinstance(row, dict):
            continue
        provider_id = str(key).casefold()
        current = result.get(provider_id)
        # Some upstream aliases differ only by case and carry only a capability
        # hint. Prefer the actionable patch record with publication controls.
        score = sum(name in row for name in ("manifest_overrides", "patch_scripts", "patch_script_options"))
        current_score = sum(
            name in (current or {}) for name in ("manifest_overrides", "patch_scripts", "patch_script_options")
        )
        if current is None or score > current_score:
            result[provider_id] = row
    return result


def provenance_rows(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    value = data.get("providers") or {}
    if not isinstance(value, dict):
        return {}
    return {str(key).casefold(): row for key, row in value.items() if isinstance(row, dict)}


def safety_finding_rows(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(row.get("provider_id") or "").casefold(): row
        for row in data.get("findings") or []
        if isinstance(row, dict) and str(row.get("provider_id") or "").strip()
    }


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def configured_safety_quarantine(
    provider_id: str,
    manifest_row: dict[str, Any] | None,
    patch: dict[str, Any] | None,
    provenance: dict[str, Any] | None,
    finding: dict[str, Any] | None,
) -> tuple[bool, str]:
    """Accept only complete, reproducible wrong-content quarantine evidence."""
    if not all(isinstance(value, dict) for value in (manifest_row, patch, provenance, finding)):
        return False, "missing_configured_safety_quarantine_evidence"
    assert manifest_row is not None and patch is not None and provenance is not None and finding is not None

    if manifest_row.get("enabled") is not False:
        return False, "safety_quarantine_manifest_not_disabled"
    if patch.get("capability") != "quarantined":
        return False, "safety_quarantine_capability_missing"
    overrides = patch.get("manifest_overrides") or {}
    if not isinstance(overrides, dict) or overrides.get("enabled") is not False:
        return False, "safety_quarantine_override_not_disabled"
    scripts = [str(value) for value in patch.get("patch_scripts") or []]
    if QUARANTINE_PATCH not in scripts:
        return False, "safety_quarantine_patch_missing"
    options = patch.get("patch_script_options") or {}
    quarantine_options = options.get(QUARANTINE_PATCH) if isinstance(options, dict) else None
    reason = str((quarantine_options or {}).get("reason") or "")
    if not reason or reason != str(finding.get("quarantine_reason") or ""):
        return False, "safety_quarantine_reason_mismatch"

    published_filename = str(manifest_row.get("filename") or "")
    published_path = ROOT / published_filename
    if not published_filename.startswith("providers/") or not published_path.is_file():
        return False, "safety_quarantine_bundle_missing"
    published = published_path.read_text(encoding="utf-8")
    if QUARANTINE_MARKER not in published or reason not in published:
        return False, "safety_quarantine_bundle_not_inert"
    published_sha = file_sha256(published_path)
    if published_sha != str(finding.get("quarantined_bundle_sha256") or ""):
        return False, "safety_quarantine_bundle_finding_sha_mismatch"
    if str(finding.get("quarantined_bundle") or "") != published_filename:
        return False, "safety_quarantine_bundle_finding_path_mismatch"

    if provenance.get("activation_mode") != "configured_safety_quarantine":
        return False, "safety_quarantine_provenance_mode_missing"
    if provenance.get("activation_eligible") is not False:
        return False, "safety_quarantine_provenance_still_eligible"
    blockers = {str(value) for value in provenance.get("activation_blockers") or []}
    if "configured_safety_quarantine" not in blockers:
        return False, "safety_quarantine_provenance_blocker_missing"
    if str(provenance.get("published_filename") or "") != published_filename:
        return False, "safety_quarantine_provenance_path_mismatch"
    if str(provenance.get("patched_sha256") or "") != published_sha:
        return False, "safety_quarantine_provenance_sha_mismatch"

    if finding.get("evidence_type") != "duration_identity_mismatch":
        return False, "unsupported_safety_finding_type"
    if finding.get("transport_playable") is not True:
        return False, "safety_finding_transport_not_playable"
    if not isinstance(finding.get("workflow_run_id"), int) or finding["workflow_run_id"] <= 0:
        return False, "safety_finding_workflow_run_missing"
    if not COMMIT_RE.fullmatch(str(finding.get("tested_commit_sha") or "")):
        return False, "safety_finding_commit_invalid"
    if not SHA256_RE.fullmatch(str(finding.get("tested_bundle_sha256") or "")):
        return False, "safety_finding_tested_bundle_sha_invalid"

    try:
        expected = float(finding["expected_duration_seconds"])
        measured = float(finding["measured_duration_seconds"])
        recorded_ratio = float(finding["duration_ratio"])
        minimum_ratio = float(finding["minimum_duration_ratio"])
        maximum_ratio = float(finding["maximum_duration_ratio"])
    except (KeyError, TypeError, ValueError):
        return False, "safety_finding_duration_invalid"
    ratio = measured / expected if expected > 0 and measured > 0 else math.nan
    if not math.isfinite(ratio) or not math.isclose(ratio, recorded_ratio, rel_tol=1e-9, abs_tol=1e-9):
        return False, "safety_finding_duration_ratio_invalid"
    if minimum_ratio <= ratio <= maximum_ratio:
        return False, "safety_finding_duration_not_contradictory"
    if not finding.get("clients_with_contradiction"):
        return False, "safety_finding_client_evidence_missing"
    return True, f"configured_safety_quarantine:{reason}"


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
    patches_by_id = provider_patch_rows(load_optional(OVERRIDES))
    provenance_by_id = provenance_rows(load_optional(PROVENANCE))
    safety_by_id = safety_finding_rows(load_optional(SAFETY_FINDINGS))
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
        if not is_missing:
            accepted, reason = configured_safety_quarantine(
                provider_id,
                manifest_row,
                patches_by_id.get(provider_id),
                provenance_by_id.get(provider_id),
                safety_by_id.get(provider_id),
            )
            if accepted:
                justified[provider_id] = reason
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
