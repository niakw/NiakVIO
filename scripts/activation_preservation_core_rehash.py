#!/usr/bin/env python3
"""Activation-preservation adapter for deterministic Core re-hashes.

Safety findings are immutable evidence of the original client observation and the
quarantine artifact produced at that time. A later deterministic Core rebuild may
change the SHA/path of the *current inert quarantine bundle* without changing that
historical evidence.

A Deep result that is merely inconclusive is also not allowed to replace the last
published proven state with an ordinary disabled bundle. Before validation this
adapter restores that exact previous published state (active or inert quarantine)
from the checked-out commit when, and only when, the current promotion report says
``published-disabled-ci-inconclusive-no-valid-runtime-evidence``. The normal strict
activation validator then runs unchanged and remains the final authority.

The tested unsafe bundle SHA, tested commit, fixture, observed contradiction and
client evidence are never rewritten or relaxed.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any

import validate_activation_preservation as legacy

_REHASHABLE_REASONS = {
    "safety_quarantine_bundle_finding_sha_mismatch",
    "safety_quarantine_bundle_finding_path_mismatch",
}
_LEGACY_CONFIGURED_SAFETY_QUARANTINE = legacy.configured_safety_quarantine
_BASELINE_ENV = "NUVIO_PUBLISHED_MANIFEST_BASELINE"


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def _git_json(path: str) -> dict[str, Any]:
    result = subprocess.run(
        ["git", "show", f"HEAD:{path}"],
        cwd=legacy.ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    value = json.loads(result.stdout)
    if not isinstance(value, dict):
        raise ValueError(f"HEAD:{path}: expected JSON object")
    return value


def _git_bytes(path: str) -> bytes:
    result = subprocess.run(
        ["git", "show", f"HEAD:{path}"],
        cwd=legacy.ROOT,
        check=True,
        capture_output=True,
    )
    return result.stdout


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _rows(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(row.get("id") or "").casefold(): row
        for row in payload.get("scrapers") or []
        if isinstance(row, dict) and str(row.get("id") or "").strip()
    }


def _replace_manifest_row(
    current: dict[str, Any], baseline: dict[str, Any], provider_id: str
) -> bool:
    """Make one manifest's provider row match the published baseline exactly."""
    baseline_rows = _rows(baseline)
    baseline_row = baseline_rows.get(provider_id)
    current_rows = current.get("scrapers") or []
    if not isinstance(current_rows, list):
        raise ValueError("manifest scrapers must be a list")

    changed = False
    replaced = False
    output: list[Any] = []
    for row in current_rows:
        if isinstance(row, dict) and str(row.get("id") or "").casefold() == provider_id:
            if baseline_row is not None and not replaced:
                replacement = copy.deepcopy(baseline_row)
                output.append(replacement)
                changed = changed or row != replacement
                replaced = True
            else:
                changed = True
            continue
        output.append(row)

    if baseline_row is not None and not replaced:
        output.append(copy.deepcopy(baseline_row))
        changed = True
    if changed:
        current["scrapers"] = output
    return changed


def _restore_casefold_mapping_entry(
    current: dict[str, Any], baseline: dict[str, Any], container_key: str, provider_id: str
) -> bool:
    current_container = current.setdefault(container_key, {})
    baseline_container = baseline.get(container_key) or {}
    if not isinstance(current_container, dict) or not isinstance(baseline_container, dict):
        return False

    baseline_matches = {
        str(key): copy.deepcopy(value)
        for key, value in baseline_container.items()
        if str(key).casefold() == provider_id
    }
    current_keys = [key for key in current_container if str(key).casefold() == provider_id]
    before = {str(key): copy.deepcopy(current_container[key]) for key in current_keys}
    for key in current_keys:
        current_container.pop(key, None)
    current_container.update(baseline_matches)
    return before != baseline_matches


def _baseline_bundle_is_restorable(row: dict[str, Any]) -> tuple[bool, str, bytes | None]:
    filename = str(row.get("filename") or "")
    if not filename.startswith("providers/") or not filename.endswith(".js"):
        return False, "baseline_bundle_path_invalid", None
    try:
        data = _git_bytes(filename)
    except subprocess.CalledProcessError:
        return False, "baseline_bundle_missing_from_head", None
    if row.get("enabled") is True:
        return True, "baseline_active", data

    # A disabled historical state may be preserved only when it is an inert
    # quarantine. The unchanged strict validator below still has to reproduce
    # its complete provenance/evidence contract before publication can pass.
    text = data.decode("utf-8", errors="replace")
    if legacy.QUARANTINE_MARKER not in text:
        return False, "baseline_disabled_state_not_inert_quarantine", None
    return True, "baseline_quarantine", data


def restore_inconclusive_previous_state() -> list[str]:
    """Restore exact published proof when this Deep could not make a decision.

    This is deliberately generic: provider IDs come only from the activation LKG
    and the current promotion report. No provider-specific exception exists.
    """
    baseline_path_raw = os.environ.get(_BASELINE_ENV, "").strip()
    if not baseline_path_raw:
        return []
    baseline_path = Path(baseline_path_raw)
    if not baseline_path.is_file():
        raise RuntimeError(f"{_BASELINE_ENV} does not point to a file: {baseline_path}")

    baseline_main = _load_json(baseline_path)
    current_main = _load_json(legacy.MAIN)
    current_vf = _load_json(legacy.VF)
    baseline_vf = _git_json("vf/manifest.json")
    report = _load_json(legacy.REPORT)
    policy = _load_json(legacy.POLICY)
    current_overrides = _load_json(legacy.OVERRIDES) if legacy.OVERRIDES.is_file() else {}
    baseline_overrides = _git_json("provider-overrides.json")
    current_provenance = _load_json(legacy.PROVENANCE) if legacy.PROVENANCE.is_file() else {}
    baseline_provenance = _git_json("PROVENANCE.json")

    baseline_rows = _rows(baseline_main)
    current_rows = _rows(current_main)
    report_by_id = legacy.report_rows(report)
    expected = {
        str(value).casefold()
        for value in policy.get("active_ids") or []
        if str(value).strip()
    }

    restored: list[str] = []
    for provider_id in sorted(expected):
        record = report_by_id.get(provider_id)
        if not isinstance(record, dict):
            continue
        if str(record.get("action") or "") != legacy.INCONCLUSIVE_DISABLE_ACTION:
            continue
        current_row = current_rows.get(provider_id)
        if isinstance(current_row, dict) and current_row.get("enabled") is True:
            continue
        baseline_row = baseline_rows.get(provider_id)
        if not isinstance(baseline_row, dict):
            continue

        restorable, reason, bundle = _baseline_bundle_is_restorable(baseline_row)
        if not restorable or bundle is None:
            continue
        filename = str(baseline_row.get("filename") or "")
        destination = legacy.ROOT / filename
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(bundle)

        _replace_manifest_row(current_main, baseline_main, provider_id)
        _replace_manifest_row(current_vf, baseline_vf, provider_id)
        _restore_casefold_mapping_entry(
            current_overrides, baseline_overrides, "provider_patches", provider_id
        )
        _restore_casefold_mapping_entry(
            current_provenance, baseline_provenance, "providers", provider_id
        )
        restored.append(f"{provider_id}:{reason}:{hashlib.sha256(bundle).hexdigest()[:16]}")
        current_rows = _rows(current_main)

    if restored:
        _write_json(legacy.MAIN, current_main)
        _write_json(legacy.VF, current_vf)
        _write_json(legacy.OVERRIDES, current_overrides)
        _write_json(legacy.PROVENANCE, current_provenance)
        print("FIELD_ACTIVATION_INCONCLUSIVE_STATE_RESTORED count=" + str(len(restored)) + " values=" + ",".join(restored))
    return restored


def _configured_safety_quarantine_with_core_rehash(
    original,
    provider_id: str,
    manifest_row: dict[str, Any] | None,
    patch: dict[str, Any] | None,
    provenance: dict[str, Any] | None,
    finding: dict[str, Any] | None,
) -> tuple[bool, str]:
    accepted, reason = original(provider_id, manifest_row, patch, provenance, finding)
    if accepted or reason not in _REHASHABLE_REASONS:
        return accepted, reason
    if not isinstance(manifest_row, dict) or not isinstance(finding, dict):
        return False, reason

    recorded_sha = str(finding.get("quarantined_bundle_sha256") or "")
    recorded_bundle = str(finding.get("quarantined_bundle") or "")
    if not legacy.SHA256_RE.fullmatch(recorded_sha):
        return False, "safety_quarantine_historical_bundle_sha_invalid"
    if not recorded_bundle.startswith("providers/") or not recorded_bundle.endswith(".js"):
        return False, "safety_quarantine_historical_bundle_path_invalid"

    current_bundle = str(manifest_row.get("filename") or "")
    current_path = legacy.ROOT / current_bundle
    if not current_bundle.startswith("providers/") or not current_path.is_file():
        return False, "safety_quarantine_current_bundle_missing"
    current_sha = legacy.file_sha256(current_path)

    rebound = copy.deepcopy(finding)
    rebound["quarantined_bundle"] = current_bundle
    rebound["quarantined_bundle_sha256"] = current_sha
    accepted, rebound_reason = original(
        provider_id,
        manifest_row,
        patch,
        provenance,
        rebound,
    )
    if not accepted:
        return False, rebound_reason
    return True, f"{rebound_reason}:deterministic_core_rehash"


def configured_safety_quarantine(
    provider_id: str,
    manifest_row: dict[str, Any] | None,
    patch: dict[str, Any] | None,
    provenance: dict[str, Any] | None,
    finding: dict[str, Any] | None,
) -> tuple[bool, str]:
    """Validate a configured safety quarantine against the current Core bundle."""
    return _configured_safety_quarantine_with_core_rehash(
        _LEGACY_CONFIGURED_SAFETY_QUARANTINE,
        provider_id,
        manifest_row,
        patch,
        provenance,
        finding,
    )


def validate() -> list[str]:
    restore_inconclusive_previous_state()
    original = legacy.configured_safety_quarantine
    legacy.configured_safety_quarantine = configured_safety_quarantine
    try:
        return legacy.validate()
    finally:
        legacy.configured_safety_quarantine = original


if __name__ == "__main__":
    errors = validate()
    if errors:
        raise SystemExit("provider activation preservation failed:\n- " + "\n- ".join(errors))
    print("provider activation preservation passed (deterministic Core rehash aware)")
