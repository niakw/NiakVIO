#!/usr/bin/env python3
"""Keep the final Core provider tail ordered and runtime-portable.

Runtime compatibility executes first, stream presentation second, and provider
branding last. The legacy filename is retained because it is part of the current
fixed-point pipeline; the implementation now guards the complete Core tail.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from normalize_core_runtime_compat import (
    assert_apply_contract as assert_runtime_contract,
    normalize_apply as normalize_runtime_apply,
    normalize_files as normalize_runtime_files,
)

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts/apply_provider_overrides.py"
CONST = 'GLOBAL_PROVIDER_BRANDING = "scripts/provider_patches/global_provider_branding_v1.py"'
PRESENTATION_CONST = 'GLOBAL_STREAM_PRESENTATION = "scripts/provider_patches/global_stream_presentation_v1.py"'
BRANDING_MARKER = '    "NUVIO_GLOBAL_PROVIDER_BRANDING_V1",\n'
PRESENTATION_MARKER = '    "NUVIO_GLOBAL_STREAM_PRESENTATION_V1",\n'
ANCHOR = '''        if text != before:
            applied.append({
                "type": "patch_script",
                "path": GLOBAL_STREAM_PRESENTATION,
                "phase": phase,
                "scope": "global_stream_presentation",
            })

    if text == original_text:
'''
REPLACEMENT = '''        if text != before:
            applied.append({
                "type": "patch_script",
                "path": GLOBAL_STREAM_PRESENTATION,
                "phase": phase,
                "scope": "global_stream_presentation",
            })

        # Provider branding is deliberately the final Core stream layer. Upstream
        # stream names can contain quality/language/codec facts; presentation must
        # read those originals before the committed emoji/name replaces the local
        # row label and title prefix.
        before = text
        text = _apply_patch_script(text, provider_id, GLOBAL_PROVIDER_BRANDING, {}, None)
        if text != before:
            applied.append({
                "type": "patch_script",
                "path": GLOBAL_PROVIDER_BRANDING,
                "phase": phase,
                "scope": "global_provider_branding",
            })

    if text == original_text:
'''


def normalize(text: str) -> tuple[str, list[str]]:
    text, runtime_changes = normalize_runtime_apply(text)
    changed: list[str] = [f"runtime:{item}" for item in runtime_changes]

    if CONST not in text:
        if PRESENTATION_CONST not in text:
            raise ValueError("GLOBAL_STREAM_PRESENTATION constant anchor missing")
        text = text.replace(PRESENTATION_CONST, PRESENTATION_CONST + "\n" + CONST, 1)
        changed.append("branding_constant")

    if BRANDING_MARKER not in text:
        if PRESENTATION_MARKER not in text:
            raise ValueError("generated Core tail presentation marker anchor missing")
        text = text.replace(PRESENTATION_MARKER, PRESENTATION_MARKER + BRANDING_MARKER, 1)
        changed.append("branding_tail_marker")

    if '"scope": "global_provider_branding"' not in text:
        if ANCHOR not in text:
            raise ValueError("global presentation application anchor missing")
        text = text.replace(ANCHOR, REPLACEMENT, 1)
        changed.append("post_presentation_branding")
    return text, changed


def assert_contract(text: str) -> None:
    assert_runtime_contract(text)
    if text.count(CONST) != 1:
        raise ValueError("GLOBAL_PROVIDER_BRANDING constant must exist exactly once")
    if text.count('"scope": "global_provider_branding"') != 1:
        raise ValueError("global provider branding application must exist exactly once")
    runtime = text.find('"scope": "global_runtime_compat"')
    presentation = text.find('"scope": "global_stream_presentation"')
    branding = text.find('"scope": "global_provider_branding"')
    final_return = text.find("    if text == original_text:", branding)
    if min(runtime, presentation, branding, final_return) < 0 or not (runtime < presentation < branding < final_return):
        raise ValueError("Core order must be runtime compatibility -> stream presentation -> provider branding -> return")
    if text.count(BRANDING_MARKER) != 1:
        raise ValueError("provider branding generated-tail marker must exist exactly once")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.apply == args.check:
        raise SystemExit("choose exactly one of --apply or --check")

    current = TARGET.read_text(encoding="utf-8")
    normalized, changed = normalize(current)
    assert_contract(normalized)
    if args.apply and normalized != current:
        TARGET.write_text(normalized, encoding="utf-8")

    runtime_file_changes = normalize_runtime_files(apply=args.apply)
    all_changes = changed + [f"runtime_file:{item}" for item in runtime_file_changes if not item.startswith("apply:")]
    if args.check and all_changes:
        raise SystemExit("Core tail pipeline normalization required: " + ", ".join(all_changes))

    print(
        "FIELD_PROVIDER_BRANDING_PIPELINE "
        f"changed={len(all_changes)} order=runtime_then_presentation_then_branding "
        "facts_preserved=true runtime_portable=true brain_systemic_guard=true"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
