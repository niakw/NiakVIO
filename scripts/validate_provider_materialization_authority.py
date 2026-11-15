#!/usr/bin/env python3
"""Fail closed when published Global provider authority diverges from materialization.

Business invariant:
- every Global active provider is represented exactly once in provider-v3-materialization.json;
- no disabled provider is represented as current executable materialization authority;
- manifest filename, materialization filename and physical bytes agree;
- the content-addressed SHA recorded by materialization matches the actual provider bytes;
- current cardinality fields derive from the live manifest, never from historical constants.

This is intentionally a publication invariant, not a health claim. A provider may
still be under runtime validation, but the bytes Nuvio loads must be the same bytes
the current materialization ledger describes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def cid(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def active_manifest_rows(root: Path) -> dict[str, dict[str, Any]]:
    manifest = load(root / "manifest.json")
    rows: dict[str, dict[str, Any]] = {}
    for row in manifest.get("scrapers") or []:
        if not isinstance(row, dict):
            raise RuntimeError("manifest contains invalid provider row")
        provider = cid(row.get("id"))
        if not provider or provider in rows:
            raise RuntimeError(f"manifest empty/duplicate provider id: {provider!r}")
        filename = str(row.get("filename") or "").strip().replace("\\", "/")
        enabled = row.get("enabled") is not False
        if enabled:
            if not filename.startswith("providers/"):
                raise RuntimeError(f"{provider}: active provider outside providers/: {filename}")
            rows[provider] = row
        elif filename.startswith("providers/"):
            raise RuntimeError(f"{provider}: disabled row still points into providers/: {filename}")
    if not rows:
        raise RuntimeError("manifest has zero active providers")
    return rows


def validate(root: Path = ROOT) -> dict[str, Any]:
    root = root.resolve()
    active = active_manifest_rows(root)
    material = load(root / "provider-v3-materialization.json")
    raw_rows = material.get("providers")
    if not isinstance(raw_rows, list):
        raise RuntimeError("materialization providers must be a list")

    by_id: dict[str, dict[str, Any]] = {}
    for row in raw_rows:
        if not isinstance(row, dict):
            raise RuntimeError("materialization contains invalid provider row")
        provider = cid(row.get("provider"))
        if not provider or provider in by_id:
            raise RuntimeError(f"materialization empty/duplicate provider id: {provider!r}")
        by_id[provider] = row

    active_ids = set(active)
    material_ids = set(by_id)
    missing = sorted(active_ids - material_ids)
    extra = sorted(material_ids - active_ids)
    if missing or extra:
        raise RuntimeError(
            "active/materialization authority mismatch "
            f"missing_active={missing} extra_nonactive={extra}"
        )

    expected_count = len(active_ids)
    for key in ("providerCount", "activeProviderIdentityCount", "expectedProviderCount"):
        value = material.get(key)
        if int(value if value is not None else -1) != expected_count:
            raise RuntimeError(
                f"materialization cardinality mismatch {key}={value!r} expected={expected_count}"
            )

    checked: list[str] = []
    for provider in sorted(active_ids):
        manifest_row = active[provider]
        material_row = by_id[provider]
        manifest_file = str(manifest_row.get("filename") or "").strip().replace("\\", "/")
        material_file = str(material_row.get("file") or "").strip().replace("\\", "/")
        if manifest_file != material_file:
            raise RuntimeError(
                f"{provider}: manifest/materialization file mismatch "
                f"manifest={manifest_file} materialization={material_file}"
            )
        path = (root / manifest_file).resolve()
        providers_dir = (root / "providers").resolve()
        if path.parent != providers_dir or not path.is_file():
            raise RuntimeError(f"{provider}: materialized provider asset missing/escaped: {manifest_file}")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        recorded = str(material_row.get("sha256") or "").strip().casefold()
        if recorded != digest:
            raise RuntimeError(
                f"{provider}: materialization sha mismatch recorded={recorded} actual={digest}"
            )
        if digest[:16] not in path.name:
            raise RuntimeError(
                f"{provider}: content-addressed filename does not expose current sha prefix: {path.name}"
            )
        checked.append(provider)

    return {
        "activeProviderCount": expected_count,
        "materializedProviderCount": len(by_id),
        "providers": checked,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    result = validate(args.root)
    print(
        "FIELD_PROVIDER_MATERIALIZATION_AUTHORITY_OK "
        f"active={result['activeProviderCount']} materialized={result['materializedProviderCount']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
