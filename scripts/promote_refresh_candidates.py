#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Safely publish a routine quick repair transaction.

The canonical publisher intentionally requires ``deep`` health. This wrapper
permits a narrower refresh transaction without weakening activation/media
gates:

* current quick evidence must still satisfy the canonical strict gates;
* new providers cannot be activated by quick refresh;
* historically active providers may be reactivated only from current positive
  proof, never from an inconclusive activation-LKG fallback;
* configured/content-addressed safety quarantines cannot be exited;
* quick runs never advance deep-validation history.
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
sys.path.insert(0, str(SCRIPTS))

import promote_candidates as pc  # noqa: E402
from apply_provider_overrides import load_overrides as load_real_overrides  # noqa: E402


def _canonical(value: Any) -> str:
    return pc.canonical_id(str(value or ""))


def _enabled_manifest_ids(manifest: dict[str, Any]) -> set[str]:
    return {
        _canonical(row.get("id"))
        for row in manifest.get("scrapers") or []
        if isinstance(row, dict) and row.get("enabled") is True and _canonical(row.get("id"))
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
    positive_activation_ids: set[str],
    quarantined_ids: set[str],
) -> dict[str, Any]:
    output = copy.deepcopy(policy)
    patches = output.setdefault("provider_patches", {})
    for cid in sorted(candidate_ids):
        if cid in positive_activation_ids and cid not in quarantined_ids:
            continue
        patch = patches.setdefault(cid, {})
        if not isinstance(patch, dict):
            patch = {}
            patches[cid] = patch
        manifest_overrides = patch.setdefault("manifest_overrides", {})
        if not isinstance(manifest_overrides, dict):
            manifest_overrides = {}
            patch["manifest_overrides"] = manifest_overrides
        manifest_overrides["enabled"] = False
    return output


def _filtered_activation_lkg(payload: dict[str, Any], preserve_ids: set[str]) -> dict[str, Any]:
    output = copy.deepcopy(payload)
    output["active_ids"] = sorted(preserve_ids)
    return output


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

    manifest = pc.load_json(pc.MANIFEST_PATH, {"scrapers": []}) or {"scrapers": []}
    activation_lkg = pc.load_json(pc.ACTIVATION_LKG_PATH, {}) or {}
    provenance = pc.load_json(pc.PROVENANCE_PATH, {"providers": {}}) or {"providers": {}}
    policy = load_real_overrides()

    current_enabled = _enabled_manifest_ids(manifest)
    historical_active = _historical_active_ids(activation_lkg)
    quarantined = _quarantine_ids(policy, manifest, provenance)

    positive_activation_ids = (current_enabled | historical_active) - quarantined
    preserve_ids = current_enabled - quarantined

    overlay = _refresh_policy_overlay(
        policy,
        candidate_ids,
        positive_activation_ids,
        quarantined,
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

    next_manifest = pc.load_json(pc.NEXT_MANIFEST_PATH, {"scrapers": []}) or {"scrapers": []}
    next_rows = {
        _canonical(row.get("id")): row
        for row in next_manifest.get("scrapers") or []
        if isinstance(row, dict)
    }
    violations: list[str] = []
    for cid, row in next_rows.items():
        if row.get("enabled") is not True:
            continue
        if cid in quarantined:
            violations.append(f"{cid}: quick refresh attempted to exit safety quarantine")
        if cid not in positive_activation_ids:
            violations.append(f"{cid}: quick refresh attempted brand-new activation")

    if violations:
        raise SystemExit("quick refresh publication policy failed:\n- " + "\n- ".join(violations))

    print(
        "quick refresh publication policy passed: "
        f"current_enabled={len(current_enabled)} "
        f"historical_active={len(historical_active)} "
        f"quarantined={len(quarantined)} "
        f"candidate_ids={len(candidate_ids)}"
    )
    return int(rc)


if __name__ == "__main__":
    raise SystemExit(main())
