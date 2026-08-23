#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Materialize fail-closed rebuild safety around provider-derived bytes.

Minifiers may preserve NUVIO comments while moving or reformatting their owning
statements. Comments alone therefore never authorize deleting bytes through a
later wrapper terminator; relocated metadata is stripped without touching the
provider body. This normalizer protects wrapper isolation, wires the durable
``core_rebuild_safety`` parser into the owning fixed-point normalizer, owns
canonical single-newline separation for the global HLS runtime hook, and keeps
provider rebuild transitions observable when a content-addressed fixed point
fails to converge.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from textwrap import dedent

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts" / "provider_engine_normalizer.py"
REAPPLY = ROOT / "scripts" / "reapply_published_overrides.py"
CORE_NORMALIZER = ROOT / "scripts" / "normalize_core_fixed_point_contract.py"
CORE_MATERIALIZER = ROOT / "scripts" / "materialize_core_fixed_point_hardening.py"
CORE_SAFETY = ROOT / "scripts" / "core_rebuild_safety.py"
HLS_RUNTIME = ROOT / "scripts" / "provider_patches" / "hls_runtime_integrity_v1.py"
CORE_HARDENING_MARKER = "return harden_generated_apply(text)"
REAPPLY_DIAGNOSTIC_MARKER = "FIELD_PROVIDER_REF_CHANGES"
REAPPLY_DIAGNOSTIC_STOP_MARKER = "FIELD_PROVIDER_REF_DIAGNOSTIC_STOP"

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


def normalized_hls(text: str) -> str:
    """Make HLS wrapper insertion byte-stable across Core/Terser reapplication."""
    expected_occurrences = 2
    current_occurrences = text.count("wrapper.rstrip()")
    if current_occurrences not in (0, expected_occurrences):
        raise ValueError(
            f"unexpected HLS wrapper separator shape: wrapper.rstrip occurrences={current_occurrences}"
        )
    return text.replace("wrapper.rstrip()", "wrapper.strip()")


def normalized_reapply_diagnostics(text: str) -> str:
    """Expose exact content-addressed transitions without changing publication bytes."""
    if REAPPLY_DIAGNOSTIC_MARKER not in text:
        anchor = '''    print(
        f"published overrides reapplied: patched={applied_count}, "
'''
        if anchor not in text:
            raise ValueError("published override summary anchor missing")
        block = '''    changed_provider_rows = sorted(
        (provider_id, old, new)
        for provider_id, (old, new) in updates.items()
        if old != new
    )
    if changed_provider_rows:
        print(
            "FIELD_PROVIDER_REF_CHANGES "
            f"count={len(changed_provider_rows)} ids={','.join(row[0] for row in changed_provider_rows)}"
        )
        print(
            "FIELD_PROVIDER_REF_TRANSITIONS values="
            + ",".join(
                f"{provider_id}:{Path(old).stem.rsplit('--', 1)[-1][:16]}>"
                f"{Path(new).stem.rsplit('--', 1)[-1][:16]}"
                for provider_id, old, new in changed_provider_rows
            )
        )
'''
        text = text.replace(anchor, block + anchor, 1)
    if REAPPLY_DIAGNOSTIC_STOP_MARKER not in text:
        anchor = '''    print(
        f"published overrides reapplied: patched={applied_count}, "
'''
        stop = '''    if 0 < len(changed_provider_rows) <= 13 and (ROOT / ".provider-fixed-point-diagnostic").is_file():
        print(
            "FIELD_PROVIDER_REF_DIAGNOSTIC_STOP "
            f"count={len(changed_provider_rows)} ids={','.join(row[0] for row in changed_provider_rows)}"
        )
        return 86
'''
        text = text.replace(anchor, stop + anchor, 1)
    return text


def _materialize_core_hardening() -> None:
    if not CORE_SAFETY.is_file():
        raise SystemExit("durable Core rebuild safety module is missing")
    if not CORE_MATERIALIZER.is_file():
        raise SystemExit("durable Core fixed-point materializer is missing")
    if CORE_HARDENING_MARKER in CORE_NORMALIZER.read_text(encoding="utf-8"):
        return
    subprocess.run([sys.executable, str(CORE_MATERIALIZER)], cwd=ROOT, check=True)
    if CORE_HARDENING_MARKER not in CORE_NORMALIZER.read_text(encoding="utf-8"):
        raise SystemExit("Core fixed-point hardening did not materialize")


def _materialize_reapply_diagnostics() -> bool:
    current = REAPPLY.read_text(encoding="utf-8")
    expected = normalized_reapply_diagnostics(current)
    changed = current != expected
    if changed:
        REAPPLY.write_text(expected, encoding="utf-8")
    (ROOT / ".provider-fixed-point-diagnostic").write_text("diagnostic-only\n", encoding="utf-8")
    return changed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.apply == args.check:
        parser.error("choose exactly one of --apply or --check")

    diagnostics_changed = False
    if args.apply:
        _materialize_core_hardening()
        diagnostics_changed = _materialize_reapply_diagnostics()
    elif not CORE_SAFETY.is_file() or CORE_HARDENING_MARKER not in CORE_NORMALIZER.read_text(encoding="utf-8"):
        raise SystemExit("Core fixed-point bounded parser is not materialized")

    current = TARGET.read_text(encoding="utf-8")
    expected = normalized(current)
    hls_current = HLS_RUNTIME.read_text(encoding="utf-8")
    hls_expected = normalized_hls(hls_current)
    if args.check:
        if current != expected:
            raise SystemExit("provider rebuild safety contract is not materialized")
        if hls_current != hls_expected:
            raise SystemExit("HLS wrapper separator fixed-point contract is not materialized")
        required = (
            're.match(r"\\s*;?\\s*\\(\\s*function\\b", region, re.I)',
            'r"\\b(?:var|let|const)\\s+__provider\\b"',
            'r"\\bmodule\\.exports\\s*=\\s*__provider\\b"',
        )
        for needle in required:
            if needle not in current:
                raise SystemExit(f"missing provider rebuild safety guard: {needle}")
        if hls_current.count("wrapper.strip()") != 2 or "wrapper.rstrip()" in hls_current:
            raise SystemExit("HLS wrapper separator must be owned by one explicit newline")
        print("provider rebuild safety contract verified")
        return 0

    changed = diagnostics_changed
    if current != expected:
        TARGET.write_text(expected, encoding="utf-8")
        changed = True
    if hls_current != hls_expected:
        HLS_RUNTIME.write_text(hls_expected, encoding="utf-8")
        changed = True
    if changed:
        print("provider rebuild safety contract materialized")
    else:
        print("provider rebuild safety contract already materialized")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
