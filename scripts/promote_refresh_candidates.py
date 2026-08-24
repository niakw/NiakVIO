#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Safely publish a routine quick repair transaction.

Routine refresh is allowed to recover an *existing* provider when the canonical
promoter has current strict playable/identity proof for a healthy sibling. This
prevents stale disabled baselines and publication-scoped audit quarantines from
waiting for the next scheduled deep run even though a good upstream variant is
already present.

Safety boundaries remain strict:

* current quick evidence must satisfy the canonical activation/media gates;
* an already-enabled provider falls back to its exact current LKG when the run
  is inconclusive;
* brand-new canonical providers remain disabled until deep;
* configured safety quarantines remain immutable and cannot be exited by quick;
* publication-scoped audit quarantines may recover only through a newly selected
  current-strict candidate; the final catalogue/media audit still runs before
  publication and can quarantine it again fail-closed;
* quick runs never advance deep-validation history or overwrite the canonical
  deep health report.
"""
from __future__ import annotations

import copy
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
REFRESH_REPORT_PATH = ROOT / "refresh-health-report.json"
sys.path.insert(0, str(SCRIPTS))

import promote_candidates as pc  # noqa: E402
from apply_provider_overrides import load_overrides as load_real_overrides  # noqa: E402
from normalize_provider_activation_overrides import is_configured_safety_quarantine  # noqa: E402
from reapply_published_overrides import (  # noqa: E402
    bump_provider_version,
    configured_authoritative_types,
)

SEMVER_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")


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


def _configured_safety_quarantine_ids(policy: dict[str, Any]) -> set[str]:
    patches = policy.get("provider_patches") if isinstance(policy.get("provider_patches"), dict) else {}
    return {
        _canonical(raw_id)
        for raw_id, patch in patches.items()
        if _canonical(raw_id) and is_configured_safety_quarantine(patch)
    }


def _publication_quarantine_ids(
    manifest: dict[str, Any],
    provenance: dict[str, Any],
) -> set[str]:
    """Return only publication quarantines that are still live now.

    Content-addressed filenames and provenance survive recovery by design.
    They are historical evidence, not current activation authority. A
    publication-scoped quarantine therefore exists only while the current
    manifest row is disabled and still points at audit-quarantine evidence.
    """
    quarantined: set[str] = set()
    current_rows = _manifest_rows(manifest)
    for cid, row in current_rows.items():
        if row.get("enabled") is not False:
            continue
        filename = str(row.get("filename") or "")
        if "--nuvio-audit-quarantine--" in filename:
            quarantined.add(cid)

    providers = provenance.get("providers") if isinstance(provenance.get("providers"), dict) else {}
    for raw_id, row in providers.items():
        if not isinstance(row, dict):
            continue
        cid = _canonical(raw_id)
        current = current_rows.get(cid)
        if not current or current.get("enabled") is not False:
            continue
        filename = str(row.get("published_filename") or "")
        if "--nuvio-audit-quarantine--" in filename:
            quarantined.add(cid)
    return {value for value in quarantined if value}


def _refresh_policy_overlay(
    policy: dict[str, Any],
    candidate_ids: set[str],
    existing_ids: set[str],
    configured_quarantine_ids: set[str],
) -> dict[str, Any]:
    """Let current proof decide existing providers while blocking unsafe/new IDs."""
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

        if cid in configured_quarantine_ids or cid not in existing_ids:
            manifest_overrides["enabled"] = False
        else:
            # Historical administrative disables are advisory. Existing
            # providers may recover only if canonical current proof enables the
            # selected sibling. No LKG/inconclusive result can do that.
            manifest_overrides.pop("enabled", None)
    return output


def _filtered_activation_lkg(payload: dict[str, Any], preserve_ids: set[str]) -> dict[str, Any]:
    output = copy.deepcopy(payload)
    output["active_ids"] = sorted(preserve_ids)
    return output


def _semver_key(value: Any) -> tuple[int, int, int]:
    match = SEMVER_RE.fullmatch(str(value or "").strip())
    if not match:
        return (-1, -1, -1)
    return tuple(int(part) for part in match.groups())


def _max_semver(*values: Any) -> str:
    candidates = [str(value).strip() for value in values if str(value or "").strip()]
    if not candidates:
        return "1.0.0"
    return max(candidates, key=_semver_key)


def _normalize_quick_manifest_row(
    row: dict[str, Any],
    previous: dict[str, Any] | None,
    policy: dict[str, Any],
) -> dict[str, Any]:
    output = copy.deepcopy(row)
    cid = _canonical(output.get("id"))
    authoritative_types = configured_authoritative_types(policy, cid)
    if authoritative_types:
        output["supportedTypes"] = list(authoritative_types)

    if previous is None:
        original_types = row.get("supportedTypes")
        if authoritative_types and original_types != authoritative_types:
            output["version"] = bump_provider_version(str(output.get("version") or "1.0.0"))
        return output

    previous_version = str(previous.get("version") or "1.0.0")
    artifact_changed = str(output.get("filename") or "") != str(previous.get("filename") or "")
    metadata_changed = output.get("supportedTypes") != previous.get("supportedTypes")
    minimum_version = (
        bump_provider_version(previous_version)
        if artifact_changed or metadata_changed
        else previous_version
    )
    output["version"] = _max_semver(output.get("version"), minimum_version)
    return output


def _preserve_quick_manifest(
    generated: dict[str, Any],
    current: dict[str, Any],
    configured_quarantine_ids: set[str],
    publication_quarantine_ids: set[str],
    policy: dict[str, Any],
) -> dict[str, Any]:
    """Preserve LKG failures but accept current-strict recovery of existing IDs."""
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
            # Discovery is welcome, activation is not. Deep remains the first
            # activation authority for a brand-new canonical provider.
            row = copy.deepcopy(raw)
            row["enabled"] = False
            row = _normalize_quick_manifest_row(row, None, policy)
        elif cid in configured_quarantine_ids:
            row = copy.deepcopy(previous)
        elif previous.get("enabled") is True:
            if raw.get("enabled") is True:
                row = copy.deepcopy(raw)
                row["enabled"] = True
                row = _normalize_quick_manifest_row(row, previous, policy)
            else:
                # Inconclusive/failed refresh must never silently shrink the
                # active set. Keep the exact current LKG row.
                row = _normalize_quick_manifest_row(previous, previous, policy)
        else:
            if raw.get("enabled") is True:
                # Existing disabled provider has fresh strict proof now. This
                # includes a publication-scoped audit quarantine whose new
                # sibling proved healthy; the final global audit remains the
                # fail-closed safety fence before push.
                row = copy.deepcopy(raw)
                row["enabled"] = True
                row = _normalize_quick_manifest_row(row, previous, policy)
            elif cid in publication_quarantine_ids:
                # No valid recovery this run: keep the inert quarantine bytes
                # and their content-addressed evidence exactly as published.
                row = copy.deepcopy(previous)
            else:
                row = copy.deepcopy(raw)
                row["enabled"] = False
                row = _normalize_quick_manifest_row(row, previous, policy)
        result.append(row)

    for cid, row in current_rows.items():
        if cid not in seen:
            if cid in configured_quarantine_ids or cid in publication_quarantine_ids:
                result.append(copy.deepcopy(row))
            else:
                result.append(_normalize_quick_manifest_row(row, row, policy))

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
    preserved_quarantine_ids: set[str],
    recovered_ids: set[str],
) -> None:
    """Store quick evidence separately and restore only still-live quarantines."""
    quick_report = pc.load_json(pc.REPORT_PATH, {}) or {}
    if isinstance(quick_report, dict):
        quick_report["test_mode"] = "quick"
        quick_report["publication_mode"] = "strict_existing_provider_refresh"
        quick_report["recovered_existing_provider_ids"] = sorted(recovered_ids)
        policy = quick_report.setdefault("policy", {})
        if isinstance(policy, dict):
            policy["quick_checks_are_report_only"] = False
            policy["quick_refresh_requires_current_positive_proof"] = True
            policy["quick_refresh_preserves_active_lkg_on_failure"] = True
            policy["quick_refresh_may_recover_existing_provider"] = True
            policy["quick_refresh_may_recover_publication_quarantine"] = True
            policy["quick_refresh_blocks_brand_new_activation"] = True
            policy["configured_safety_quarantine_is_immutable"] = True
            policy["deep_required_for_durable_profile_learning"] = True
        _write_json(REFRESH_REPORT_PATH, quick_report)

    # health-report.json remains the durable deep report. The separate refresh
    # report proves current quick recoveries without rewriting deep history.
    pc.REPORT_PATH.write_bytes(canonical_deep_report_bytes)

    provenance = pc.load_json(pc.PROVENANCE_PATH, {"providers": {}}) or {"providers": {}}
    if isinstance(provenance, dict):
        provenance["validation_mode"] = "quick"
        provenance["publication_mode"] = "strict_existing_provider_refresh"
        providers = provenance.get("providers")
        if not isinstance(providers, dict):
            providers = {}
            provenance["providers"] = providers
        for row in providers.values():
            if isinstance(row, dict) and row.get("checked_at"):
                row["check_mode"] = "quick"
                row["publication_mode"] = "strict_existing_provider_refresh"

        # Only quarantines still present in the final manifest retain their old
        # immutable provenance. A recovered publication quarantine must keep the
        # newly generated current-proof provenance instead.
        original_rows = _provider_rows_by_canonical(original_provenance)
        generated_rows = _provider_rows_by_canonical(provenance)
        for cid in sorted(preserved_quarantine_ids):
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

    current_rows = _manifest_rows(manifest)
    current_ids = set(current_rows)
    current_enabled = _enabled_manifest_ids(manifest)
    historical_active = _historical_active_ids(activation_lkg)
    configured_quarantines = _configured_safety_quarantine_ids(policy)
    publication_quarantines = _publication_quarantine_ids(manifest, original_provenance)

    # LKG only grants preservation, never activation. Existing disabled IDs must
    # earn current proof from the canonical promoter to recover.
    filtered_lkg = _filtered_activation_lkg(activation_lkg, set(current_enabled))
    overlay = _refresh_policy_overlay(
        policy,
        candidate_ids,
        current_ids,
        configured_quarantines,
    )

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
            # Canonical promoter requires the configured validation-mode token;
            # evidence itself remains the real quick health transaction.
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
    generated_rows = _manifest_rows(generated_manifest)
    next_manifest = _preserve_quick_manifest(
        generated_manifest,
        manifest,
        configured_quarantines,
        publication_quarantines,
        policy,
    )
    _write_json(pc.NEXT_MANIFEST_PATH, next_manifest)

    next_rows = _manifest_rows(next_manifest)
    next_enabled = _enabled_manifest_ids(next_manifest)
    recovered_ids = next_enabled - current_enabled
    removed_ids = current_enabled - next_enabled

    preserved_publication_quarantines = {
        cid
        for cid in publication_quarantines & current_ids
        if next_rows.get(cid) == current_rows.get(cid)
    }
    preserved_quarantines = configured_quarantines | preserved_publication_quarantines

    _postprocess_refresh_outputs(
        canonical_deep_report_bytes,
        original_provenance,
        preserved_quarantines,
        recovered_ids,
    )

    violations: list[str] = []
    if removed_ids:
        violations.append("quick refresh attempted disablement: " + ", ".join(sorted(removed_ids)))

    for cid in sorted(recovered_ids):
        if cid not in current_ids:
            violations.append(f"{cid}: quick refresh attempted brand-new activation")
            continue
        if cid in configured_quarantines:
            violations.append(f"{cid}: quick refresh attempted configured safety-quarantine exit")
            continue
        generated = generated_rows.get(cid)
        if not isinstance(generated, dict) or generated.get("enabled") is not True:
            violations.append(f"{cid}: recovery lacks canonical current-strict activation proof")

    for cid in sorted(configured_quarantines & current_ids):
        if next_rows.get(cid) != current_rows[cid]:
            violations.append(f"{cid}: quick refresh attempted to mutate configured safety quarantine")

    if violations:
        raise SystemExit("quick refresh publication policy failed:\n- " + "\n- ".join(violations))

    print(
        "quick refresh publication policy passed: "
        f"current_enabled={len(current_enabled)} "
        f"next_enabled={len(next_enabled)} "
        f"recovered_existing={len(recovered_ids)} "
        f"historical_active={len(historical_active)} "
        f"configured_quarantines={len(configured_quarantines)} "
        f"publication_quarantines={len(publication_quarantines)} "
        f"candidate_ids={len(candidate_ids)} "
        f"recovered_ids={','.join(sorted(recovered_ids)) or '-'}"
    )
    return int(rc)


if __name__ == "__main__":
    raise SystemExit(main())
