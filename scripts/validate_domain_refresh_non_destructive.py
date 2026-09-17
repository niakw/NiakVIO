#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

ALLOWED_PATCH_KEYS = {
    "official_site",
    "official_hub",
    "domain_substitutions",
    "replacements",
    "runtime_domain_replacements",
}
ALLOWED_MANIFEST_OVERRIDE_KEYS = {"logo", "icon", "favicon"}
ALLOWED_MANIFEST_ROW_KEYS = {"filename"}
ALLOWED_MATERIAL_ROW_KEYS = {"file", "sha256", "providerDataSha256"}
ALLOWED_MATERIAL_TOP_KEYS = {
    "generation",
    "providerCount",
    "expectedProviderCount",
    "domainAuthorityOnlyUpdate",
    "domainAuthorityUpdatedProviders",
}


def load(path: str | Path) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"{path}: object required")
    return value


def canon(value: object) -> str:
    return str(value or "").strip().casefold()


def rows(document: dict[str, Any], key: str, id_key: str) -> dict[str, dict[str, Any]]:
    raw = document.get(key) or []
    if isinstance(raw, dict):
        return {canon(k): v for k, v in raw.items() if canon(k) and isinstance(v, dict)}
    if isinstance(raw, list):
        return {
            canon(v.get(id_key)): v
            for v in raw
            if isinstance(v, dict) and canon(v.get(id_key))
        }
    raise AssertionError(f"{key}: object/list required")


def strip_allowed_patch(patch: dict[str, Any]) -> dict[str, Any]:
    out = json.loads(json.dumps(patch))
    for key in ALLOWED_PATCH_KEYS:
        out.pop(key, None)
    manifest = out.get("manifest_overrides")
    if isinstance(manifest, dict):
        for key in ALLOWED_MANIFEST_OVERRIDE_KEYS:
            manifest.pop(key, None)
        if not manifest:
            out.pop("manifest_overrides", None)
    return out


def strip_keys(row: dict[str, Any], allowed: set[str]) -> dict[str, Any]:
    return {k: v for k, v in row.items() if k not in allowed}


def changed_ids(changes: dict[str, Any]) -> set[str]:
    return {canon(x) for x in changes.get("changed") or [] if canon(x)}


def validate_provider_files(before_manifest: dict[str, Any], after_manifest: dict[str, Any], touched: set[str]) -> None:
    before_rows = rows(before_manifest, "scrapers", "id")
    after_rows = rows(after_manifest, "scrapers", "id")
    allowed_paths: set[str] = set()
    for pid in touched:
        for source in (before_rows.get(pid), after_rows.get(pid)):
            if isinstance(source, dict):
                path = str(source.get("filename") or "").strip()
                if path.startswith(("providers/", "provider-disabled/")):
                    allowed_paths.add(path)
    proc = subprocess.run(
        ["git", "diff", "--name-only", "--", "providers/", "provider-disabled/"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    observed = {line.strip() for line in proc.stdout.splitlines() if line.strip()}
    unexpected = sorted(observed - allowed_paths)
    if unexpected:
        raise AssertionError(f"domain refresh touched unrelated provider bundles: {unexpected[:20]}")


def validate(args: argparse.Namespace) -> dict[str, Any]:
    before_overrides = load(args.before_overrides)
    after_overrides = load(args.after_overrides)
    before_manifest = load(args.before_manifest)
    after_manifest = load(args.after_manifest)
    before_material = load(args.before_materialization)
    after_material = load(args.after_materialization)
    before_provenance = load(args.before_provenance)
    after_provenance = load(args.after_provenance)
    changes = load(args.changes)
    touched = changed_ids(changes)

    before_patches = rows(before_overrides, "provider_patches", "id")
    after_patches = rows(after_overrides, "provider_patches", "id")
    if set(before_patches) != set(after_patches):
        raise AssertionError("Domain Refresh may not add/remove provider patches")
    for pid in sorted(before_patches):
        before = before_patches[pid]
        after = after_patches[pid]
        if pid not in touched:
            if before != after:
                raise AssertionError(f"{pid}: untouched provider patch mutated")
            continue
        if strip_allowed_patch(before) != strip_allowed_patch(after):
            raise AssertionError(f"{pid}: non-domain provider repair/proof data mutated")
        if before.get("repair_disposition") != after.get("repair_disposition"):
            raise AssertionError(f"{pid}: repair_disposition changed during Domain Refresh")
        if before.get("provider_lego_scripts") != after.get("provider_lego_scripts"):
            raise AssertionError(f"{pid}: provider Lego changed during Domain Refresh")

    before_manifest_rows = rows(before_manifest, "scrapers", "id")
    after_manifest_rows = rows(after_manifest, "scrapers", "id")
    if list(before_manifest_rows) != list(after_manifest_rows):
        raise AssertionError("Domain Refresh may not change manifest provider identity/order")
    for pid in before_manifest_rows:
        before = before_manifest_rows[pid]
        after = after_manifest_rows[pid]
        if pid not in touched:
            if before != after:
                raise AssertionError(f"{pid}: untouched manifest row mutated")
        elif strip_keys(before, ALLOWED_MANIFEST_ROW_KEYS) != strip_keys(after, ALLOWED_MANIFEST_ROW_KEYS):
            raise AssertionError(f"{pid}: Domain Refresh changed non-filename manifest fields")

    before_material_rows = rows(before_material, "providers", "provider")
    after_material_rows = rows(after_material, "providers", "provider")
    if set(before_material_rows) != set(after_material_rows):
        raise AssertionError("Domain Refresh may not change materialization provider identity")
    for pid in before_material_rows:
        before = before_material_rows[pid]
        after = after_material_rows[pid]
        if pid not in touched:
            if before != after:
                raise AssertionError(f"{pid}: untouched materialization row mutated")
        elif strip_keys(before, ALLOWED_MATERIAL_ROW_KEYS) != strip_keys(after, ALLOWED_MATERIAL_ROW_KEYS):
            raise AssertionError(f"{pid}: Domain Refresh changed non-domain materialization fields")
    before_material_top = {k: v for k, v in before_material.items() if k != "providers" and k not in ALLOWED_MATERIAL_TOP_KEYS}
    after_material_top = {k: v for k, v in after_material.items() if k != "providers" and k not in ALLOWED_MATERIAL_TOP_KEYS}
    if before_material_top != after_material_top:
        raise AssertionError("Domain Refresh mutated unrelated materialization metadata")

    before_prov_rows = rows(before_provenance, "providers", "id")
    after_prov_rows = rows(after_provenance, "providers", "id")
    if set(before_prov_rows) != set(after_prov_rows):
        raise AssertionError("Domain Refresh may not add/remove provenance providers")
    for pid in before_prov_rows:
        if pid not in touched and before_prov_rows[pid] != after_prov_rows[pid]:
            raise AssertionError(f"{pid}: untouched provenance mutated")

    validate_provider_files(before_manifest, after_manifest, touched)
    declared_updates = {canon(row.get("provider")) for row in changes.get("bundle_updates") or [] if isinstance(row, dict)}
    if declared_updates != touched:
        raise AssertionError(f"bundle update accounting mismatch touched={sorted(touched)} bundles={sorted(declared_updates)}")

    result = {
        "changed": sorted(touched),
        "preserved_provider_patches": len(before_patches) - len(touched),
        "preserved_manifest_rows": len(before_manifest_rows) - len(touched),
        "repair_evidence_preserved": True,
        "unrelated_bundle_churn": False,
    }
    print("FIELD_DOMAIN_REFRESH_NON_DESTRUCTIVE " + json.dumps(result, sort_keys=True))
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--before-overrides", required=True)
    parser.add_argument("--before-manifest", required=True)
    parser.add_argument("--before-materialization", required=True)
    parser.add_argument("--before-provenance", required=True)
    parser.add_argument("--after-overrides", default="provider-overrides.json")
    parser.add_argument("--after-manifest", default="manifest.json")
    parser.add_argument("--after-materialization", default="provider-v3-materialization.json")
    parser.add_argument("--after-provenance", default="PROVENANCE.json")
    parser.add_argument("--changes", default="health-output/domain-site-changes.json")
    args = parser.parse_args()
    validate(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
