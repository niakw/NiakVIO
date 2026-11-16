#!/usr/bin/env python3
"""Compatibility entry point for the retired identity-only ProviderBase migration.

Historical automation may still reference this path, so keep the entry point
available but remove its former authority. It must never reconstruct from the
Global manifest alone or replay the old runtime-v5 migration in isolation.

The only current ProviderBase materialization authority is
`scripts/materialize_provider_base_v3_store.py`, which derives the active
Global+France projection union, applies the cumulative current runtime
preparation, and persists the canonical ProviderBase store/provenance.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANONICAL_MATERIALIZER = ROOT / "scripts" / "materialize_provider_base_v3_store.py"


def main() -> int:
    if not CANONICAL_MATERIALIZER.is_file():
        raise SystemExit("canonical ProviderBase v3 materializer is missing")
    completed = subprocess.run(
        [sys.executable, str(CANONICAL_MATERIALIZER)],
        cwd=ROOT,
        check=False,
    )
    if completed.returncode:
        return int(completed.returncode)
    print(
        "IDENTITY_ONLY_PROVIDER_BASE_COMPAT "
        "retired=true canonical=materialize_provider_base_v3_store.py "
        "scope=Global+France"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
