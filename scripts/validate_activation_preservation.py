#!/usr/bin/env python3
"""Prevent automated releases from shrinking the canonical provider catalogue.

NIAKVIO_HUB46_ACTIVATION_AUTHORITY_V1

Publication activation and runtime route confidence are separate concerns:

* every canonical provider remains present and ``enabled=true`` in the catalogue;
* ``official_hub`` is discovery/address metadata only and never an ON/OFF switch;
* Repair/health evidence controls route/DATA state (on/repair/off), not catalogue
  visibility;
* quarantined, terminal or unresolved providers remain catalogued but must fail
  closed at runtime through their audited route/DATA disposition;
* historical activation LKG remains an anti-deletion/accounting source only.

Legacy safety/provenance helpers remain in this module because historical evidence
adapters import them, but they are not permitted to turn a canonical catalogue row
off.
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
HUB_MATRIX = ROOT / "automation" / "evidence" / "hub-lab-matrix-46.json"
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
    main_rows = rows(load(MAIN))
    vf_rows = rows(load(VF))
    patches_by_id = provider_patch_rows(load_optional(OVERRIDES))
    matrix = load(HUB_MATRIX)
    target = {
        str(row.get("manifestId") or "").strip().casefold().replace("_", "-")
        for row in matrix.get("rows") or []
        if isinstance(row, dict) and str(row.get("manifestId") or "").strip()
    }
    active = {
        provider_id
        for provider_id, row in main_rows.items()
        if row.get("enabled") is True
    }

    errors: list[str] = []
    if int(matrix.get("hubCount") or 0) != 46 or len(target) != 46:
        errors.append(f"hub activation authority must contain exactly 46 providers, got {len(target)}")
    if len(main_rows) != 96:
        errors.append(f"canonical catalogue must contain 96 providers, got {len(main_rows)}")

    missing = sorted(target - set(main_rows))
    extra = sorted(active - target)
    disabled_target = sorted(target - active)
    if missing:
        errors.append("46-hub target missing from canonical catalogue: " + ",".join(missing))
    if disabled_target:
        errors.append("46-hub target unexpectedly disabled: " + ",".join(disabled_target))
    if extra:
        errors.append("non-target provider unexpectedly enabled: " + ",".join(extra))
    if len(active) != 46:
        errors.append(f"enabled provider count must be exactly 46, got {len(active)}")

    for provider_id, patch in sorted(patches_by_id.items()):
        mo = patch.get("manifest_overrides") if isinstance(patch.get("manifest_overrides"), dict) else {}
        if "enabled" in mo and bool(mo.get("enabled")) != (provider_id in target):
            errors.append(f"override activation mismatch for hub46 authority: {provider_id}")

    mismatched = sorted(
        provider_id
        for provider_id in set(main_rows) & set(vf_rows)
        if bool(main_rows[provider_id].get("enabled"))
        != bool(vf_rows[provider_id].get("enabled"))
    )
    if mismatched:
        errors.append("hub46 activation projection mismatch: " + ",".join(mismatched))

    registry_only = sorted(
        provider_id
        for provider_id in active
        if not declared_hub_enabled(patches_by_id.get(provider_id))
    )
    if registry_only:
        print(
            "FIELD_ACTIVATION_HUB46_REGISTRY_ONLY "
            f"count={len(registry_only)} activation_authority=hub_lab_matrix_46"
        )

    return errors


def main() -> int:
    errors = validate()
    if errors:
        raise SystemExit("provider activation preservation failed:\n- " + "\n- ".join(errors))
    active_count = sum(1 for row in rows(load(MAIN)).values() if row.get("enabled") is True)
    print(f"provider activation preservation passed ({active_count} enabled; exact hub-matrix-46 authority)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
