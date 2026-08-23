#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Materialize fail-closed rebuild safety around provider-derived bytes.

Minifiers may preserve NUVIO comments while moving or reformatting their owning
statements. Comments alone therefore never authorize deleting bytes through a
later wrapper terminator. This normalizer protects wrapper isolation and wires
the durable ``core_rebuild_safety`` parser into the owning fixed-point normalizer
before it generates publication code.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from textwrap import dedent

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts" / "provider_engine_normalizer.py"
CORE_NORMALIZER = ROOT / "scripts" / "normalize_core_fixed_point_contract.py"
CORE_MIGRATION = ROOT / "scripts" / "harden_core_fixed_point_normalizer_once.py"
CORE_SAFETY = ROOT / "scripts" / "core_rebuild_safety.py"
CORE_HARDENING_MARKER = "return harden_generated_apply(text)"

SAFE_FUNCTION = dedent(r'''
def _owned_wrapper_end(text: str, marker_end: int, limit: int) -> int | None:
    """Return an exact owned IIFE end without ever crossing provider bytes.

    Preserved comments are not structural boundaries: Terser or another formatter
    may relocate them. A marker is accepted only when the following non-whitespace
    bytes begin an IIFE and the candidate span contains no provider declaration or
    export bridge. Ambiguous shapes fail closed and remain untouched.
    """
    region = text[marker_end:limit]
    if not re.match(r"\s*;?\s*\(\s*function\b", region, re.I):
        return None

    candidate_end: int | None = None
    global_call = GLOBAL_WRAPPER_CALL_RE.search(region)
    if global_call:
        call_start = marker_end + global_call.start()
        end = text.find(");", call_start, limit)
        if end >= 0:
            candidate_end = end + 2
    if candidate_end is None:
        empty_call = EMPTY_IIFE_END_RE.search(region)
        if empty_call:
            candidate_end = marker_end + empty_call.end()
    if candidate_end is None:
        return None

    candidate = text[marker_end:candidate_end]
    protected = (
        r"\b(?:var|let|const)\s+__provider\b",
        r"\bmodule\.exports\s*=\s*__provider\b",
        r"\b(?:globalThis|global|self)\.getStreams\s*=\s*__provider\.getStreams\b",
    )
    if any(re.search(pattern, candidate) for pattern in protected):
        return None
    return candidate_end
''').lstrip("\n")


def normalized(text: str) -> str:
    start = text.index("def _owned_wrapper_end(")
    end = text.index("\ndef strip_foreign_provider_wrappers(", start)
    return text[:start] + SAFE_FUNCTION + text[end:]


def _materialize_core_hardening() -> None:
    if not CORE_SAFETY.is_file():
        raise SystemExit("durable Core rebuild safety module is missing")
    if CORE_HARDENING_MARKER in CORE_NORMALIZER.read_text(encoding="utf-8"):
        return
    subprocess.run([sys.executable, str(CORE_MIGRATION)], cwd=ROOT, check=True)
    if CORE_HARDENING_MARKER not in CORE_NORMALIZER.read_text(encoding="utf-8"):
        raise SystemExit("Core fixed-point hardening migration did not materialize")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.apply == args.check:
        parser.error("choose exactly one of --apply or --check")

    if args.apply:
        _materialize_core_hardening()
    elif not CORE_SAFETY.is_file() or CORE_HARDENING_MARKER not in CORE_NORMALIZER.read_text(encoding="utf-8"):
        raise SystemExit("Core fixed-point bounded parser is not materialized")

    current = TARGET.read_text(encoding="utf-8")
    expected = normalized(current)
    if args.check:
        if current != expected:
            raise SystemExit("provider rebuild safety contract is not materialized")
        required = (
            're.match(r"\\s*;?\\s*\\(\\s*function\\b", region, re.I)',
            'r"\\b(?:var|let|const)\\s+__provider\\b"',
            'r"\\bmodule\\.exports\\s*=\\s*__provider\\b"',
        )
        for needle in required:
            if needle not in current:
                raise SystemExit(f"missing provider rebuild safety guard: {needle}")
        print("provider rebuild safety contract verified")
        return 0

    if current != expected:
        TARGET.write_text(expected, encoding="utf-8")
        print("provider rebuild safety contract materialized")
    else:
        print("provider rebuild safety contract already materialized")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
