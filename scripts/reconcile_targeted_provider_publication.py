#!/usr/bin/env python3
"""Reconcile targeted provider publication back to a public fixed point."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from domain_refresh_transaction_v2 import _generation, source_qualified_provider_name
from provider_patch_blocks import decode_managed_data, validate_managed_fixes
from provider_v3_minimizer import minimize_text, validate_transform
from current_provider_scope import projection_active_provider_ids


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected object: {path}")
    return value


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def cid(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def config_fix_id(provider_id: str) -> str:
    return f"PROVIDER.{provider_id.upper()}.CONFIG.V1"


def data_digest(data: dict[str, Any]) -> str:
    raw = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


CATALOG_SCRAPER_FIELDS = (
    "id",
    "name",
    "description",
    "version",
    "author",
    "supportedTypes",
    "filename",
    "enabled",
    "logo",
    "contentLanguage",
    "formats",
    "limited",
    "supportsExternalPlayer",
    "disabledPlatforms",
    "hasSettings",
    "notes",
    "disabledReason",
    "disabledAt",
    "purgeAfter",
    "lifecycleState",
)


def sync_global_catalog_scraper(
    provider_id: str,
    manifest_row: dict[str, Any],
    catalog_record: dict[str, Any],
) -> None:
    """Mirror one Global published row into provider_catalog without transport aliases."""
    projections = catalog_record.get("projections")
    scraper = catalog_record.get("scraper")
    if not isinstance(projections, dict) or projections.get("general") is not True:
        raise RuntimeError(f"{provider_id}: Global manifest identity lacks general catalogue authority")
    if not isinstance(scraper, dict):
        raise RuntimeError(f"{provider_id}: provider_catalog scraper row missing")

    for key in CATALOG_SCRAPER_FIELDS:
        if key in {"supportedTypes", "filename", "disabledPlatforms"}:
            continue
        if key in manifest_row:
            scraper[key] = copy.deepcopy(manifest_row[key])
        else:
            scraper.pop(key, None)

    semantic = manifest_row.get("canonicalSupportedTypes")
    if not isinstance(semantic, list) or not semantic:
        semantic = manifest_row.get("supportedTypes") or []
    scraper["supportedTypes"] = copy.deepcopy(semantic)

    filename = str(manifest_row.get("filename") or "").strip().replace("\\", "/")
    while filename.startswith("../"):
        filename = filename[3:]
    if not filename:
        raise RuntimeError(f"{provider_id}: Global manifest filename missing")
    scraper["filename"] = filename
    scraper["disabledPlatforms"] = []


def reconcile(
    root: Path,
    provider_ids: list[str],
    *,
    sync_projections: Callable[[bool], Any] | None = None,
) -> list[dict[str, str]]:
    manifest_path = root / "manifest.json"
    catalog_path = root / "provider_catalog.json"
    materialization_path = root / "provider-v3-materialization.json"
    provenance_path = root / "PROVENANCE.json"
    manifest = load_json(manifest_path)
    catalog = load_json(catalog_path) if catalog_path.is_file() else None
    materialization = load_json(materialization_path)
    provenance = load_json(provenance_path) if provenance_path.is_file() else None
    provenance_rows = provenance.get("providers") if isinstance(provenance, dict) else None
    if provenance is not None and not isinstance(provenance_rows, dict):
        raise RuntimeError("PROVENANCE.json providers map required")

    manifest_rows = [
        row for row in manifest.get("scrapers") or []
        if isinstance(row, dict) and cid(row.get("id"))
    ]
    material_rows = [
        row for row in materialization.get("providers") or []
        if isinstance(row, dict) and cid(row.get("provider"))
    ]
    manifest_by_id = {cid(row.get("id")): row for row in manifest_rows}
    publication_by_id: dict[str, tuple[dict[str, Any], str]] = {
        provider_id: (row, "global-manifest")
        for provider_id, row in manifest_by_id.items()
    }
    catalog_record_by_id: dict[str, dict[str, Any]] = {}
    if isinstance(catalog, dict):
        for record in catalog.get("providers") or []:
            if not isinstance(record, dict):
                continue
            scraper = record.get("scraper")
            projections = record.get("projections")
            provider_id = cid(
                record.get("canonicalId")
                or ((scraper or {}).get("id") if isinstance(scraper, dict) else "")
            )
            if provider_id:
                if provider_id in catalog_record_by_id:
                    raise RuntimeError(f"{provider_id}: duplicate provider_catalog identity")
                catalog_record_by_id[provider_id] = record
            if (
                not provider_id
                or not isinstance(scraper, dict)
                or not isinstance(projections, dict)
                or projections.get("general") is not False
                or projections.get("vf") is not True
            ):
                continue
            if provider_id in publication_by_id:
                raise RuntimeError(
                    f"{provider_id}: France-only catalog identity collides with Global manifest"
                )
            publication_by_id[provider_id] = (scraper, "france-only-catalog")
    material_by_id = {cid(row.get("provider")): row for row in material_rows}

    requested = [cid(value) for value in provider_ids if cid(value)]
    unknown = sorted(set(requested) - set(publication_by_id))
    if unknown:
        raise RuntimeError("unknown published providers: " + ",".join(unknown))

    # Snapshot executable identity authority while the on-disk projection and
    # its content-addressed assets are still mutually consistent. The loop
    # below intentionally replaces provider files before the new manifest is
    # published; re-reading projection scope after those old assets are
    # unlinked creates a read-after-delete race against the stale disk manifest.
    if root.resolve() == ROOT.resolve():
        active_ids = set(projection_active_provider_ids())
    else:
        # Unit/workbench roots do not share the repository providers/ tree.
        # Their local manifest/catalog is the only valid active-scope authority.
        active_ids = {
            provider_id
            for provider_id, (row, _authority) in publication_by_id.items()
            if row.get("enabled") is not False
        }

    updates: list[dict[str, str]] = []
    for provider_id in requested:
        manifest_row, entry_authority = publication_by_id[provider_id]
        material_row = material_by_id.get(provider_id)
        if material_row is None:
            raise RuntimeError(f"{provider_id}: materialization row missing")

        current_rel = str(manifest_row.get("filename") or "").strip()
        current_path = root / current_rel
        if not current_rel or not current_path.is_file():
            raise RuntimeError(f"{provider_id}: manifest bundle missing: {current_rel!r}")

        original = current_path.read_text(encoding="utf-8")
        original_fix_ids = validate_managed_fixes(original)
        fix_id = config_fix_id(provider_id)
        if fix_id not in original_fix_ids:
            raise RuntimeError(f"{provider_id}: CONFIG Lego missing: {fix_id}")

        minimized = minimize_text(original)
        validate_transform(original, minimized.text)
        text = minimized.text
        if validate_managed_fixes(text) != original_fix_ids:
            raise RuntimeError(f"{provider_id}: fixed-point canonicalization changed Lego ownership")
        if minimize_text(text).text != text:
            raise RuntimeError(f"{provider_id}: targeted publication is not minimizer fixed-point")

        raw = text.encode("utf-8")
        digest = hashlib.sha256(raw).hexdigest()
        data = decode_managed_data(text, fix_id)
        if not isinstance(data, dict):
            raise RuntimeError(f"{provider_id}: CONFIG data is not an object")

        old_rel = str(material_row.get("file") or current_rel).strip() or current_rel
        old_path = root / old_rel
        new_rel = f"providers/{source_qualified_provider_name(provider_id, old_path, digest)}"
        new_path = root / new_rel
        new_path.parent.mkdir(parents=True, exist_ok=True)
        if new_path != current_path:
            new_path.write_bytes(raw)
        else:
            current_path.write_bytes(raw)

        manifest_row["filename"] = new_rel
        material_row["file"] = new_rel
        material_row["sha256"] = digest
        material_row["providerDataSha256"] = data_digest(data)

        if isinstance(catalog, dict) and entry_authority == "global-manifest":
            catalog_record = catalog_record_by_id.get(provider_id)
            if catalog_record is None:
                raise RuntimeError(f"{provider_id}: Global manifest identity missing from provider_catalog")
            sync_global_catalog_scraper(provider_id, manifest_row, catalog_record)

        if isinstance(provenance_rows, dict):
            provenance_row = provenance_rows.get(provider_id)
            if not isinstance(provenance_row, dict):
                raise RuntimeError(f"{provider_id}: provenance row missing")
            provenance_row["published_filename"] = new_rel
            provenance_row["sha256"] = digest
            if "patched_sha256" in provenance_row:
                provenance_row["patched_sha256"] = digest

            fixed = provenance_row.get("final_fixed_point")
            if not isinstance(fixed, dict):
                fixed = {}
            fixed.update({
                "schema_version": 1,
                "verified": True,
                "tool": "raw-bytes",
                "tool_version": "raw-v1",
                "mangle": False,
                "one_physical_line": True,
                "sha256": digest,
            })
            provenance_row["final_fixed_point"] = fixed

            proof = provenance_row.get("final_minimizer")
            if not isinstance(proof, dict):
                proof = {}
            minimizer_path = ROOT / "scripts" / "provider_v3_minimizer.py"
            proof.update({
                "schema_version": 3,
                "tool": "scripts/provider_v3_minimizer.py",
                "tool_sha256": hashlib.sha256(minimizer_path.read_bytes()).hexdigest(),
                "production_enabled": True,
                "terser_allowed": False,
                "one_physical_line": True,
                "saved_bytes": int(proof.get("saved_bytes") or 0),
                "transformed_lines": int(proof.get("transformed_lines") or 0),
                "skipped_reason": str(proof.get("skipped_reason") or ""),
                "sha256": digest,
            })
            provenance_row["final_minimizer"] = proof

        if current_path != new_path and current_path.exists():
            current_path.unlink()

        updates.append({
            "provider": provider_id,
            "authority": entry_authority,
            "from": current_rel,
            "to": new_rel,
            "sha256": digest,
            "savedBytes": str(minimized.saved_bytes),
        })

    # Materialization is authority for the executable Global+France union.
    # The identity snapshot above is stable across this transaction; targeting
    # only Global publication must never retire France-only rows.
    material_rows[:] = [
        row for row in material_rows
        if cid(row.get("provider")) in active_ids
    ]
    materialization["providers"] = material_rows
    materialization["generation"] = _generation(material_rows)
    materialization["providerCount"] = len(material_rows)
    materialization["activeProviderIdentityCount"] = len(active_ids)
    materialization["expectedProviderCount"] = len(active_ids)
    materialization["targetedPublicationFixedPointProviders"] = sorted(set(requested))
    materialization["targetedPublicationComplete"] = len(material_rows) == len(active_ids)

    write_json(manifest_path, manifest)
    if isinstance(catalog, dict):
        write_json(catalog_path, catalog)
    write_json(materialization_path, materialization)
    if isinstance(provenance, dict):
        write_json(provenance_path, provenance)

    if sync_projections is not None:
        sync_projections(check=False)

    return updates


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", action="append", default=[])
    args = parser.parse_args()
    if not args.provider:
        raise SystemExit("at least one --provider is required")

    from sync_manifest_projection_rows import sync as sync_projection_rows

    updates = reconcile(ROOT, args.provider, sync_projections=sync_projection_rows)
    print(
        "FIELD_TARGETED_PUBLICATION_FIXED_POINT "
        + " ".join(
            f"{row['provider']}={row['to']}:{row['sha256'][:16]}"
            for row in updates
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
