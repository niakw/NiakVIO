#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "tests" / "overrides_test.py"


def main() -> int:
    text = PATH.read_text(encoding="utf-8")
    old = '''def test_domain_overrides() -> None:
    source = b"const BASE='https://french-stream.one';"
    output, patch_records = apply_overrides("frenchstream", source)
    # The stable domain migration is still recorded during discovery, but the
    # terminal safety patch deliberately replaces the whole artifact with an
    # inert provider while Frenchstream is quarantined.
    assert b"NUVIO_PROVIDER_QUARANTINE_V1" in output
    assert b"french-stream.one" not in output
    assert any(
        row.get("from") == "french-stream.one"
        and row.get("to") == "fs16.lol"
        for row in patch_records
    )
'''
    new = '''def test_domain_overrides() -> None:
    source = b"const BASE='https://french-stream.one';"
    output, patch_records = apply_overrides("frenchstream", source)
    # A configured terminal safety quarantine replaces the provider with an
    # inert artifact. Historical route/domain mappings are intentionally pruned
    # from terminal quarantines so a later reapply cannot resurrect a stale
    # repair path. Domain replacement behavior remains covered by active
    # providers such as Movix and Flemmix below.
    assert b"NUVIO_PROVIDER_QUARANTINE_V1" in output
    assert b"french-stream.one" not in output
    assert not any(
        row.get("type") == "replace"
        and row.get("from") == "french-stream.one"
        for row in patch_records
    )
'''
    if old in text:
        text = text.replace(old, new, 1)
    elif new not in text:
        raise SystemExit("terminal quarantine domain test anchor missing")
    PATH.write_text(text, encoding="utf-8")
    print("terminal quarantine override test contract patched")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
