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
LEGACY_ASSERTION = '        "output = text[:existing_span[0]] + bootstrap + text[existing_span[1]:]",\n'
RUNTIME_ASSERTIONS = '''        "def _runtime_domain_span_matches_rules(candidate: str, rules: dict[str, str]) -> bool:",\n        "_strip_runtime_domain_orphan_calls(text, rules)",\n        "_runtime_domain_span_matches_rules(candidate, rules)",\n        "return text, 0 if text == original_text else max(1, orphan_count)",\n'''


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

    if LEGACY_ASSERTION in text:
        text = text.replace(LEGACY_ASSERTION, RUNTIME_ASSERTIONS, 1)
        changed = True
    elif RUNTIME_ASSERTIONS not in text:
        raise SystemExit("runtime-domain fixed-point assertion anchor is missing")

    if LEGACY_ASSERTION in text:
        raise SystemExit("obsolete runtime-domain replacement assertion remains")
    for required in (
        MARKER,
        "def _runtime_domain_span_matches_rules(candidate: str, rules: dict[str, str]) -> bool:",
        "_strip_runtime_domain_orphan_calls(text, rules)",
        "_runtime_domain_span_matches_rules(candidate, rules)",
        "return text, 0 if text == original_text else max(1, orphan_count)",
    ):
        if required not in text:
            raise SystemExit(f"missing durable Core fixed-point assertion: {required}")

    if changed:
        TARGET.write_text(text, encoding="utf-8")
        print("durable Core fixed-point hardening materialized")
    else:
        print("durable Core fixed-point hardening already materialized")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
