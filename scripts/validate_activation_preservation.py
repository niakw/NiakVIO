#!/usr/bin/env python3
"""Prevent automated releases from silently shrinking the provider set."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "provider-activation-lkg.json"
MAIN = ROOT / "manifest.json"
VF = ROOT / "vf" / "manifest.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def rows(data: dict) -> dict[str, dict]:
    return {
        str(row.get("id") or "").casefold(): row
        for row in data.get("scrapers") or []
        if isinstance(row, dict) and str(row.get("id") or "").strip()
    }


def validate() -> list[str]:
    policy = load(POLICY)
    main_rows = rows(load(MAIN))
    vf_rows = rows(load(VF))
    expected = {str(value).casefold() for value in policy.get("active_ids") or []}
    minimum = int(policy.get("minimum_enabled_count") or len(expected))
    active = {provider_id for provider_id, row in main_rows.items() if row.get("enabled") is True}

    errors: list[str] = []
    missing_entries = sorted(expected - set(main_rows))
    if missing_entries:
        errors.append("activation LKG providers missing from manifest: " + ", ".join(missing_entries))

    disabled = sorted(expected - active)
    if disabled:
        errors.append("activation LKG providers were disabled: " + ", ".join(disabled))

    if len(active) < minimum:
        errors.append(f"enabled provider count regressed: {len(active)} < {minimum}")

    mismatched = sorted(
        provider_id
        for provider_id in set(main_rows) & set(vf_rows)
        if bool(main_rows[provider_id].get("enabled")) != bool(vf_rows[provider_id].get("enabled"))
    )
    if mismatched:
        errors.append("main/VF activation mismatch: " + ", ".join(mismatched))

    manual_disabled = {str(value).casefold() for value in (policy.get("manual_disabled") or {})}
    unexpectedly_enabled = sorted(manual_disabled & active)
    if unexpectedly_enabled:
        errors.append("manually disabled providers were re-enabled: " + ", ".join(unexpectedly_enabled))

    return errors


def main() -> int:
    errors = validate()
    if errors:
        raise SystemExit("provider activation preservation failed:\n- " + "\n- ".join(errors))
    active_count = sum(
        1 for row in rows(load(MAIN)).values() if row.get("enabled") is True
    )
    print(f"provider activation preservation passed ({active_count} enabled)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
