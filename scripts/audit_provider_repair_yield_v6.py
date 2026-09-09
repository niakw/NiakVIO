#!/usr/bin/env python3
"""Repair-yield gate with stream-level mixed-identity acceptance.

A lane is identity-safe when it has at least one playable verified stream, even if
other returned candidates were correctly rejected as contradictions. Rejected
candidates never become accepted output; they simply no longer poison the whole
provider lane. A lane with contradictions and zero verified playable streams
remains wrong-content/fail-closed.
"""
from __future__ import annotations

import audit_provider_repair_yield_v6_impl as impl


def accepted_verified_stream(row: dict) -> bool:
    return int(row.get("playable") or 0) > 0 and int(row.get("verified") or 0) > 0


def identity_safe(row: dict) -> bool:
    if accepted_verified_stream(row):
        return True
    return int(row.get("contradictions") or 0) == 0 and str(row.get("status") or "") != "wrong_content"


impl.identity_safe = identity_safe


def main() -> int:
    return impl.main()


if __name__ == "__main__":
    raise SystemExit(main())
