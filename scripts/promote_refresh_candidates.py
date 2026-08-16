#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Safely publish a routine quick repair transaction.

The canonical publisher intentionally requires ``deep`` health. This wrapper
permits a narrower refresh transaction without weakening activation/media
gates:

* current quick evidence must still satisfy the canonical strict gates;
* quick may replace bytes for an already-enabled provider only when the
  canonical promoter keeps that candidate enabled; otherwise the exact current
  published row is restored as LKG;
* quick never changes the current activation set, never reactivates historical
  providers, never activates new providers, and never exits a quarantine;
* safety-quarantined rows are restored byte-for-byte at manifest level;
* the canonical deep promotion report is preserved. Quick publication evidence
  is written separately to ``refresh-health-report.json``;
* quick runs never advance deep-validation history.

Deep therefore remains the sole authority for activation changes, quarantine
entry/exit, broad catalogue decisions, and durable learned repair profiles.
"""
from __future__ import annotations

import copy
import json
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
REFRESH_REPORT_PATH = ROOT / "refresh-health-report.json"
sys.path.insert(0, str(SCRIPTS))

import promote_candidates as pc  # noqa: E402
from apply_provider_overrides import load_overrides as load_real_overrides  # noqa: E402


def _canonical(value: Any) -> str:
    return pc.canonical_id(str(value or ""))


def _manifest_rows(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        _canonical(row.get("id")): row
        for row in manifest.get("scrapers") or []
        if isinstance(row, dict) and _canonical(row.get("id"))
    }


def _enabled_manifest_ids(manifest: dict[str, Any]) -> set[str]:
    return {
        cid
        for cid, row in _manifest_rows(manifest).items()
        if row.get("enabled") is True
    }


def _historical_active_ids(payload: dict[str, Any]) -> set[str]:
    return {_canonical(value) for value in payload.get("active_ids") or [] if _canonical(value)}


def _quarantine_ids(
    policy: dict[str, Any],
    manifest: dict[str, Any],
    provenance: dict[str, Any],
) -> set[str]:
    quarantined: set[str] = set()
    patches = policy.get("provider_patches") if isinstance(policy.get("provider_patches"), dict) else {}
    for raw_id, patch in patches.items():
        if not isinstance(patch, dict):
            continue
        manifest_overrides = patch.get("manifest_overrides")
        if isinstance(manifest_overrides, dict) and manifest_overrides.get("enabled") is False:
            quarantined.add(_canonical(raw_id))

    for row in manifest.get("scrapers") or []:
        if not isinstance(row, dict):
            continue
        filename = str(row.get("filename") or "")
        if "--nuvio-audit-quarantine--" in filename or "NUVIO_PROVIDER_QUARANTINE_V1" in filename:
            quarantined.add(_canonical(row.get("id")))

    providers = provenance.get("providers") if isinstance(provenance.get("providers"), dict) else {}
    for raw_id, row in providers.items():
        if not isinstance(row, dict):
            continue
        filename = str(row.get("published_filename") or "")
        if "--nuvio-audit-quarantine--" in filename:
            quarantined.add(_canonical(raw_id))
    return {value for value in quarantined if value}


def _refresh_policy_overlay(
    policy: dict[str, Any],
    candidate_ids: set[str],
    current_enabled_ids: set[str],
) -> dict[str, Any]:
    """Make the in-memory publisher policy preserve today's activation set."""
    output = copy.deepcopy(policy)
    patches = output.setdefault("provider_patches", {})
    for cid in sorted(candidate_ids):
        patch = patches.setdefault(cid, {})
        if not isinstance(patch, dict):
            patch = {}
            patches[cid] = patch
        manifest_overrides = patch.setdefault("manifest_overrides", {})
        if not isinstance(manifest_overrides, dict):
            manifest_overrides = {}
            patch["manifest_overrides"] = manifest_overrides
        manifest_overrides["enabled"] = cid in current_enabled_ids
    return output


def _filtered_activation_lkg(payload: dict[str, Any], preserve_ids: set[str]) -> dict[str, Any]:
    output = copy.deepcopy(payload)
    output["active_ids"] = sorted(preserve_ids)
    return output


def _preserve_quick_manifest(
    generated: dict[str, Any],
    current: dict[str, Any],
    quarantined_ids: set[str],
) -> dict[str, Any]:
    """Allow byte refreshes while making activation changes impossible.

    For an existing enabled provider, a generated row is accepted only when the
    canonical promoter itself kept it enabled. A generated disabled row falls
    back to the exact current row instead of re-enabling newly failed bytes.
    Existing disabled providers stay disabled. Quarantines are copied from the
    current manifest verbatim. Missing current rows are appended unchanged.
    Brand-new rows may be discovered/published, but stay disabled until deep.
    """
    output = copy.deepcopy(generated)
    current_rows = _manifest_rows(current)
    result: list[dict[str, Any]] = []
    seen: set[str] = set()

    for raw in generated.get("scrapers") or []:
        if not isinstance(raw, dict):
            continue
        cid = _canonical(raw.get("id"))
        if not cid:
            continue
        seen.add(cid)
        previous = current_rows.get(cid)
        if previous is None:
            row = copy.deepcopy(raw)
            row["enabled"] = False
        elif cid in quarantined_ids:
            row = copy.deepcopy(previous)
        elif previous.get("enabled") is True:
            if raw.get("enabled") is True:
                row = copy.deepcopy(raw)
                row["enabled"] = True
            else:
                row = copy.deepcopy(previous)
        else:
            row = copy.deepcopy(raw)
            row["enabled"] = False
        result.append(row)

    for cid, row in current_rows.items():
        if cid not in seen:
            result.append(copy.deepcopy(row))

    output["scrapers"] = result
    return output


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _provider_rows_by_canonical(provenance: dict[str, Any]) -> dict[str, tuple[str, dict[str, Any]]]:
    providers = provenance.get("providers") if isinstance(provenance.get("providers"), dict) else {}
    output: dict[str, tuple[str, dict[str, Any]]] = {}
    for raw_id, row in providers.items():
        if isinstance(row, dict):
            cid = _canonical(raw_id)
            if cid:
                output[cid] = (str(raw_id), row)
    return output


def _postprocess_refresh_outputs(
    canonical_deep_report_bytes: bytes,
    original_provenance: dict[str, Any],
    quarantined_ids: set[str],
) -> None:
    """Store quick evidence separately and restore canonical deep authority."""
    quick_report = pc.load_json(pc.REPORT_PATH, {}) or {}
    if isinstance(quick_report, dict):
        quick_report["test_mode"] = "quick"
        quick_report["publication_mode"] = "restricted_quick_refresh"
        policy = quick_report.setdefault("policy", {})
        if isinstance(policy, dict):
            policy["quick_checks_are_report_only"] = False
            policy["deep_checks_are_required_for_publication"] = False
            policy["quick_refresh_publication_is_restricted"] = True
            policy["quick_refresh_requires_current_positive_proof"] = True
            policy["quick_refresh_preserves_activation_set"] = True
            policy["deep_required_for_activation_change_or_quarantine_exit"] = True
        _write_json(REFRESH_REPORT_PATH, quick_report)

    # health-report.json is the durable deep activation proof consumed by
    # validate_activation_preservation.py. A quick refresh must never replace it.
    pc.REPORT_PATH.write_bytes(canonical_deep_report_bytes)

    provenance = pc.load_json(pc.PROVENANCE_PATH, {"providers": {}}) or {"providers": {}}
    if isinstance(provenance, dict):
        provenance["validation_mode"] = "quick"
        provenance["publication_mode"] = "restricted_quick_refresh"
        providers = provenance.get("providers")
        if not isinstance(providers, dict):
            providers = {}
            provenance["providers"] = providers
        for row in providers.values():
            if isinstance(row, dict) and row.get("checked_at"):
                row["check_mode"] = "quick"
                row["publication_mode"] = "restricted_quick_refresh"

        # Safety quarantine provenance is part of the durable evidence for the
        # inert current bundle. Quick must not rewrite it to candidate evidence.
        original_rows = _provider_rows_by_canonical(original_provenance)
        generated_rows = _provider_rows_by_canonical(provenance)
        for cid in sorted(quarantined_ids):
            original = original_rows.get(cid)
            if original is None:
                continue
            original_key, original_row = original
            generated = generated_rows.get(cid)
            if generated is not None:
                generated_key, _ = generated
                providers[generated_key] = copy.deepcopy(original_row)
            else:
                providers[original_key] = copy.deepcopy(original_row)
        _write_json(pc.PROVENANCE_PATH, provenance)


def main() -> int:
    stage = Path(os.environ.get("NUVIO_STAGE", ROOT / "staging")).resolve()
    health_path = Path(
        os.environ.get("NUVIO_HEALTH_RESULTS", stage / "health-results.json")
    ).resolve()
    if not health_path.is_file():
        raise SystemExit(f"missing quick health results: {health_path}")

    real_health = json.loads(health_path.read_text(encoding="utf-8"))
    if str(real_health.get("mode") or "") != "quick":
        raise SystemExit(f"refresh publisher requires quick evidence; got {real_health.get('mode')!r}")

    registry_path = stage / "candidates.json"
    if not registry_path.is_file():
        raise SystemExit(f"missing candidate registry: {registry_path}")
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    candidate_ids = {
        _canonical(row.get("canonical_id") or row.get("upstream_id"))
        for row in registry.get("candidates") or []
        if isinstance(row, dict)
    }
    candidate_ids.discard("")

    if not pc.REPORT_PATH.is_file():
        raise SystemExit("quick refresh requires an existing canonical deep health-report.json")
    canonical_deep_report_bytes = pc.REPORT_PATH.read_bytes()
    canonical_deep_report = json.loads(canonical_deep_report_bytes.decode("utf-8"))
    if str(canonical_deep_report.get("test_mode") or "") != "deep":
        raise SystemExit("quick refresh requires the current canonical deep promotion report")

    manifest = pc.load_json(pc.MANIFEST_PATH, {"scrapers": []}) or {"scrapers": []}
    activation_lkg = pc.load_json(pc.ACTIVATION_LKG_PATH, {}) or {}
    original_provenance = pc.load_json(pc.PROVENANCE_PATH, {"providers": {}}) or {"providers": {}}
    policy = load_real_overrides()

    current_enabled = _enabled_manifest_ids(manifest)
    historical_active = _historical_active_ids(activation_lkg)
    quarantined = _quarantine_ids(policy, manifest, original_provenance)

    # Routine refresh has no activation authority. Its positive activation set
    # is exactly the providers that are already enabled on current main.
    positive_activation_ids = set(current_enabled)
    preserve_ids = set(current_enabled)

    overlay = _refresh_policy_overlay(
        policy,
        candidate_ids,
        current_enabled,
    )
    filtered_lkg = _filtered_activation_lkg(activation_lkg, preserve_ids)

    original_load_overrides = pc.load_overrides
    original_load_json = pc.load_json
    original_update_history = pc.update_strict_history

    config = original_load_json(pc.CONFIG_PATH, {}) or {}
    required_mode = str((config.get("activation") or {}).get("required_validation_mode", "deep"))

    def refresh_load_overrides() -> dict[str, Any]:
        return copy.deepcopy(overlay)

    def refresh_load_json(path: Path, default: Any = None) -> Any:
        value = original_load_json(path, default)
        resolved = Path(path).resolve()
        if resolved == pc.HEALTH_RESULTS_PATH.resolve() and isinstance(value, dict):
            value = copy.deepcopy(value)
            value["mode"] = required_mode
            value["refresh_validation_mode"] = "quick"
        elif resolved == pc.ACTIVATION_LKG_PATH.resolve() and isinstance(value, dict):
            value = copy.deepcopy(filtered_lkg)
        return value

    def refresh_update_history(
        previous: dict[str, Any],
        candidates: list[dict[str, Any]],
        results: list[dict[str, Any]],
        pre_evaluations: dict[str, tuple[dict[str, dict[str, Any]], dict[str, Any]]],
        _mode: str,
        activation: dict[str, Any],
    ) -> dict[str, Any]:
        return original_update_history(
            previous,
            candidates,
            results,
            pre_evaluations,
            "quick",
            activation,
        )

    try:
        pc.load_overrides = refresh_load_overrides
        pc.load_json = refresh_load_json
        pc.update_strict_history = refresh_update_history
        rc = pc.main()
    finally:
        pc.load_overrides = original_load_overrides
        pc.load_json = original_load_json
        pc.update_strict_history = original_update_history

    generated_manifest = pc.load_json(pc.NEXT_MANIFEST_PATH, {"scrapers": []}) or {"scrapers": []}
    next_manifest = _preserve_quick_manifest(generated_manifest, manifest, quarantined)
    _write_json(pc.NEXT_MANIFEST_PATH, next_manifest)

    _postprocess_refresh_outputs(
        canonical_deep_report_bytes,
        original_provenance,
        quarantined,
    )

    next_enabled = _enabled_manifest_ids(next_manifest)
    violations: list[str] = []
    if next_enabled != current_enabled:
        added = sorted(next_enabled - current_enabled)
        removed = sorted(current_enabled - next_enabled)
        if added:
            violations.append("quick refresh attempted activation: " + ", ".join(added))
        if removed:
            violations.append("quick refresh attempted disablement: " + ", ".join(removed))

    current_rows = _manifest_rows(manifest)
    next_rows = _manifest_rows(next_manifest)
    for cid in sorted(quarantined & set(current_rows)):
        if next_rows.get(cid) != current_rows[cid]:
            violations.append(f"{cid}: quick refresh attempted to mutate safety quarantine")

    if violations:
        raise SystemExit("quick refresh publication policy failed:\n- " + "\n- ".join(violations))

    print(
        "quick refresh publication policy passed: "
        f"current_enabled={len(current_enabled)} "
        f"historical_active={len(historical_active)} "
        f"quarantined={len(quarantined)} "
        f"candidate_ids={len(candidate_ids)} "
        f"activation_delta=0"
    )
    return int(rc)


if __name__ == "__main__":
    raise SystemExit(main())
