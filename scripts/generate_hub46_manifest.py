#!/usr/bin/env python3
"""Generate the physical 46-provider manifest consumed by the native repair Labs.

The published/global manifest remains untouched.  This derived root-level manifest is
intentionally rooted beside providers/ so relative provider filenames keep their normal
GitHub raw URL semantics inside the official Nuvio clients.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "manifest.json"
DEFAULT_MATRIX = ROOT / "automation/evidence/hub-lab-matrix-46.json"
DEFAULT_OUTPUT = ROOT / "manifest-hub46.json"


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"expected JSON object: {path}")
    return value


def matrix_ids(matrix: dict[str, Any]) -> list[str]:
    rows = matrix.get("rows")
    if not isinstance(rows, list):
        raise SystemExit("Hub-46 matrix rows must be a list")
    ids: list[str] = []
    seen: set[str] = set()
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise SystemExit(f"Hub-46 matrix row {index} is not an object")
        raw = row.get("manifestId") or row.get("registryId")
        provider_id = str(raw or "").strip()
        if not provider_id:
            raise SystemExit(f"Hub-46 matrix row {index} has no provider id")
        key = provider_id.casefold()
        if key in seen:
            raise SystemExit(f"duplicate Hub-46 provider id: {provider_id}")
        seen.add(key)
        ids.append(provider_id)
    declared = int(matrix.get("hubCount") or 0)
    if declared <= 0 or len(ids) != declared:
        raise SystemExit(f"active hub authority mismatch: hubCount={declared} rows={len(ids)}")
    return ids


def build(source: dict[str, Any], matrix: dict[str, Any]) -> dict[str, Any]:
    scrapers = source.get("scrapers")
    if not isinstance(scrapers, list):
        raise SystemExit("source manifest scrapers must be a list")
    by_id: dict[str, dict[str, Any]] = {}
    for row in scrapers:
        if not isinstance(row, dict):
            continue
        provider_id = str(row.get("id") or "").strip()
        if not provider_id:
            continue
        key = provider_id.casefold()
        if key in by_id:
            raise SystemExit(f"duplicate provider in source manifest: {provider_id}")
        by_id[key] = row

    wanted = matrix_ids(matrix)
    selected: list[dict[str, Any]] = []
    missing: list[str] = []
    for provider_id in wanted:
        row = by_id.get(provider_id.casefold())
        if row is None:
            missing.append(provider_id)
        else:
            selected.append(row)
    if missing:
        raise SystemExit("Hub-46 provider(s) absent from source manifest: " + ", ".join(missing))
    expected_count = len(wanted)
    if len(selected) != expected_count:
        raise SystemExit(f"derived manifest count={len(selected)} expected={expected_count}")

    output = dict(source)
    output["scrapers"] = selected
    output["labScope"] = {
        "kind": "active-hub-repair-campaign",
        "providerCount": len(wanted),
        "authority": "automation/evidence/hub-lab-matrix-46.json",
    }
    return output


def generate(source_path: Path, matrix_path: Path, output_path: Path, *, check: bool = False) -> None:
    output = build(load_json(source_path), load_json(matrix_path))
    rendered = json.dumps(output, ensure_ascii=False, indent=2) + "\n"
    if check:
        if not output_path.is_file():
            raise SystemExit(f"derived Hub-46 manifest missing: {output_path}")
        current = output_path.read_text(encoding="utf-8")
        if current != rendered:
            raise SystemExit("derived Hub-46 manifest is stale; rerun scripts/generate_hub46_manifest.py")
        print(f"FIELD_HUB46_MANIFEST_CHECK providers={len(output.get('scrapers') or [])} status=clean path={output_path}")
        return
    output_path.write_text(rendered, encoding="utf-8")
    print(f"FIELD_HUB46_MANIFEST_GENERATED providers={len(output.get('scrapers') or [])} path={output_path}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--matrix", type=Path, default=DEFAULT_MATRIX)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    generate(args.source, args.matrix, args.output, check=args.check)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
