#!/usr/bin/env python3
"""Expose Castle API language evidence on each stream row, without inferring roles."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts/provider_patches/castle_runtime_v1.py"

REPLACEMENTS = (
    (
        "  function outputRows(value,meta,label){",
        "  function outputRows(value,meta,label,language){",
    ),
    (
        '          name:"Castle "+label+" - "+quality,',
        '          name:"Castle - "+quality,\n          sourceLabel:"Castle "+label,',
    ),
    (
        "          quality:quality,\n          headers:playbackHeaders(),",
        "          quality:quality,\n          language:s(language),\n          headers:playbackHeaders(),",
    ),
    (
        '        name:"Castle "+label,',
        '        name:"Castle",\n        sourceLabel:"Castle "+label,',
    ),
    (
        '        quality:String(c.resolution===3?"1080p":c.resolution===1?"480p":"720p"),\n        headers:playbackHeaders(),',
        '        quality:String(c.resolution===3?"1080p":c.resolution===1?"480p":"720p"),\n        language:s(language),\n        headers:playbackHeaders(),',
    ),
    (
        '        var label="["+s(track.languageName||track.abbreviate||"Unknown")+"]";\n'
        '        streams.push.apply(streams,outputRows(\n'
        '          await video(sec,activeMovieId,episodeId,track.languageId),\n'
        '          meta,\n'
        '          label\n'
        '        ));',
        '        var trackLanguage=s(track.languageName||track.abbreviate||"");\n'
        '        var label="["+(trackLanguage||"Unknown")+"]";\n'
        '        streams.push.apply(streams,outputRows(\n'
        '          await video(sec,activeMovieId,episodeId,track.languageId),\n'
        '          meta,\n'
        '          label,\n'
        '          trackLanguage\n'
        '        ));',
    ),
    (
        '          meta,\n          "[Shared]"\n        ));',
        '          meta,\n          "[Shared]",\n          ""\n        ));',
    ),
)


def main() -> int:
    text = TARGET.read_text(encoding="utf-8")
    before = text
    for old, new in REPLACEMENTS:
        if new in text:
            continue
        if text.count(old) != 1:
            raise AssertionError(f"Castle language migration anchor drifted: {old}")
        text = text.replace(old, new, 1)

    required = (
        "function outputRows(value,meta,label,language)",
        'name:"Castle - "+quality',
        'sourceLabel:"Castle "+label',
        "language:s(language)",
        'var trackLanguage=s(track.languageName||track.abbreviate||"")',
        "label,\n          trackLanguage",
        '"[Shared]",\n          ""',
    )
    for needle in required:
        if needle not in text:
            raise AssertionError(f"Castle structured language contract missing: {needle}")

    if text != before:
        TARGET.write_text(text, encoding="utf-8")
    print("CASTLE_LANGUAGE_STRUCTURE_V1_OK", "changed=" + str(text != before).lower())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
