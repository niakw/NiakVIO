#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Fail-closed Nuvio client runtime-contract guard before provider Brain mutation."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts/check_nuvio_client_upstreams.py"


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected object")
    return value


def guard(output: Path) -> dict[str, Any]:
    if os.environ.get("NIAKVIO_SKIP_CLIENT_DRIFT_GUARD", "0").strip() == "1":
        return {"skipped": True, "reason": "explicit_test_override"}

    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(
        [sys.executable, str(CHECKER), "--output", str(output)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=240,
        check=False,
    )
    if completed.returncode != 0:
        details = "\n".join(part.strip() for part in (completed.stdout, completed.stderr) if part and part.strip())
        raise RuntimeError(f"Nuvio client runtime contract drift blocks provider Brain mutation: {details[-2200:]}")
    report = load_json(output)
    inconclusive = [str(value) for value in report.get("inconclusive") or [] if str(value)]
    review = [str(value) for value in report.get("review_required") or [] if str(value)]
    if review:
        raise RuntimeError("Nuvio client runtime re-audit required before provider Brain mutation: " + ", ".join(review))
    if inconclusive:
        raise RuntimeError("Nuvio client runtime verification is inconclusive; fail-closed before provider Brain mutation: " + ", ".join(inconclusive))
    print(
        "FIELD_NUVIO_CLIENT_BRAIN_COMPAT "
        f"verified={len(report.get('verified') or [])} safe_advance={len(report.get('safe_advance_available') or [])} "
        "review_required=0 inconclusive=0 provider_mutation_allowed=true"
    )
    return report


def main() -> int:
    output = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "health-output/nuvio-client-upstream-status.json"
    guard(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
