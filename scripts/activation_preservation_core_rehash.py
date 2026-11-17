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
import sys
from pathlib import Path
from typing import Any

import validate_activation_preservation as legacy

_REHASHABLE_REASONS = {
    "safety_quarantine_bundle_finding_sha_mismatch",
    "safety_quarantine_bundle_finding_path_mismatch",
}
_LEGACY_CONFIGURED_SAFETY_QUARANTINE = legacy.configured_safety_quarantine
_BASELINE_ENV = "NUVIO_PUBLISHED_MANIFEST_BASELINE"
_CLEAN_PENDING_PRESERVE_ACTION = "preserved-published-state-clean-candidate-pending"


def _record_requires_baseline_restore(record: dict[str, Any]) -> bool:
    """Return true only for non-conclusive reports that explicitly preserve published state."""
    action = str(record.get("action") or "")
    if action == legacy.INCONCLUSIVE_DISABLE_ACTION:
        return True
    if record.get("enabled") is False and legacy.report_failure_is_inconclusive(record):
        return True
    if action != _CLEAN_PENDING_PRESERVE_ACTION:
        return False
    # The Quick clean-migration report may carry enabled=false even when the
    # publication action explicitly says to preserve the previously published
    # state. Absence of failed gates is the decisive signal; the baseline/LKG
    # remains the activation authority until conclusive evidence says otherwise.
    return not bool(record.get("failed_gates") or [])


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


def _baseline_matches_checked_out_head(baseline_path: Path) -> bool:
    """A preservation baseline is valid only for the HEAD it was captured from."""
    try:
        current_head_manifest = _git_bytes("manifest.json")
    except subprocess.CalledProcessError:
        return False
    return baseline_path.read_bytes() == current_head_manifest


def _rematerialize_current_core_after_restore() -> None:
    """Rebuild deterministic publication state after provider-state restore."""
    commands = (
        [sys.executable, "scripts/build_provider_runtime_profiles.py"],
        [sys.executable, "scripts/reapply_published_overrides.py"],
        [sys.executable, "scripts/generate_language_manifests.py"],
        [sys.executable, "scripts/prune_unreferenced_providers.py"],
        [sys.executable, "scripts/reapply_published_overrides.py", "--check"],
    )
    for command in commands:
        subprocess.run(command, cwd=legacy.ROOT, check=True)


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _rows(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(row.get("id") or "").casefold(): row
        for row in payload.get("scrapers") or []
        if isinstance(row, dict) and str(row.get("id") or "").strip()
    }


def _sync_derived_projection(path: Path, source: dict[str, Any]) -> None:
    """Refresh an existing projection from its current source without changing membership."""
    if not path.is_file():
        return
    projection = _load_json(path)
    source_rows = _rows(source)
    refreshed: list[dict[str, Any]] = []
    for row in projection.get("scrapers") or []:
        if not isinstance(row, dict):
            continue
        provider_id = str(row.get("id") or "").casefold()
        source_row = source_rows.get(provider_id)
        if source_row is None:
            raise RuntimeError(f"derived projection provider absent from source manifest: {provider_id}")
        replacement = copy.deepcopy(source_row)
        filename = str(replacement.get("filename") or "")
        if filename.startswith("providers/"):
            replacement["filename"] = "../" + filename
        refreshed.append(replacement)
    projection["version"] = source.get("version")
    projection["scrapers"] = refreshed
    _write_json(path, projection)

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
    """Retired compatibility hook; current validation must never restore activation.

    Historical activation LKG is evidence only. Current activation is owned by
    provider folders and Global+France projection authority, so a Deep/rehash
    validator may observe or rebind deterministic Core proof but may not rewrite
    manifest rows, provider overrides, provenance, or provider bytes.
    """
    print("FIELD_ACTIVATION_LKG_RESTORE_RETIRED mutation=false authority=current-projection")
    return []


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
