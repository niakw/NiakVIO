#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "automation" / "mobile-vf-runtime.json"
POLICY = ROOT / "automation" / "mobile-vf-runtime-policy.json"
CROSS_POLICY = ROOT / "automation" / "platform-runtime-policy.json"
MAIN = ROOT / "manifest.json"
VF = ROOT / "vf" / "manifest.json"


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def rows(document: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(row.get("id") or "").casefold(): row
        for row in document.get("scrapers") or []
        if isinstance(row, dict) and str(row.get("id") or "").strip()
    }


def android_disabled(row: dict[str, Any]) -> bool:
    return "android" in {str(value).casefold() for value in row.get("disabledPlatforms") or []}


def main() -> int:
    # From 5.20.28 onward Android is one slice of the conservative cross-platform
    # policy. Delegate to the stronger validator so this historical entry point
    # cannot re-impose the old "no proof == disabled" rule.
    if CROSS_POLICY.is_file():
        process = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "validate_platform_runtime_policy.py")],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        if process.returncode != 0:
            raise SystemExit(process.stderr or process.stdout or "cross-platform runtime validation failed")
        print("Android runtime policy validated via cross-platform policy")
        return 0

    # Legacy 5.20.27 validation remains available only until the cross-platform
    # policy is first published.
    report = load(REPORT)
    policy = load(POLICY)
    main_doc = load(MAIN)
    vf_doc = load(VF)
    main_rows = rows(main_doc)
    vf_rows = rows(vf_doc)
    report_rows = {
        str(row.get("id") or "").casefold(): row
        for row in report.get("providers") or []
        if isinstance(row, dict) and str(row.get("id") or "").strip()
    }
    errors: list[str] = []
    proven = {provider_id for provider_id, row in report_rows.items() if row.get("android_direct_movie_proof") is True}
    for provider_id, evidence in sorted(report_rows.items()):
        main_row = main_rows.get(provider_id)
        if main_row is None:
            continue
        should_disable = evidence.get("android_direct_movie_proof") is not True
        if android_disabled(main_row) != should_disable:
            errors.append(f"{provider_id}: legacy main Android state mismatch")
        vf_row = vf_rows.get(provider_id)
        if vf_row is not None and android_disabled(vf_row) != should_disable:
            errors.append(f"{provider_id}: legacy VF Android state mismatch")
    if sorted(policy.get("android_direct_movie_proven") or []) != sorted(proven):
        errors.append("legacy policy/report proof mismatch")
    if errors:
        raise SystemExit("legacy Android runtime policy validation failed:\n- " + "\n- ".join(errors))
    print("legacy Android runtime policy validated pending cross-platform publication")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
