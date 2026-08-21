#!/usr/bin/env python3
"""Non-mutating compatibility shim for native reader labs.

NiakVIO native-reader labs are human-UX observations. They must never patch,
harden, or otherwise modify the checked-out Nuvio application (or the host OS)
to improve test outcomes. Any Nuvio/OS setup, build, player-launch, or playback
failure must remain observable evidence and be classified as external unless a
NiakVIO-owned cause is demonstrated.

The workflow still invokes this historical entry point for compatibility, but
it intentionally performs no mutation.
"""

from __future__ import annotations

import argparse
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify the Nuvio checkout exists without modifying it."
    )
    parser.add_argument("project_root", help="Path to the checked-out Nuvio project")
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    if not root.is_dir():
        raise SystemExit(f"Nuvio project root does not exist: {root}")

    print(f"native-reader human-UX policy: leaving Nuvio checkout unchanged: {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
