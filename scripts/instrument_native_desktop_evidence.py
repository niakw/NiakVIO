#!/usr/bin/env python3
"""Compatibility shim: NuvioDesktop runtime instrumentation is disabled.

The native Desktop lab must observe the official runtime without patching
PluginRuntime, FetchBridge or any repository/network loader. This historical entry
point is retained only so old callers remain harmless and policy-compliant.
"""
from __future__ import annotations

import argparse
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("repo")
    args = parser.parse_args()
    repo = Path(args.repo).resolve()
    if not (repo / ".git").exists():
        raise SystemExit(f"official NuvioDesktop checkout missing: {repo}")
    print(
        "FIELD_NATIVE_RUNTIME_INSTRUMENTATION client=desktop "
        "status=disabled_by_human_ux_policy runtime_mutation=false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
