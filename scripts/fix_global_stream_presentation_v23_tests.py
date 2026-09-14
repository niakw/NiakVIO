#!/usr/bin/env python3
"""Migrate legacy V22 presentation assertions to the V23 language-role contract."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "tests/global_stream_presentation_test.py"

REPLACEMENTS = (
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


def main() -> int:
    text = TARGET.read_text(encoding="utf-8")
    before = text
    for old, new in REPLACEMENTS:
        if new in text:
            continue
        if text.count(old) != 1:
            raise AssertionError(f"V23 presentation test anchor drifted: {old}")
        text = text.replace(old, new, 1)
    # V23 contract: language/role detail belongs to badges/description, never the title.
    if ' - MULTI (VF/VO)"' in text or ' - 1080p - VF"' in text or ' - 1080p - VO"' in text:
        raise AssertionError("legacy language suffix remains in presentation title assertion")
    if text != before:
        TARGET.write_text(text, encoding="utf-8")
    print("GLOBAL_STREAM_PRESENTATION_V23_TESTS_OK", "changed=" + str(text != before).lower())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
