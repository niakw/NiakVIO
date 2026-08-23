#!/usr/bin/env python3
"""Audit provider publication fixed-point convergence with actionable provider IDs.

This is intentionally non-mutating outside its disposable CI checkout. It runs the
same Core preparation steps, records which content-addressed provider references
change on each pass, and fails early when the exact stale set repeats.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manifest.json"
REAPPLY = ROOT / "scripts" / "reapply_published_overrides.py"


def run(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *args], cwd=ROOT, text=True, check=check,
    )


def refs() -> dict[str, str]:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    return {
        str(row.get("id") or "").strip().casefold(): str(row.get("filename") or "")
        for row in data.get("scrapers") or []
        if isinstance(row, dict) and row.get("id")
    }


def main() -> int:
    run("scripts/normalize_core_media_policy.py", "--apply")
    run("scripts/apply_runtime_capability_upgrade_v4.py")
    run("scripts/build_provider_runtime_profiles.py")

    previous_stale: tuple[str, ...] | None = None
    for pass_no in range(1, 5):
        before = refs()
        run(str(REAPPLY))
        after = refs()
        changed = tuple(sorted(pid for pid in set(before) | set(after) if before.get(pid) != after.get(pid)))
        print(
            "FIELD_PROVIDER_FIXED_POINT_PASS "
            f"pass={pass_no} changed_count={len(changed)} ids={','.join(changed) or '-'}",
            flush=True,
        )
        checked = run(str(REAPPLY), "--check", check=False)
        if checked.returncode == 0:
            print(f"FIELD_PROVIDER_FIXED_POINT_RESULT status=converged pass={pass_no}", flush=True)
            return 0
        if previous_stale is not None and changed == previous_stale:
            print(
                "FIELD_PROVIDER_FIXED_POINT_RESULT status=stagnant "
                f"pass={pass_no} changed_count={len(changed)} ids={','.join(changed)}",
                flush=True,
            )
            return 3
        previous_stale = changed

    print(
        "FIELD_PROVIDER_FIXED_POINT_RESULT status=nonconvergent "
        f"changed_count={len(previous_stale or ())} ids={','.join(previous_stale or ())}",
        flush=True,
    )
    return 4


if __name__ == "__main__":
    raise SystemExit(main())
