#!/usr/bin/env python3
"""Portfolio preservation gate with stream-level wrong-content classification."""
from __future__ import annotations

import compare_quick_yield_preservation_impl as impl

_original_load = impl.load


def accepted_verified_stream(row: dict) -> bool:
    return int(row.get("playable") or 0) > 0 and int(row.get("verified") or 0) > 0


def normalize_report(report: dict) -> dict:
    value = dict(report)
    terminal_wrong: set[str] = set()
    for row in report.get("rows") or []:
        if not isinstance(row, dict):
            continue
        provider = str(row.get("provider_id") or row.get("provider") or "").strip().casefold()
        contradictions = int(row.get("contradictions") or 0)
        if provider and contradictions > 0 and not accepted_verified_stream(row):
            terminal_wrong.add(provider)
    # Old reports without rows retain their declared summary for compatibility.
    if isinstance(report.get("rows"), list):
        value["wrong_content_providers"] = sorted(terminal_wrong)
    return value


def load(path: str) -> dict:
    return normalize_report(_original_load(path))


impl.load = load


def main() -> int:
    return impl.main()


if __name__ == "__main__":
    raise SystemExit(main())
