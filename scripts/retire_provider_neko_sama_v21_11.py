#!/usr/bin/env python3
"""V21.11 proof-first retirement guard for Neko-Sama.

The V21.11 slot was wired into the canonical Repair pipeline before an actual
migration existed.  Do not turn that wiring mistake into a destructive provider
retirement: Neko-Sama still has recent positive native fixture evidence in this
repository.  Terminal disable/off decisions belong to the proof-driven Repair
finalizer, not to an unconditional DATA migration.

This migration is therefore intentionally idempotent and non-destructive.  It
keeps the cumulative migration slot stable while making the safety decision
explicit.  A future retirement must replace this guard together with current,
authoritative terminal evidence and its own regression test.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROVIDER_ID = "neko-sama"
RETIREMENT_ALLOWED = False
REVISION = "v21.11-proof-first-retirement-guard"


def main() -> int:
    provider_files = sorted((ROOT / "providers").glob(f"{PROVIDER_ID}-*.js"))
    print(
        "FIELD_PROVIDER_RETIREMENT_GUARD "
        f"provider={PROVIDER_ID} revision={REVISION} "
        f"retirement_allowed={str(RETIREMENT_ALLOWED).lower()} "
        f"published_files={len(provider_files)} "
        "decision=preserve reason=no_authoritative_terminal_retirement_evidence",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
