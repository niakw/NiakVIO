#!/usr/bin/env python3
"""Migrate legacy V22 presentation assertions to the V23 language-role contract."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GLOBAL_TEST = ROOT / "tests/global_stream_presentation_test.py"
PIPELINE_TEST = ROOT / "tests/global_stream_presentation_pipeline_test.py"

GLOBAL_REPLACEMENTS = (
    (
        'assert presentation.REVISION == "all-providers-client-projection-strongest-evidence-v22"',
        'assert presentation.REVISION == "all-providers-client-projection-language-roles-v23"',
    ),
    (
        'assert "all-providers-client-projection-strongest-evidence-v22" in patched',
        'assert "all-providers-client-projection-language-roles-v23" in patched',
    ),
    (
        'assert row["title"] == "Purstream - 4K - MULTI (VF/VO)", row',
        'assert row["title"] == "Purstream - 4K", row',
    ),
    (
        'assert vf["title"] == "Coflix - 1080p - VF"',
        'assert vf["title"] == "Coflix - 1080p"',
    ),
    (
        'assert desktop_native["row"]["title"] == "Cineby - 1080p - VO", desktop_native',
        'assert desktop_native["row"]["title"] == "Cineby - 1080p", desktop_native',
    ),
    (
        'assert vfq["language"] == "VFQ" and "🇫🇷 VFQ" in vfq["description"]\nassert "vfq" in vfq["badgeIds"]',
        'assert vfq["language"] == "VFQ", vfq\nassert vfq["languageTracks"] == [{"code":"fr","tag":"FR","label":"French","role":"Dub"}], vfq\nassert "French · Dub" in vfq["description"], vfq\nassert "FR Dub" in vfq["displayBadges"], vfq\nassert "vfq" in vfq["badgeIds"]',
    ),
    (
        'print("global stream presentation V22 strongest-evidence tests passed")',
        'print("global stream presentation V23 language-role tests passed")',
    ),
)

PIPELINE_REPLACEMENTS = (
    (
        '    # V22 exposes both proven quality and the detailed language in the client\n'
        '    # title. Quality therefore remains visible but is no longer necessarily the\n'
        '    # final suffix.\n'
        '    assert " - 1080p" in native["row"]["title"], native\n'
        '    assert native["row"]["title"].endswith(" - VO"), native',
        '    # V23 keeps the title uniform: provider + strongest proven quality only.\n'
        '    # Language remains in the structured fields, badges and description.\n'
        '    assert native["row"]["title"] == "Generic Core Test - 1080p", native\n'
        '    assert native["row"]["language"] == "VO", native\n'
        '    assert "🌐 VO" in native["row"]["description"], native',
    ),
)


def apply_replacements(path: Path, replacements: tuple[tuple[str, str], ...]) -> bool:
    text = path.read_text(encoding="utf-8")
    before = text
    for old, new in replacements:
        if new in text:
            continue
        if text.count(old) != 1:
            raise AssertionError(f"V23 presentation test anchor drifted in {path.name}: {old}")
        text = text.replace(old, new, 1)
    if text != before:
        path.write_text(text, encoding="utf-8")
        return True
    return False


def main() -> int:
    global_changed = apply_replacements(GLOBAL_TEST, GLOBAL_REPLACEMENTS)
    pipeline_changed = apply_replacements(PIPELINE_TEST, PIPELINE_REPLACEMENTS)
    global_text = GLOBAL_TEST.read_text(encoding="utf-8")
    if ' - MULTI (VF/VO)"' in global_text or ' - 1080p - VF"' in global_text or ' - 1080p - VO"' in global_text:
        raise AssertionError("legacy language suffix remains in presentation title assertion")
    print(
        "GLOBAL_STREAM_PRESENTATION_V23_TESTS_OK",
        f"global_changed={str(global_changed).lower()}",
        f"pipeline_changed={str(pipeline_changed).lower()}",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
