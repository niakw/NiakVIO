#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Remove stale routing replacements from terminal quarantine candidates.

A content-addressed quarantine bundle is intentionally inert. Once every staged
variant for a provider is a NUVIO_PROVIDER_QUARANTINE_V1 bundle, historical
routing replacement records are no longer meaningful and can make the override
validator demand terminal hosts that the inert bundle deliberately does not
contain. This normalization is publication-neutral: it never reactivates a
provider and never edits the quarantined JavaScript bytes.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MARKER = "NUVIO_PROVIDER_QUARANTINE_V1"


def load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def normalize(root: Path, stage: Path, overrides_path: Path) -> dict[str, int]:
    registry_path = stage / "candidates.json"
    if not registry_path.is_file():
        raise FileNotFoundError(f"missing staged candidate registry: {registry_path}")

    config = load_object(overrides_path)
    registry = load_object(registry_path)
    patches = config.get("provider_patches")
    if not isinstance(patches, dict):
        patches = {}
        config["provider_patches"] = patches

    rows_by_provider: dict[str, list[tuple[dict[str, Any], str]]] = {}
    for row in registry.get("candidates") or []:
        if not isinstance(row, dict):
            continue
        provider_id = str(row.get("canonical_id") or row.get("upstream_id") or "").strip().casefold()
        relative = str(row.get("local_path") or "")
        path = (stage / relative).resolve()
        try:
            path.relative_to(stage.resolve())
        except ValueError:
            continue
        if not provider_id or not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        rows_by_provider.setdefault(provider_id, []).append((row, text))

    terminal = {
        provider_id
        for provider_id, rows in rows_by_provider.items()
        if rows and all(MARKER in text for _row, text in rows)
    }

    removed_maps = 0
    removed_records = 0
    for provider_id in sorted(terminal):
        patch = patches.get(provider_id)
        if not isinstance(patch, dict):
            continue
        for key in ("replacements", "route_replacements", "runtime_domain_replacements"):
            value = patch.get(key)
            if isinstance(value, dict):
                removed_maps += len(value)
                patch[key] = {}
        for row, _text in rows_by_provider.get(provider_id, []):
            records = row.get("local_patches") if isinstance(row.get("local_patches"), list) else []
            kept = []
            for record in records:
                if isinstance(record, dict) and record.get("type") == "replace":
                    removed_records += 1
                    continue
                kept.append(record)
            row["local_patches"] = kept

    meta = config.setdefault("provider_engine_normalization", {})
    if not isinstance(meta, dict):
        meta = {}
        config["provider_engine_normalization"] = meta
    meta["terminal_quarantine_routing_contracts_pruned"] = len(terminal)
    meta["terminal_quarantine_mapping_entries_removed"] = removed_maps
    meta["terminal_quarantine_replace_records_removed"] = removed_records

    overrides_path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    return {
        "providers": len(terminal),
        "mappings": removed_maps,
        "records": removed_records,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", type=Path, default=ROOT / "staging")
    parser.add_argument("--overrides", type=Path, default=ROOT / "provider-overrides.json")
    args = parser.parse_args()
    stats = normalize(ROOT, args.stage.resolve(), args.overrides.resolve())
    print(
        "terminal quarantine normalization: "
        f"providers={stats['providers']} mappings={stats['mappings']} records={stats['records']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
