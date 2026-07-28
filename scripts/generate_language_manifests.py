#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Generate the VF-only manifest alongside the general manifest.

Output:
- vf/manifest.json: all declared/observed French-capable providers, preserving enabled state.

Classification comes from health-report.json, where observed runtime language
modes take precedence over broad upstream descriptions. Provider filenames are
rewritten relative to the nested manifest directories.
"""
from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def atomic_write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, delete=False, suffix=".tmp"
    ) as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        temporary = handle.name
    os.replace(temporary, path)


def nested_entry(entry: dict[str, Any]) -> dict[str, Any]:
    copied = dict(entry)
    filename = str(copied.get("filename", ""))
    if filename and not filename.startswith(("http://", "https://", "/", "../")):
        copied["filename"] = f"../{filename}"
    return copied


def build_manifest(
    source: dict[str, Any],
    language_by_id: dict[str, str],
    accepted_groups: set[str],
    name_suffix: str,
) -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    for entry in source.get("scrapers", []):
        if not isinstance(entry, dict):
            continue
        provider_id = str(entry.get("id", ""))
        declared = entry.get("contentLanguage", [])
        if isinstance(declared, str):
            declared = [declared]
        declared_fr = any(str(value).casefold().startswith("fr") for value in declared)
        observed_group = language_by_id.get(provider_id)
        if observed_group not in accepted_groups and not declared_fr:
            continue
        entries.append(nested_entry(entry))
    return {
        "name": f"{source.get('name', 'Nuvio Curated Providers')} — {name_suffix}",
        "version": source.get("version"),
        "scrapers": entries,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=ROOT / "manifest.json")
    parser.add_argument("--report", type=Path, default=ROOT / "health-report.json")
    args = parser.parse_args()

    manifest = load_json(args.manifest.resolve())
    report = load_json(args.report.resolve())
    language_by_id = {
        str(item.get("id", "")): str(item.get("manifest_ordering", {}).get("language_group", "other"))
        for item in report.get("providers", [])
        if isinstance(item, dict)
    }

    vf_manifest = build_manifest(manifest, language_by_id, {"vf"}, "VF uniquement")
    atomic_write_json(ROOT / "vf" / "manifest.json", vf_manifest)

    print(f"Generated VF manifest: VF={len(vf_manifest['scrapers'])}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
