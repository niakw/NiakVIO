#!/usr/bin/env python3
"""Compatibility shim: production Nuvio runtime instrumentation is disabled.

Native labs are human-UX observation only. They may not patch Nuvio production
source code to gain extra logging. Keep this historical entry point so old suite
references are harmless; evidence must come from NiakVIO-owned test code, official
Nuvio logs already emitted by the client, or external process output.
"""
from __future__ import annotations

import argparse
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("client", choices=("tv", "mobile"))
    parser.add_argument("repo")
    args = parser.parse_args()
    repo = Path(args.repo).resolve()
    if not (repo / ".git").exists():
        raise SystemExit(f"official Nuvio checkout missing: {repo}")
    print(
        f"FIELD_NATIVE_RUNTIME_INSTRUMENTATION client={args.client} "
        "status=disabled_by_human_ux_policy runtime_mutation=false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
