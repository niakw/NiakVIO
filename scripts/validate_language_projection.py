#!/usr/bin/env python3
"""Validate deterministic VF and no-anime manifest projections."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from generate_language_manifests import build_manifest, build_no_anime_manifest

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
    parser.add_argument("--no-anime", type=Path, default=ROOT / "no-anime" / "manifest.json")
    parser.add_argument("--vf-no-anime", type=Path, default=ROOT / "vf-no-anime" / "manifest.json")
    args = parser.parse_args()

    manifest = load(args.manifest.resolve())
    report = load(args.report.resolve())
    actual = load(args.vf.resolve())
    actual_no_anime = load(args.no_anime.resolve())
    actual_vf_no_anime = load(args.vf_no_anime.resolve())
    language_by_id = {
        str(item.get("id", "")).casefold(): str(item.get("manifest_ordering", {}).get("language_group", "other"))
        for item in report.get("providers", [])
        if isinstance(item, dict)
    }
    expected = build_manifest(manifest, language_by_id, {"vf"}, "VF uniquement")

    if actual != expected:
        expected_ids = ids(expected)
        actual_ids = ids(actual)
        expected_canonical = {value.casefold() for value in expected_ids}
        actual_canonical = {value.casefold() for value in actual_ids}
        missing = [value for value in expected_ids if value.casefold() not in actual_canonical]
        extra = [value for value in actual_ids if value.casefold() not in expected_canonical]
        order_mismatch = (
            not missing
            and not extra
            and [value.casefold() for value in expected_ids] != [value.casefold() for value in actual_ids]
        )
        details = [
            f"expected={len(expected_ids)} actual={len(actual_ids)}",
            f"missing={missing[:20]}",
            f"extra={extra[:20]}",
            f"order_mismatch={order_mismatch}",
            f"version_expected={expected.get('version')} version_actual={actual.get('version')}",
        ]
        raise SystemExit("VF projection validation failed: " + "; ".join(details))

    expected_no_anime = build_no_anime_manifest(manifest)
    expected_vf_no_anime = build_no_anime_manifest(expected)

    def validate_exact(label: str, actual_projection: dict[str, Any], expected_projection: dict[str, Any]) -> None:
        if actual_projection == expected_projection:
            return
        expected_ids = ids(expected_projection)
        actual_ids = ids(actual_projection)
        expected_canonical = {value.casefold() for value in expected_ids}
        actual_canonical = {value.casefold() for value in actual_ids}
        missing = [value for value in expected_ids if value.casefold() not in actual_canonical]
        extra = [value for value in actual_ids if value.casefold() not in expected_canonical]
        raise SystemExit(
            f"{label} projection validation failed: "
            f"expected={len(expected_ids)} actual={len(actual_ids)}; "
            f"missing={missing[:20]}; extra={extra[:20]}"
        )

    validate_exact("general no-anime", actual_no_anime, expected_no_anime)
    validate_exact("VF no-anime", actual_vf_no_anime, expected_vf_no_anime)

    enabled = sum(1 for row in actual.get("scrapers") or [] if isinstance(row, dict) and row.get("enabled") is True)
    print(
        f"VF projection validation passed (providers={len(ids(actual))}, enabled={enabled}); "
        f"no-anime projections passed (general={len(ids(actual_no_anime))}, vf={len(ids(actual_vf_no_anime))})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
