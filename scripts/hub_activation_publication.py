#!/usr/bin/env python3
"""Validate/persist current provider activation state.

Cardinality is derived from current identities; no fixed provider count is policy.
The active matrix must match enabled manifest providers, while disabled-retained
providers remain visible in manifest.json and provider_catalog.json.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "automation/evidence/hub-lab-matrix-46.json"


def load(rel: str):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def cid(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def active_scope() -> set[str]:
    matrix = load("automation/evidence/hub-lab-matrix-46.json")
    ids = {
        cid(row.get("manifestId") or row.get("provider"))
        for row in matrix.get("rows") or []
        if isinstance(row, dict) and cid(row.get("manifestId") or row.get("provider"))
    }
    declared = int(matrix.get("hubCount") or len(ids))
    if not ids or declared != len(ids):
        raise AssertionError(f"active matrix identity mismatch declared={declared} ids={len(ids)}")
    return ids


def compute_scope() -> dict:
    manifest = load("manifest.json")
    overrides = load("provider-overrides.json")
    patches = overrides.get("provider_patches") if isinstance(overrides.get("provider_patches"), dict) else {}
    rows = [row for row in manifest.get("scrapers") or [] if isinstance(row, dict)]
    row_ids = [cid(row.get("id")) for row in rows]
    if any(not value for value in row_ids) or len(row_ids) != len(set(row_ids)):
        raise AssertionError("manifest provider identities must be unique and non-empty")

    targets = active_scope()
    manifest_active = {cid(row.get("id")) for row in rows if row.get("enabled") is not False}
    if manifest_active != targets:
        raise AssertionError(
            f"active identity mismatch matrix_only={sorted(targets-manifest_active)} manifest_only={sorted(manifest_active-targets)}"
        )

    enabled, disabled = [], []
    for row in rows:
        pid = cid(row.get("id"))
        patch = patches.get(pid) if isinstance(patches.get(pid), dict) else {}
        expected = pid in targets
        if bool(row.get("enabled")) is not expected:
            raise AssertionError((pid, row.get("enabled"), expected))
        mo = patch.get("manifest_overrides") if isinstance(patch.get("manifest_overrides"), dict) else {}
        if "enabled" in mo and bool(mo.get("enabled")) is not expected:
            raise AssertionError((pid, mo.get("enabled"), expected))
        (enabled if expected else disabled).append(pid)

    return {
        "schemaVersion": 2,
        "authority": "manifest.json enabled identities + automation/evidence/hub-lab-matrix-46.json",
        "catalogueProviderCount": len(rows),
        "enabledProviderCount": len(enabled),
        "disabledProviderCount": len(disabled),
        "enabledProviders": sorted(enabled),
        "disabledProviders": sorted(disabled),
        "repairScope": "current-enabled-providers-only",
        "nativeLabPolicy": "reuse-existing-artifacts-first; rerun-only-for-specific-fix-validation",
    }


def write_scope(scope: dict) -> None:
    target = ROOT / "automation/hub-activation-scope.json"
    target.write_text(json.dumps(scope, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def verify_catalog(scope: dict) -> None:
    catalog = load("provider_catalog.json")
    providers = [row for row in catalog.get("providers") or [] if isinstance(row, dict)]
    enabled_expected = set(scope["enabledProviders"])
    disabled_expected = set(scope["disabledProviders"])
    actual_ids: set[str] = set()
    actual_enabled: set[str] = set()
    actual_disabled: set[str] = set()
    for row in providers:
        scraper = row.get("scraper") or {}
        pid = cid(row.get("canonicalId") or scraper.get("id"))
        if not pid:
            continue
        actual_ids.add(pid)
        if scraper.get("enabled") is False:
            actual_disabled.add(pid)
        else:
            actual_enabled.add(pid)
    expected_ids = enabled_expected | disabled_expected
    if actual_ids != expected_ids:
        raise AssertionError(
            f"provider_catalog identity mismatch missing={sorted(expected_ids-actual_ids)} extra={sorted(actual_ids-expected_ids)}"
        )
    if actual_enabled != enabled_expected or actual_disabled != disabled_expected:
        raise AssertionError(
            f"provider_catalog activation mismatch enabled={sorted(actual_enabled^enabled_expected)} disabled={sorted(actual_disabled^disabled_expected)}"
        )


def append_memory(scope: dict) -> None:
    memory = ROOT / "MEMORY.md"
    text = memory.read_text(encoding="utf-8")
    marker = "## 2026-09-15 — active matrix publication authority"
    if marker in text:
        return
    block = f"""\n\n{marker}\n\n- Current visible catalogue: **{scope['catalogueProviderCount']}** identities, derived from the manifest.\n- Executable providers: **{scope['enabledProviderCount']}**, derived from enabled current identities.\n- Disabled-retained providers: **{scope['disabledProviderCount']}**; they remain visible until lifecycle expiry or reactivation.\n- Provider count is data, never a release gate constant.\n"""
    memory.write_text(text.rstrip() + block + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write-scope", action="store_true")
    ap.add_argument("--verify-catalog", action="store_true")
    ap.add_argument("--append-memory", action="store_true")
    args = ap.parse_args()
    scope = compute_scope()
    if args.write_scope:
        write_scope(scope)
    if args.verify_catalog:
        verify_catalog(scope)
    if args.append_memory:
        append_memory(scope)
    print(
        "HUB_ACTIVATION_SCOPE",
        f"visible={scope['catalogueProviderCount']}",
        f"enabled={scope['enabledProviderCount']}",
        f"disabled={scope['disabledProviderCount']}",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
