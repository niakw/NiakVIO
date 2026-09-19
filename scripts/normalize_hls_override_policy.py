#!/usr/bin/env python3
"""Migrate provider metadata to content-proven HLS validation.

A path fragment such as `/troll/` is not proof that a response is invalid. The
real gate is the fetched content: a playlist must begin with `#EXTM3U` after BOM
and whitespace normalization. Known fake hosts such as fstream.top remain
blocked independently.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OLD_PATCH = "scripts/provider_patches/stream_output_sanitizer.py"
NEW_PATCH = "scripts/provider_patches/stream_output_sanitizer_v5.py"
TARGET_FILES = (ROOT / "provider-overrides.json", ROOT / "PROVENANCE.json")


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def migrate(value: Any, parent_key: str = "") -> tuple[Any, int]:
    changes = 0
    if isinstance(value, dict):
        output: dict[str, Any] = {}
        for key, item in value.items():
            new_key = NEW_PATCH if key == OLD_PATCH else key
            if new_key != key:
                changes += 1
            migrated, count = migrate(item, key)
            changes += count
            if new_key in output and isinstance(output[new_key], dict) and isinstance(migrated, dict):
                output[new_key].update(migrated)
            else:
                output[new_key] = migrated
        return output, changes

    if isinstance(value, list):
        output: list[Any] = []
        for item in value:
            if parent_key == "blocked_path_patterns" and str(item).strip().casefold() == "/troll/":
                changes += 1
                continue
            migrated, count = migrate(item, parent_key)
            changes += count
            if migrated == OLD_PATCH:
                migrated = NEW_PATCH
                changes += 1
            if migrated not in output:
                output.append(migrated)
            elif migrated != item:
                changes += 1
        return output, changes

    if isinstance(value, str) and value == OLD_PATCH:
        return NEW_PATCH, 1
    return value, 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail when migration is still required")
    args = parser.parse_args()

    total = 0
    results: list[tuple[Path, Any, int]] = []
    for path in TARGET_FILES:
        original = load(path)
        migrated, changes = migrate(original)
        if changes and isinstance(migrated, dict) and isinstance(migrated.get("schema_version"), int):
            migrated["schema_version"] += 1
        total += changes
        results.append((path, migrated, changes))

    if args.check:
        if total:
            print(f"global HLS override policy requires {total} migration(s)")
            return 1
        print("global HLS override policy is normalized")
        return 0

    for path, migrated, changes in results:
        if changes:
            dump(path, migrated)
            print(f"normalized {path.relative_to(ROOT)}: {changes} change(s)")
    if not total:
        print("global HLS override policy already normalized")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
