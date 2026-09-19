#!/usr/bin/env python3
"""Make Provider v3 fixture-residue detection aware of semantic query constants."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts" / "validate_provider_v3_routes_sequential.py"
MARKER = "PROVIDER_V3_SEMANTIC_QUERY_RESIDUE_V1"

OLD = '''    fixture_specific = []
    if tmdb and tmdb in route:
        fixture_specific.append(tmdb)
    for raw_title in title_values:
        if raw_title and len(raw_title) >= 4 and raw_title in urllib.parse.unquote(route).casefold():
            fixture_specific.append(raw_title)
    if fixture_specific:
        reusable = False
'''

NEW = '''    fixture_specific = []
    if tmdb and tmdb in route:
        fixture_specific.append(tmdb)

    # PROVIDER_V3_SEMANTIC_QUERY_RESIDUE_V1
    # Detect leaked fixture titles only in path/query values that can actually
    # carry content identity. Canonical semantic constants (type=movie|tv|anime)
    # are stable Provider contract DATA, not fixture-specific residue.
    try:
        residue_parts = urllib.parse.urlsplit(route)
        residue_haystacks = [urllib.parse.unquote(residue_parts.path or "/").casefold()]
        semantic_query_keys = {
            "type", "mediatype", "media_type", "media", "category", "kind"
        }
        for residue_key, residue_value in urllib.parse.parse_qsl(
            residue_parts.query, keep_blank_values=True
        ):
            if (
                residue_key.casefold() in semantic_query_keys
                and canonical(residue_value) in REPRESENTATIVE
            ):
                continue
            residue_haystacks.append(urllib.parse.unquote(residue_value).casefold())
    except ValueError:
        residue_haystacks = [urllib.parse.unquote(route).casefold()]

    for raw_title in title_values:
        if (
            raw_title
            and len(raw_title) >= 4
            and any(raw_title in haystack for haystack in residue_haystacks)
        ):
            fixture_specific.append(raw_title)
    if fixture_specific:
        reusable = False
'''


def patch() -> bool:
    text = TARGET.read_text(encoding="utf-8")
    if MARKER in text:
        validate(text)
        return False
    if text.count(OLD) != 1:
        raise AssertionError(f"semantic query residue anchor count={text.count(OLD)}")
    text = text.replace(OLD, NEW, 1)
    TARGET.write_text(text, encoding="utf-8")
    validate(text)
    return True


def validate(text: str | None = None) -> None:
    value = text if text is not None else TARGET.read_text(encoding="utf-8")
    required = (
        MARKER,
        "semantic_query_keys = {",
        "canonical(residue_value) in REPRESENTATIVE",
        "residue_haystacks",
    )
    for needle in required:
        if needle not in value:
            raise AssertionError(f"semantic query residue contract missing: {needle}")


def main() -> int:
    changed = patch()
    print(
        "PROVIDER_V3_SEMANTIC_QUERY_RESIDUE_V1_OK "
        f"changed={str(changed).lower()} canonical_semantic_query_values=stable"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
