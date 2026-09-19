#!/usr/bin/env python3
"""Experimental fast wrapper: prove V16 before the existing targeted runner.

Not a publication gate. V16 is promoted into the canonical pipeline only after a
positive targeted proof and full portfolio preservation.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import run_provider_repair_fast_targeted_v1 as v1  # noqa: E402


def main() -> int:
    subprocess.run([sys.executable, str(ROOT / "scripts" / "upgrade_provider_route_slug_identity_v16.py")], cwd=ROOT, check=True)
    subprocess.run([sys.executable, str(ROOT / "tests" / "provider_route_slug_identity_v16_test.py")], cwd=ROOT, check=True)
    return v1.main()


if __name__ == "__main__":
    raise SystemExit(main())
