#!/usr/bin/env python3
"""Materialize exactly one Provider v3 bundle from current structured DATA.

Used by the strict sequential live reconstruction gate. The provider's candidate
bundle is probed, its DATA is finalized, then this script immediately rebuilds the
same provider from the finalized DATA before the workflow may advance to the next
provider.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import materialize_provider_v3_all as allmat

ROOT = Path(__file__).resolve().parents[1]


def materialize_one(provider_id: str) -> dict[str, object]:
    provider_id = allmat.canonical_id(provider_id)
    manifest = allmat.load(allmat.DEFAULT_SOURCE_MANIFEST)
    overrides = allmat.load(allmat.DEFAULT_OVERRIDES)
    static_knowledge = allmat.load(allmat.DEFAULT_STATIC_KNOWLEDGE)
    patches = overrides.get("provider_patches") or {}
    capabilities = overrides.get("provider_capabilities") or {}
    static_rows = static_knowledge.get("providers") or {}

    entry = next(
        (
            row for row in manifest.get("scrapers") or []
            if isinstance(row, dict)
            and allmat.canonical_id(str(row.get("id") or "")) == provider_id
        ),
        None,
    )
    if not isinstance(entry, dict):
        raise ValueError(f"{provider_id}: manifest row not found")
    patch = patches.get(provider_id)
    capability = capabilities.get(provider_id)
    static_row = static_rows.get(provider_id)
    if not isinstance(patch, dict) or not isinstance(capability, dict) or not isinstance(static_row, dict):
        raise ValueError(f"{provider_id}: incomplete structured DATA")

    allmat.normalize_anime_transport_compatibility(entry)
    model = allmat.provider_model(provider_id, patch, capability, static_row)
    seed = allmat.build_clean_provider_seed(
        provider_id,
        entry,
        known_site=model.get("knownSite"),
        provider_model=model,
    )
    base, stripped = allmat.build_base_from_seed(
        provider_id,
        seed,
        overrides_path=allmat.DEFAULT_OVERRIDES,
    )
    data = allmat.build_provider_data_model(
        provider_id,
        entry,
        known_site=model.get("knownSite"),
        provider_model=model,
    )
    bundle = allmat.compose_provider_bundle(provider_id, base, data)
    bundle, applied = allmat.apply_overrides(
        provider_id,
        bundle,
        phase="discovery",
        include_global_core=True,
        config_path=allmat.DEFAULT_OVERRIDES,
    )
    text = bundle.decode("utf-8", errors="strict")

    if text.count("/* BEGIN NIAKVIO_PROVIDER */") != 1:
        raise ValueError(f"{provider_id}: BEGIN PROVIDER cardinality")
    if text.count("/* END NIAKVIO_PROVIDER */") != 1:
        raise ValueError(f"{provider_id}: END PROVIDER cardinality")
    if not text.rstrip().endswith("/* END NIAKVIO_PROVIDER */"):
        raise ValueError(f"{provider_id}: bytes after END PROVIDER")
    if "searchParams.set(" in text or "searchParams.delete(" in text:
        raise ValueError(f"{provider_id}: QuickJS URLSearchParams mutation remains")

    fix_ids = allmat.validate_managed_fixes(text)
    config_id = f"PROVIDER.{provider_id.upper()}.CONFIG.V1"
    if config_id not in fix_ids:
        raise ValueError(f"{provider_id}: provider CONFIG Lego missing")
    core_ids = [fix_id for fix_id in fix_ids if fix_id.startswith("CORE.")]
    if not core_ids:
        raise ValueError(f"{provider_id}: no Core Lego materialized")

    boundary = "/* NUVIO_GLOBAL_CORE_START_BOUNDARY_V1 */"
    if text.count(boundary) != 1:
        raise ValueError(f"{provider_id}: Core boundary count={text.count(boundary)} expected=1")
    boundary_at = text.index(boundary)
    provider_fix_positions: list[int] = []
    core_fix_positions: list[int] = []
    for fix_id in fix_ids:
        span = allmat.owned_span(text, fix_id)
        if span is None:
            raise ValueError(f"{provider_id}: managed Lego span missing: {fix_id}")
        if fix_id.startswith("PROVIDER."):
            provider_fix_positions.append(span[0])
        elif fix_id.startswith("CORE."):
            core_fix_positions.append(span[0])
    if provider_fix_positions and max(provider_fix_positions) >= boundary_at:
        raise ValueError(f"{provider_id}: Provider Lego found after Core boundary")
    if core_fix_positions and min(core_fix_positions) <= boundary_at:
        raise ValueError(f"{provider_id}: Core Lego found before Core boundary")

    minimized = allmat.minimize_text(text)
    allmat.validate_transform(text, minimized.text)
    text = minimized.text
    bundle = text.encode("utf-8")
    if allmat.validate_managed_fixes(text) != fix_ids:
        raise ValueError(f"{provider_id}: minimizer changed managed Lego ownership")
    if text.count(boundary) != 1:
        raise ValueError(f"{provider_id}: minimizer changed Core boundary")

    digest = hashlib.sha256(bundle).hexdigest()
    filename = f"{provider_id}-{digest[:16]}.js"
    relative = f"providers/{filename}"
    allmat.DEFAULT_OUT.mkdir(parents=True, exist_ok=True)
    (allmat.DEFAULT_OUT / filename).write_bytes(bundle)
    entry["filename"] = relative
    entry["version"] = allmat.base_version(entry.get("version"))
    allmat.write_json(allmat.DEFAULT_SOURCE_MANIFEST, manifest)

    report = {
        "provider": provider_id,
        "file": relative,
        "sha256": digest,
        "providerDataSha256": hashlib.sha256(
            json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest(),
        "baseStrippedGeneratedCore": bool(stripped),
        "fixIds": fix_ids,
        "coreCount": len(core_ids),
        "applied": applied,
        "deviceSpecificJs": False,
        "devices": ["tv", "mobile", "desktop"],
        "legacyProviderJsExecuted": False,
        "upstreamJsExecuted": False,
        "minimizer": {
            "enabled": True,
            "savedBytes": minimized.saved_bytes,
            "transformedLines": minimized.transformed_lines,
            "skippedReason": minimized.skipped_reason,
        },
    }
    print(
        "FIELD_PROVIDER_V3_ONE_MATERIALIZED "
        f"provider={provider_id} sha256={digest[:16]} file={relative}"
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("provider_id")
    args = parser.parse_args()
    materialize_one(args.provider_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
