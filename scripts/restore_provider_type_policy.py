#!/usr/bin/env python3
"""Validate/apply sparse user-confirmed provider semantic media-type constraints.

provider-type-policy.json is deliberately *not* provider scope, activation, or
manifest transport authority. It is a sparse current-catalog intent contract.
provider_catalog.json stores semantic capability; rendered manifests may add
transport-only aliases such as anime -> tv.

Default mode is validation-only. --apply is an explicit maintenance operation
that aligns current catalog/structured DATA, then uses the canonical catalog
renderer to regenerate manifests.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "provider-type-policy.json"
CATALOG = ROOT / "provider_catalog.json"
OVERRIDES = ROOT / "provider-overrides.json"
RENDERER = ROOT / "engine_v2/scripts/render-manifests-from-catalog.mjs"
ALLOWED_TYPES = {"movie", "tv", "anime"}


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path.relative_to(ROOT)}: JSON object required")
    return value


def write(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def cid(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def normalize_types(values: object) -> list[str]:
    out: list[str] = []
    for value in values if isinstance(values, list) else []:
        item = str(value or "").strip().casefold()
        if item in ALLOWED_TYPES and item not in out:
            out.append(item)
    return out


def policy_rows(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if int(payload.get("schema_version") or 0) < 2:
        raise ValueError("provider-type-policy schema >=2 required")
    rows = payload.get("providers")
    if not isinstance(rows, dict):
        raise ValueError("provider-type-policy providers map required")
    out: dict[str, dict[str, Any]] = {}
    for raw_id, row in rows.items():
        provider = cid(raw_id)
        if not provider or not isinstance(row, dict):
            raise ValueError(f"invalid provider-type-policy row: {raw_id!r}")
        if provider in out:
            raise ValueError(f"duplicate provider-type-policy identity: {provider}")
        semantic = normalize_types(row.get("supportedTypes"))
        if not semantic:
            raise ValueError(f"{provider}: empty semantic type policy")
        out[provider] = row
    return out


def catalog_rows(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if payload.get("sourceOfTruth") is not True:
        raise ValueError("provider_catalog.json must remain sourceOfTruth")
    providers = payload.get("providers")
    if not isinstance(providers, list):
        raise ValueError("provider_catalog.json providers list required")
    out: dict[str, dict[str, Any]] = {}
    for record in providers:
        if not isinstance(record, dict) or not isinstance(record.get("scraper"), dict):
            continue
        scraper = record["scraper"]
        provider = cid(record.get("canonicalId") or scraper.get("id"))
        if not provider or provider in out:
            raise ValueError(f"invalid/duplicate current catalog identity: {provider!r}")
        out[provider] = scraper
    return out


def validate(
    policy: dict[str, dict[str, Any]],
    catalog: dict[str, dict[str, Any]],
    overrides: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    outside = sorted(set(policy) - set(catalog))
    if outside:
        errors.append("policy identities outside current catalog: " + ",".join(outside))

    patches = overrides.get("provider_patches") if isinstance(overrides.get("provider_patches"), dict) else {}
    capabilities = overrides.get("provider_capabilities") if isinstance(overrides.get("provider_capabilities"), dict) else {}

    for provider in sorted(set(policy) & set(catalog)):
        desired = normalize_types(policy[provider].get("supportedTypes"))
        scraper = catalog[provider]
        actual = normalize_types(scraper.get("supportedTypes"))
        if "canonicalSupportedTypes" in scraper:
            errors.append(f"{provider}: catalog contains manifest-only canonicalSupportedTypes")
        if actual != desired:
            errors.append(f"{provider}: catalog semantic types {actual} != policy {desired}")

        patch = patches.get(provider)
        if isinstance(patch, dict) and normalize_types(patch.get("published_types")) != desired:
            errors.append(
                f"{provider}: provider_patches published_types "
                f"{normalize_types(patch.get('published_types'))} != policy {desired}"
            )
        capability = capabilities.get(provider)
        if isinstance(capability, dict) and normalize_types(capability.get("catalogue_types")) != desired:
            errors.append(
                f"{provider}: provider_capabilities catalogue_types "
                f"{normalize_types(capability.get('catalogue_types'))} != policy {desired}"
            )
    return errors


def apply_policy(
    policy: dict[str, dict[str, Any]],
    catalog_payload: dict[str, Any],
    overrides: dict[str, Any],
) -> list[str]:
    by_id = catalog_rows(catalog_payload)
    outside = sorted(set(policy) - set(by_id))
    if outside:
        raise ValueError("refuse to resurrect non-current policy identities: " + ",".join(outside))

    patches = overrides.get("provider_patches")
    capabilities = overrides.get("provider_capabilities")
    if not isinstance(patches, dict) or not isinstance(capabilities, dict):
        raise ValueError("structured provider override maps required")

    changed: list[str] = []
    for provider, row in sorted(policy.items()):
        desired = normalize_types(row.get("supportedTypes"))
        scraper = by_id[provider]
        dirty = normalize_types(scraper.get("supportedTypes")) != desired or "canonicalSupportedTypes" in scraper
        scraper["supportedTypes"] = desired
        scraper.pop("canonicalSupportedTypes", None)

        patch = patches.get(provider)
        if isinstance(patch, dict) and normalize_types(patch.get("published_types")) != desired:
            patch["published_types"] = list(desired)
            dirty = True
        capability = capabilities.get(provider)
        if isinstance(capability, dict) and normalize_types(capability.get("catalogue_types")) != desired:
            capability["catalogue_types"] = list(desired)
            dirty = True
        if dirty:
            changed.append(provider)
    return changed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    policy_payload = load(POLICY)
    catalog_payload = load(CATALOG)
    overrides = load(OVERRIDES)
    policy = policy_rows(policy_payload)
    catalog = catalog_rows(catalog_payload)

    if args.apply:
        changed = apply_policy(policy, catalog_payload, overrides)
        write(CATALOG, catalog_payload)
        write(OVERRIDES, overrides)
        subprocess.run(["node", str(RENDERER.relative_to(ROOT))], cwd=ROOT, check=True)
        catalog_payload = load(CATALOG)
        overrides = load(OVERRIDES)
        catalog = catalog_rows(catalog_payload)
    else:
        changed = []

    errors = validate(policy, catalog, overrides)
    if errors:
        raise SystemExit("provider type policy contract failed:\n- " + "\n- ".join(errors))

    print(
        "PROVIDER_TYPE_POLICY_OK "
        f"mode={'apply' if args.apply else 'check'} policy={len(policy)} "
        f"catalog={len(catalog)} changed={len(changed)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
