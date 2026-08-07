#!/usr/bin/env python3
"""Validate that vf/manifest.json is the exact deterministic VF projection."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from generate_language_manifests import build_manifest

ROOT = Path(__file__).resolve().parents[1]


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def ids(manifest: dict[str, Any]) -> list[str]:
    return [
        str(row.get("id") or "")
        for row in manifest.get("scrapers") or []
        if isinstance(row, dict)
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=ROOT / "manifest.json")
    parser.add_argument("--report", type=Path, default=ROOT / "health-report.json")
    parser.add_argument("--vf", type=Path, default=ROOT / "vf" / "manifest.json")
    args = parser.parse_args()

    manifest = load(args.manifest.resolve())
    report = load(args.report.resolve())
    actual = load(args.vf.resolve())
    language_by_id = {
        str(item.get("id", "")): str(item.get("manifest_ordering", {}).get("language_group", "other"))
        for item in report.get("providers", [])
        if isinstance(item, dict)
    }
    expected = build_manifest(manifest, language_by_id, {"vf"}, "VF uniquement")

    if actual != expected:
        expected_ids = ids(expected)
        actual_ids = ids(actual)
        missing = [value for value in expected_ids if value not in set(actual_ids)]
        extra = [value for value in actual_ids if value not in set(expected_ids)]
        order_mismatch = not missing and not extra and expected_ids != actual_ids
        details = [
            f"expected={len(expected_ids)} actual={len(actual_ids)}",
            f"missing={missing[:20]}",
            f"extra={extra[:20]}",
            f"order_mismatch={order_mismatch}",
            f"version_expected={expected.get('version')} version_actual={actual.get('version')}",
        ]
        raise SystemExit("VF projection validation failed: " + "; ".join(details))

    enabled = sum(1 for row in actual.get("scrapers") or [] if isinstance(row, dict) and row.get("enabled") is True)
    print(f"VF projection validation passed (providers={len(ids(actual))}, enabled={enabled})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
