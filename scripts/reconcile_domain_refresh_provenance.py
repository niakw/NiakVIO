#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manifest.json"
MATERIALIZATION = ROOT / "provider-v3-materialization.json"
PROVENANCE = ROOT / "PROVENANCE.json"


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"{path}: object required")
    return value


def write(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def canon(value: object) -> str:
    return str(value or "").strip().casefold()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--changes", default="health-output/domain-site-changes.json")
    args = parser.parse_args()

    changes = load(ROOT / args.changes)
    selected = {canon(x) for x in changes.get("changed") or [] if canon(x)}
    manifest = load(MANIFEST)
    materialization = load(MATERIALIZATION)
    provenance = load(PROVENANCE)

    manifest_rows = {
        canon(row.get("id")): row
        for row in manifest.get("scrapers") or []
        if isinstance(row, dict) and canon(row.get("id"))
    }
    material_rows = {
        canon(row.get("provider")): row
        for row in materialization.get("providers") or []
        if isinstance(row, dict) and canon(row.get("provider"))
    }
    provenance_rows = provenance.get("providers")
    if not isinstance(provenance_rows, dict):
        raise SystemExit("PROVENANCE.json providers map required")

    changed = []
    for provider_id in sorted(selected):
        manifest_row = manifest_rows.get(provider_id)
        material_row = material_rows.get(provider_id)
        provenance_row = provenance_rows.get(provider_id)
        if not all(isinstance(x, dict) for x in (manifest_row, material_row, provenance_row)):
            raise SystemExit(f"{provider_id}: incomplete publication provenance state")
        filename = str(manifest_row.get("filename") or "").strip()
        digest = str(material_row.get("sha256") or "").strip().casefold()
        if not filename.startswith("providers/") or len(digest) != 64:
            raise SystemExit(f"{provider_id}: invalid current publication identity")
        before = json.dumps(provenance_row, ensure_ascii=False, sort_keys=True)
        provenance_row["published_filename"] = filename
        provenance_row["sha256"] = digest
        if "patched_sha256" in provenance_row:
            provenance_row["patched_sha256"] = digest
        fixed = provenance_row.get("final_fixed_point")
        if isinstance(fixed, dict):
            fixed["sha256"] = digest
        minimizer = provenance_row.get("final_minimizer")
        if isinstance(minimizer, dict):
            minimizer["sha256"] = digest
        if before != json.dumps(provenance_row, ensure_ascii=False, sort_keys=True):
            changed.append(provider_id)

    if changed:
        write(PROVENANCE, provenance)
    print(
        "FIELD_DOMAIN_REFRESH_PROVENANCE "
        f"scope={','.join(sorted(selected)) if selected else '-'} "
        f"changed={','.join(changed) if changed else '-'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
