#!/usr/bin/env python3
"""Reconcile targeted provider publication back to a public fixed point."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from domain_refresh_transaction_v2 import _generation, source_qualified_provider_name
from provider_patch_blocks import decode_managed_data, validate_managed_fixes


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


def reconcile(
    root: Path,
    provider_ids: list[str],
    *,
    sync_projections: Callable[[bool], Any] | None = None,
) -> list[dict[str, str]]:
    manifest_path = root / "manifest.json"
    materialization_path = root / "provider-v3-materialization.json"
    manifest = load_json(manifest_path)
    materialization = load_json(materialization_path)

    manifest_rows = [
        row for row in manifest.get("scrapers") or []
        if isinstance(row, dict) and cid(row.get("id"))
    ]
    material_rows = [
        row for row in materialization.get("providers") or []
        if isinstance(row, dict) and cid(row.get("provider"))
    ]
    manifest_by_id = {cid(row.get("id")): row for row in manifest_rows}
    material_by_id = {cid(row.get("provider")): row for row in material_rows}

    requested = [cid(value) for value in provider_ids if cid(value)]
    unknown = sorted(set(requested) - set(manifest_by_id))
    if unknown:
        raise RuntimeError("unknown manifest providers: " + ",".join(unknown))

    updates: list[dict[str, str]] = []
    for provider_id in requested:
        manifest_row = manifest_by_id[provider_id]
        material_row = material_by_id.get(provider_id)
        if material_row is None:
            raise RuntimeError(f"{provider_id}: materialization row missing")

        current_rel = str(manifest_row.get("filename") or "").strip()
        current_path = root / current_rel
        if not current_rel or not current_path.is_file():
            raise RuntimeError(f"{provider_id}: manifest bundle missing: {current_rel!r}")

        raw = current_path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        text = raw.decode("utf-8")
        fix_id = config_fix_id(provider_id)
        if fix_id not in validate_managed_fixes(text):
            raise RuntimeError(f"{provider_id}: CONFIG Lego missing: {fix_id}")
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

        manifest_row["filename"] = new_rel
        material_row["file"] = new_rel
        material_row["sha256"] = digest
        material_row["providerDataSha256"] = data_digest(data)
        updates.append({
            "provider": provider_id,
            "from": current_rel,
            "to": new_rel,
            "sha256": digest,
        })

    materialization["generation"] = _generation(material_rows)
    materialization["providerCount"] = len(material_rows)
    materialization["expectedProviderCount"] = len(material_rows)
    materialization["targetedPublicationFixedPointProviders"] = sorted(set(requested))

    write_json(manifest_path, manifest)
    write_json(materialization_path, materialization)

    if sync_projections is not None:
        sync_projections(False)

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
