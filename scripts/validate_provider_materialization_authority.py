#!/usr/bin/env python3
"""Fail closed when published Global+France provider authority diverges from materialization.

Business invariant:
- every active provider in the Global+France projection union is represented exactly once in provider-v3-materialization.json;
- no disabled provider is represented as current executable materialization authority;
- manifest filename, materialization filename and physical bytes agree;
- the content-addressed SHA recorded by materialization matches the actual provider bytes;
- current cardinality fields derive from the live projections, never from historical constants.

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
    """Normalize active executable rows across Global and optional France projection."""
    projections: list[tuple[str, str]] = [("manifest.json", "")]
    if (root / "vf" / "manifest.json").is_file():
        projections.append(("vf/manifest.json", "../"))

    states: dict[str, tuple[str, bool]] = {}
    active: dict[str, dict[str, Any]] = {}
    for relative, prefix in projections:
        manifest = load(root / relative)
        local: set[str] = set()
        raw_rows = manifest.get("scrapers")
        if not isinstance(raw_rows, list):
            raise RuntimeError(f"{relative}: missing scraper list")
        for raw in raw_rows:
            if not isinstance(raw, dict):
                raise RuntimeError(f"{relative}: invalid provider row")
            provider = cid(raw.get("id"))
            if not provider or provider in local:
                raise RuntimeError(f"{relative}: empty/duplicate provider id: {provider!r}")
            local.add(provider)
            filename = str(raw.get("filename") or "").strip().replace("\\", "/")
            if prefix:
                if not filename.startswith(prefix):
                    raise RuntimeError(f"{relative}: invalid projection prefix for {provider}: {filename}")
                filename = filename[len(prefix):]
            enabled = raw.get("enabled") is not False
            if enabled and not filename.startswith("providers/"):
                raise RuntimeError(f"{provider}: active provider outside providers/: {filename}")
            if not enabled and filename.startswith("providers/"):
                raise RuntimeError(f"{provider}: disabled row still points into providers/: {filename}")
            state = (filename, enabled)
            if provider in states and states[provider] != state:
                raise RuntimeError(
                    f"projection asset or enabled state mismatch: {provider} "
                    f"{states[provider]} != {state}"
                )
            states[provider] = state
            if enabled:
                normalized = dict(raw)
                normalized["filename"] = filename
                active[provider] = normalized
    if not active:
        raise RuntimeError("Global+France projections have zero active providers")
    return active


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
