#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""One-shot migration wiring durable Core rebuild safety into its owner."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts" / "normalize_core_fixed_point_contract.py"
IMPORT = "from core_rebuild_safety import harden_generated_apply\n"
MARKER = "return harden_generated_apply(text)"


def main() -> int:
    text = TARGET.read_text(encoding="utf-8")
    changed = False

    if IMPORT not in text:
        anchor = "from textwrap import dedent\n"
        if anchor not in text:
            raise SystemExit("fixed-point normalizer import anchor missing")
        text = text.replace(anchor, anchor + IMPORT, 1)
        changed = True

    if MARKER not in text:
        tail = "    return text\n\n\ndef normalize_reapply(text: str) -> str:\n"
        replacement = "    return harden_generated_apply(text)\n\n\ndef normalize_reapply(text: str) -> str:\n"
        if tail not in text:
            raise SystemExit("normalize_apply return anchor missing")
        text = text.replace(tail, replacement, 1)
        changed = True

    if changed:
        TARGET.write_text(text, encoding="utf-8")
        print("Core fixed-point normalizer hardened through core_rebuild_safety")
    else:
        print("Core fixed-point normalizer hardening already materialized")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
