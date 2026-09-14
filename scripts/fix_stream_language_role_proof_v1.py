#!/usr/bin/env python3
"""Make Original/Dub role inference evidence-based.

A provider-language hint such as VF is not enough to prove `Dub` when the
original language is unknown. Patch the durable migration source and, when the
migration has already been applied in the current workspace, its generated Core
outputs as well.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "scripts/upgrade_stream_language_roles_v1.py"
ENGINE = ROOT / "engine_v2/src/stream-presentation.mjs"
GLOBAL = ROOT / "scripts/provider_patches/global_stream_presentation_v1.py"

REPLACEMENTS = (
    (
        '      add("fr", original === "fr" ? "Original" : "Dub");',
        '      if (original) add("fr", original === "fr" ? "Original" : "Dub");',
    ),
    (
        '      if (isVfProvider(provider) && original !== "fr") add("fr", "Dub");',
        '      if (original && isVfProvider(provider) && original !== "fr") add("fr", "Dub");',
    ),
    (
        'else if(/^(?:VF|VFF|VFQ|FR|FRA|FRE|FRENCH|FRANCAIS|FRANÇAIS|FR-CA)$/i.test(explicit)){add("fr",original==="fr"?"Original":"Dub")}',
        'else if(/^(?:VF|VFF|VFQ|FR|FRA|FRE|FRENCH|FRANCAIS|FRANÇAIS|FR-CA)$/i.test(explicit)){if(original)add("fr",original==="fr"?"Original":"Dub")}',
    ),
    (
        'if(s(c.providerLanguageMode).toLowerCase()==="vf"&&original!=="fr")add("fr","Dub")',
        'if(original&&s(c.providerLanguageMode).toLowerCase()==="vf"&&original!=="fr")add("fr","Dub")',
    ),
)


def patch(path: Path, *, required: bool) -> bool:
    if not path.exists():
        if required:
            raise FileNotFoundError(path)
        return False
    text = path.read_text(encoding="utf-8")
    before = text
    touched = 0
    for old, new in REPLACEMENTS:
        if new in text:
            continue
        if old in text:
            text = text.replace(old, new)
            touched += 1
    if required and touched == 0 and not all(new in text for _old, new in REPLACEMENTS[:2]):
        raise AssertionError(f"{path}: evidence-role source shape drifted")
    if text != before:
        path.write_text(text, encoding="utf-8")
        return True
    return False


def main() -> int:
    changes = {
        "migration": patch(MIGRATION, required=True),
        "engine": patch(ENGINE, required=False),
        "global": patch(GLOBAL, required=False),
    }
    print("STREAM_LANGUAGE_ROLE_PROOF_V1_OK", changes)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
