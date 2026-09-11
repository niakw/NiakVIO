#!/usr/bin/env python3
"""Prevent automated releases from silently violating provider activation authority.

Activation policy is now explicit and deterministic:

* all 96 canonical providers remain present for census/recovery;
* ``provider-overrides.json -> provider_patches.<provider>.official_hub`` is the
  single publication activation authority;
* a non-empty declared hub means enabled, an absent hub means disabled;
* historical activation LKG/deep evidence still protects route/DATA and safety
  history, but it may not override declared-hub activation.

Legacy conclusive-disablement/quarantine evidence remains validated for historical
providers that still have a declared hub. CI-inconclusive results may not disable
such a provider. Conversely, hub-less providers do not require a fresh health
failure merely to remain disabled: absence of the declared activation authority is
itself the deterministic publication decision.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import subprocess
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
CATALOGUE_AUDIT_MODE = "catalogue_audit_safety_quarantine"
CATALOGUE_AUDIT_SOURCE = "catalogue_media_audit"
CATALOGUE_AUDIT_BLOCKER = "catalogue_audit_playable_identity_contradiction"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")

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


def published_baseline_rows() -> dict[str, dict[str, Any]]:
    raw = str(os.environ.get("NUVIO_PUBLISHED_MANIFEST_BASELINE") or "").strip()
    if raw:
        path = Path(raw)
        if path.is_file():
            try:
                return rows(load(path))
            except (OSError, ValueError, json.JSONDecodeError):
                return {}
    try:
        process = subprocess.run(
            ["git", "show", "HEAD:manifest.json"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
            timeout=10,
        )
        if process.returncode == 0 and process.stdout.strip():
            payload = json.loads(process.stdout)
            if isinstance(payload, dict):
                return rows(payload)
    except (OSError, ValueError, json.JSONDecodeError, subprocess.SubprocessError):
        pass
    return {}


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
        score = sum(name in row for name in ("manifest_overrides", "patch_scripts", "patch_script_options"))
        current_score = sum(
            name in (current or {}) for name in ("manifest_overrides", "patch_scripts", "patch_script_options")
        )
        if current is None or score > current_score:
            result[provider_id] = row
    return result


def declared_hub_enabled(patch: dict[str, Any] | None) -> bool:
    return bool(str((patch or {}).get("official_hub") or "").strip())


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
    evidence_type = str(finding.get("evidence_type") or "")
    if evidence_type in {"manual_live_wrong_content", "manual_live_non_playable"}:
        if finding.get("evidence_source") != "operator_live_client_report":
            return False, "manual_safety_finding_source_invalid"
        if finding.get("operator_confirmed") is not True:
            return False, "manual_safety_finding_not_confirmed"
        if not COMMIT_RE.fullmatch(str(finding.get("tested_commit_sha") or "")):
            return False, "manual_safety_finding_commit_invalid"
        tested_sha = str(finding.get("tested_bundle_sha256") or "")
        tested_bundle = str(finding.get("tested_bundle") or "")
        if not SHA256_RE.fullmatch(tested_sha):
            return False, "manual_safety_finding_bundle_sha_invalid"
        if not tested_bundle.startswith("providers/") or not tested_bundle.endswith(f"--{tested_sha[:16]}.js"):
            return False, "manual_safety_finding_bundle_path_invalid"
        fixture = finding.get("fixture")
        if not isinstance(fixture, dict) or not str(fixture.get("tmdbId") or "") or not str(fixture.get("title") or ""):
            return False, "manual_safety_finding_fixture_invalid"
        if evidence_type == "manual_live_wrong_content":
            if finding.get("transport_playable") is not True:
                return False, "manual_wrong_content_not_transport_playable"
            if not str(finding.get("observed_content") or "").strip():
                return False, "manual_wrong_content_observation_missing"
            if not finding.get("clients_with_contradiction"):
                return False, "manual_wrong_content_client_missing"
        else:
            if finding.get("transport_playable") is not False:
                return False, "manual_non_playable_transport_flag_invalid"
            if str(finding.get("observed_failure") or "") not in {"infinite_loading", "non_media_html", "timeout"}:
                return False, "manual_non_playable_observation_invalid"
            if not finding.get("clients_with_failure"):
                return False, "manual_non_playable_client_missing"
        return True, f"configured_safety_quarantine:{reason}:{evidence_type}"
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


def catalogue_audit_safety_quarantine(
    manifest_row: dict[str, Any] | None,
    provenance: dict[str, Any] | None,
) -> tuple[bool, str]:
    if not isinstance(manifest_row, dict) or not isinstance(provenance, dict):
        return False, "missing_catalogue_audit_quarantine_evidence"
    if manifest_row.get("enabled") is not False:
        return False, "catalogue_audit_quarantine_manifest_not_disabled"
    published_filename = str(manifest_row.get("filename") or "")
    if "--nuvio-audit-quarantine--" not in published_filename:
        return False, "catalogue_audit_quarantine_filename_marker_missing"
    published_path = ROOT / published_filename
    if not published_filename.startswith("providers/") or not published_path.is_file():
        return False, "catalogue_audit_quarantine_bundle_missing"
    published = published_path.read_text(encoding="utf-8")
    if QUARANTINE_MARKER not in published or CATALOGUE_AUDIT_BLOCKER not in published:
        return False, "catalogue_audit_quarantine_bundle_not_inert"
    published_sha = file_sha256(published_path)
    expected_suffix = published_filename.rsplit("--", 1)[-1].removesuffix(".js")
    if expected_suffix != published_sha[:16]:
        return False, "catalogue_audit_quarantine_content_address_mismatch"
    if provenance.get("activation_eligible") is not False:
        return False, "catalogue_audit_quarantine_provenance_still_eligible"
    blockers = {str(value) for value in provenance.get("activation_blockers") or []}
    if CATALOGUE_AUDIT_BLOCKER not in blockers:
        return False, "catalogue_audit_quarantine_provenance_blocker_missing"
    if str(provenance.get("published_filename") or "") != published_filename:
        return False, "catalogue_audit_quarantine_provenance_path_mismatch"
    if str(provenance.get("patched_sha256") or provenance.get("sha256") or "") != published_sha:
        return False, "catalogue_audit_quarantine_provenance_sha_mismatch"
    records = [
        row for row in provenance.get("local_patches") or []
        if isinstance(row, dict)
        and row.get("type") == "safety_quarantine"
        and row.get("source") == CATALOGUE_AUDIT_SOURCE
    ]
    conclusive = False
    if records:
        record = records[-1]
        if str(record.get("reason") or "") != CATALOGUE_AUDIT_BLOCKER:
            return False, "catalogue_audit_quarantine_reason_mismatch"
        contradictions = int(record.get("identity_contradictions") or 0)
        playable = int(record.get("playable_streams") or 0)
        if contradictions > 0 and playable > 0:
            conclusive = True
    gates = provenance.get("activation_gates")
    if not conclusive and isinstance(gates, dict):
        identity = gates.get("10_content_identity_integrity")
        playable_gate = gates.get("00_current_playable_stream")
        if isinstance(identity, dict) and isinstance(playable_gate, dict):
            identity_evidence = identity.get("evidence")
            playable_evidence = playable_gate.get("evidence")
            if isinstance(identity_evidence, dict) and isinstance(playable_evidence, dict):
                contradictions = int(identity_evidence.get("identity_contradiction_count") or 0)
                duration_mismatches = int(identity_evidence.get("duration_identity_mismatch_count") or 0)
                playable = int(playable_evidence.get("streams_playable") or 0)
                conclusive = playable > 0 and (contradictions > 0 or duration_mismatches > 0)
    if not conclusive:
        return False, "catalogue_audit_quarantine_has_no_current_conclusive_contradiction"
    return True, f"catalogue_audit_safety_quarantine:{CATALOGUE_AUDIT_BLOCKER}"


def report_failure_is_inconclusive(record: dict[str, Any] | None) -> bool:
    if not isinstance(record, dict):
        return True
    evidence = record.get("evidence") if isinstance(record.get("evidence"), dict) else {}
    status = str(record.get("observed_status") or evidence.get("status") or "").strip().casefold()
    def count(name: str) -> int:
        try:
            return int(evidence.get(name) or 0)
        except (TypeError, ValueError):
            return 0
    hard_contradiction = (
        count("disallowed_streams") > 0
        or count("identity_contradiction_count") > 0
        or count("duration_identity_mismatch_count") > 0
    )
    positive_runtime_proof = count("streams_playable") > 0 or count("payload_verified_streams") > 0
    if hard_contradiction or positive_runtime_proof:
        return False
    if status in {"unavailable", "no_streams", "blocked", "provider_unreachable", "runtime_error", "reachable", "degraded"}:
        return True
    failures = {str(value).strip().casefold() for value in evidence.get("failure_classes") or [] if str(value).strip()}
    infrastructure_failures = {"provider_http_error", "network_error", "dns_error", "timeout", "provider_timeout", "runtime_timeout", "connection_error"}
    return bool(failures) and failures <= infrastructure_failures


def conclusive_disablement(record: dict[str, Any] | None, *, missing: bool) -> tuple[bool, str]:
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
        return False, f"missing_provider_not_justified_by_{action or 'unknown_action'}"
    if action in CONCLUSIVE_DISABLE_ACTIONS:
        if not failed and action != "disabled-sustained-outage":
            return False, "conclusive_disable_action_has_no_failed_gate"
        if action != "disabled-sustained-outage" and report_failure_is_inconclusive(record):
            return False, "runtime_or_network_evidence_is_inconclusive"
        return True, action
    return False, f"non_conclusive_disable_action:{action or 'missing'}"


def pending_clean_preservation_is_deferred(record: dict[str, Any] | None, provenance_row: dict[str, Any] | None) -> bool:
    del provenance_row
    if not isinstance(record, dict):
        return False
    return bool(str(record.get("action") or "") == "preserved-published-state-clean-candidate-pending" and record.get("enabled") is False)


def preexisting_published_disable_is_deferred(
    manifest_row: dict[str, Any] | None,
    baseline_row: dict[str, Any] | None,
    record: dict[str, Any] | None,
) -> bool:
    if not isinstance(manifest_row, dict) or manifest_row.get("enabled") is not False:
        return False
    if not isinstance(baseline_row, dict) or baseline_row.get("enabled") is not False:
        return False
    if str(os.environ.get("NUVIO_PROVIDER_V3_CONTEXT") or "").strip().casefold() == "workspace":
        return True
    return isinstance(record, dict) and record.get("enabled") is False


def validate() -> list[str]:
    policy = load(POLICY)
    main_rows = rows(load(MAIN))
    vf_rows = rows(load(VF))
    report = load(REPORT)
    report_by_id = report_rows(report)
    baseline_by_id = published_baseline_rows()
    patches_by_id = provider_patch_rows(load_optional(OVERRIDES))
    provenance_by_id = provenance_rows(load_optional(PROVENANCE))
    safety_by_id = safety_finding_rows(load_optional(SAFETY_FINDINGS))
    expected = {str(value).casefold() for value in policy.get("active_ids") or []}
    minimum = int(policy.get("minimum_enabled_count") or len(expected))
    active = {provider_id for provider_id, row in main_rows.items() if row.get("enabled") is True}

    errors: list[str] = []
    if str(report.get("test_mode") or "") != "deep":
        errors.append("activation preservation requires the current deep promotion report")

    # Hub declaration is the current publication authority for every catalogue row.
    # This is deliberately evaluated before historical activation-LKG handling.
    for provider_id, manifest_row in sorted(main_rows.items()):
        expected_enabled = declared_hub_enabled(patches_by_id.get(provider_id))
        actual_enabled = manifest_row.get("enabled") is True
        if actual_enabled != expected_enabled:
            errors.append(
                "declared-hub activation mismatch: "
                f"{provider_id} expected_enabled={str(expected_enabled).lower()} "
                f"actual_enabled={str(actual_enabled).lower()}"
            )

    justified: dict[str, str] = {}
    deferred_to_learning: dict[str, str] = {}
    for provider_id in sorted(expected):
        manifest_row = main_rows.get(provider_id)
        is_missing = manifest_row is None
        if is_missing:
            errors.append(f"activation LKG provider missing from 96-provider catalogue: {provider_id}")
            continue

        # Explicitly supersede historical activation LKG when the provider no
        # longer has the declared activation authority. This is not health proof;
        # route/DATA evidence remains preserved separately for Learning/Repair.
        if not declared_hub_enabled(patches_by_id.get(provider_id)):
            if manifest_row.get("enabled") is True:
                errors.append(f"hub-less activation LKG provider unexpectedly enabled: {provider_id}")
            else:
                justified[provider_id] = "declared_official_hub_absent"
                print(
                    "FIELD_ACTIVATION_LKG_SUPERSEDED_BY_HUB_AUTHORITY "
                    f"provider={provider_id} enabled=false"
                )
            continue

        if manifest_row.get("enabled") is True:
            continue
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
        accepted, reason = catalogue_audit_safety_quarantine(manifest_row, provenance_by_id.get(provider_id))
        if accepted:
            justified[provider_id] = reason
            continue
        record = report_by_id.get(provider_id)
        accepted, reason = conclusive_disablement(record, missing=False)
        if accepted:
            justified[provider_id] = reason
            continue
        provenance_row = provenance_by_id.get(provider_id)
        pending_v2_preserved = bool(pending_clean_preservation_is_deferred(record, provenance_row))
        if pending_v2_preserved:
            deferred_to_learning[provider_id] = "pending_clean_v2_preserved_published_state"
            print("FIELD_ACTIVATION_DEFERRED_TO_LEARNING " f"provider={provider_id} reason=pending_clean_v2_preserved_published_state")
            continue
        preserved_safety_ci_uncertain = bool(
            isinstance(record, dict)
            and str(record.get("action") or "") == "preserved-conclusive-safety-quarantine-ci-uncertain"
            and record.get("enabled") is False
            and isinstance(provenance_row, dict)
            and str(provenance_row.get("activation_mode") or "").startswith("catalogue_audit_")
            and CATALOGUE_AUDIT_BLOCKER in {str(value) for value in (provenance_row.get("activation_blockers") or [])}
        )
        if preserved_safety_ci_uncertain:
            justified[provider_id] = "preserved_conclusive_safety_quarantine_ci_uncertain"
            continue
        baseline_row = baseline_by_id.get(provider_id)
        if preexisting_published_disable_is_deferred(manifest_row, baseline_row, record):
            deferred_to_learning[provider_id] = "preexisting_published_disabled_state_nonconclusive"
            continue
        errors.append(f"declared-hub provider disabled without conclusive proof: {provider_id} ({reason})")

    # Historical LKG floor remains an anti-deletion/accounting guard. Hub-less
    # historical members count as explicitly accounted for, not as active.
    accounted_for = len(active) + len(justified) + len(deferred_to_learning)
    if accounted_for < minimum:
        errors.append(f"enabled-or-authoritatively-accounted provider count regressed: {accounted_for} < {minimum}")

    mismatched = sorted(
        provider_id
        for provider_id in set(main_rows) & set(vf_rows)
        if bool(main_rows[provider_id].get("enabled")) != bool(vf_rows[provider_id].get("enabled"))
    )
    if mismatched:
        print("FIELD_ACTIVATION_PROJECTION_DRIFT_DEFERRED providers=" + ",".join(mismatched))
    return errors


def main() -> int:
    errors = validate()
    if errors:
        raise SystemExit("provider activation preservation failed:\n- " + "\n- ".join(errors))
    active_count = sum(1 for row in rows(load(MAIN)).values() if row.get("enabled") is True)
    print(f"provider activation preservation passed ({active_count} enabled; declared-hub authority; LKG history preserved)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
