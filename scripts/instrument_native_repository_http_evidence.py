#!/usr/bin/env python3
"""Compatibility shim: repository HTTP runtime instrumentation is disabled.

Human-UX native labs must not inject interceptors into Nuvio production repository
or network loaders. Keep this entry point only so historical suite references are
safe and explicit. Repository evidence must be inferred from test-owned observation,
official logs or external process output without modifying Nuvio runtime code.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from audit_native_client_checkout import audit_checkout


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("client", choices=("tv", "mobile", "desktop"))
    parser.add_argument("repo")
    args = parser.parse_args()
    repo = Path(args.repo).resolve()
    if not (repo / ".git").exists():
        raise SystemExit(f"official Nuvio checkout missing: {repo}")
    audit_checkout(repo, args.client)
    print(
        f"FIELD_NATIVE_REPOSITORY_RUNTIME_INSTRUMENTATION client={args.client} "
        "status=disabled_by_human_ux_policy runtime_mutation=false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
