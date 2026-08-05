#!/usr/bin/env python3
"""Restore the validated activation union without reverting provider code."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "provider-activation-lkg.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def bump_patch(value: object) -> str:
    match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", str(value or ""))
    if not match:
        return "1.0.1"
    major, minor, patch = map(int, match.groups())
    return f"{major}.{minor}.{patch + 1}"


def restore(path: Path, expected: set[str], *, require_all: bool) -> tuple[list[str], list[str], set[str]]:
    data = load(path)
    found: set[str] = {
        str(row.get("id") or "").casefold()
        for row in data.get("scrapers") or []
        if isinstance(row, dict) and str(row.get("id") or "").strip()
    }
    applicable = expected if require_all else expected & found
    enabled_now: list[str] = []
    disabled_now: list[str] = []

    for row in data.get("scrapers") or []:
        if not isinstance(row, dict):
            continue
        provider_id = str(row.get("id") or "").casefold()
        if not provider_id:
            continue
        desired = provider_id in applicable
        current = row.get("enabled") is True
        if current == desired:
            continue
        row["enabled"] = desired
        row["version"] = bump_patch(row.get("version"))
        (enabled_now if desired else disabled_now).append(provider_id)

    if require_all:
        missing = sorted(expected - found)
        if missing:
            raise RuntimeError(f"{path}: activation union providers missing: {missing}")

    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return sorted(enabled_now), sorted(disabled_now), applicable


def main() -> int:
    policy = load(POLICY)
    expected = {str(value).casefold() for value in policy.get("active_ids") or []}
    if len(expected) != int(policy.get("minimum_enabled_count") or 0):
        raise RuntimeError("activation policy count does not match unique active_ids")

    main_enabled, main_disabled, _main_expected = restore(
        ROOT / "manifest.json", expected, require_all=True
    )
    vf_enabled, vf_disabled, vf_expected = restore(
        ROOT / "vf" / "manifest.json", expected, require_all=False
    )

    main = load(ROOT / "manifest.json")
    main_count = sum(1 for row in main.get("scrapers") or [] if row.get("enabled") is True)
    if main_count != len(expected):
        raise RuntimeError(f"restored main enabled count is {main_count}, expected {len(expected)}")

    vf = load(ROOT / "vf" / "manifest.json")
    vf_count = sum(1 for row in vf.get("scrapers") or [] if row.get("enabled") is True)
    if vf_count != len(vf_expected):
        raise RuntimeError(f"restored VF enabled count is {vf_count}, expected {len(vf_expected)}")

    print("reactivated main:", ", ".join(main_enabled) or "none")
    print("disabled main:", ", ".join(main_disabled) or "none")
    print("reactivated vf:", ", ".join(vf_enabled) or "none")
    print("disabled vf:", ", ".join(vf_disabled) or "none")
    print(f"restored activation union: main={main_count}, vf={vf_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
