#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Materialize durable Core rebuild-safety wiring into the fixed-point normalizer."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts" / "normalize_core_fixed_point_contract.py"
IMPORT = "from core_rebuild_safety import harden_generated_apply\n"
IMPORT_ANCHOR = "from textwrap import dedent\n"
MARKER = "return harden_generated_apply(text)"
TAIL = "    return text\n\n\ndef normalize_reapply(text: str) -> str:\n"
REPLACEMENT = "    return harden_generated_apply(text)\n\n\ndef normalize_reapply(text: str) -> str:\n"


def main() -> int:
    text = TARGET.read_text(encoding="utf-8")
    changed = False

    if IMPORT not in text:
        if IMPORT_ANCHOR not in text:
            raise SystemExit("Core fixed-point import anchor is missing")
        text = text.replace(IMPORT_ANCHOR, IMPORT_ANCHOR + IMPORT, 1)
        changed = True

    if MARKER not in text:
        if TAIL not in text:
            raise SystemExit("Core fixed-point return anchor is missing")
        text = text.replace(TAIL, REPLACEMENT, 1)
        changed = True

    if changed:
        TARGET.write_text(text, encoding="utf-8")
        print("durable Core fixed-point hardening materialized")
    else:
        print("durable Core fixed-point hardening already materialized")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
