#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Compatibility entrypoint for an in-flight Deep publisher.

The canonical finite audit is audit_catalogue_identity_media.py. This adapter
only translates the retired argument-based workflow contract into that audit's
environment contract; it does not duplicate audit or quarantine policy.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / "scripts" / "audit_catalogue_identity_media.py"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--stage", type=Path, required=True)
    parser.add_argument("--health", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    required = {
        "manifest": args.manifest,
        "stage candidates": args.stage / "candidates.json",
        "health evidence": args.health,
        "canonical auditor": CANONICAL,
    }
    missing = [f"{label}: {path}" for label, path in required.items() if not path.is_file()]
    if missing:
        print("legacy catalogue audit compatibility failed:", file=sys.stderr)
        for item in missing:
            print(f"- missing {item}", file=sys.stderr)
        return 2

    env = dict(os.environ)
    env["NUVIO_CATALOGUE_AUDIT_OUTPUT"] = str(args.output.resolve())
    completed = subprocess.run([sys.executable, str(CANONICAL)], cwd=ROOT, env=env, check=False)
    return int(completed.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
