#!/usr/bin/env python3
"""Keep provider branding as the final Core stream presentation layer.

Branding must run after stream fact extraction/presentation: many upstream providers
encode quality/language/codec facts in their original stream name. Running the
branding wrapper earlier would erase those facts before the shared presentation
layer can normalize them. This normalizer materializes and then guards that ordering
inside apply_provider_overrides.py for every provider.
"""
from __future__ import annotations

import argparse
from pathlib import Path

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
    changed: list[str] = []
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
    if text.count(CONST) != 1:
        raise ValueError("GLOBAL_PROVIDER_BRANDING constant must exist exactly once")
    if text.count('"scope": "global_provider_branding"') != 1:
        raise ValueError("global provider branding application must exist exactly once")
    presentation = text.find('"scope": "global_stream_presentation"')
    branding = text.find('"scope": "global_provider_branding"')
    final_return = text.find("    if text == original_text:", branding)
    if presentation < 0 or branding < 0 or final_return < 0 or not (presentation < branding < final_return):
        raise ValueError("Core order must be stream presentation -> provider branding -> return")
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
    if args.check and changed:
        raise SystemExit("provider branding pipeline normalization required: " + ", ".join(changed))
    if args.apply and normalized != current:
        TARGET.write_text(normalized, encoding="utf-8")
    print(
        "FIELD_PROVIDER_BRANDING_PIPELINE "
        f"changed={len(changed)} order=presentation_then_branding facts_preserved=true"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
