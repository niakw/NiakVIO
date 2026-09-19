#!/usr/bin/env python3
"""Disambiguate `s=` search aliases from season parameters in Provider v3 routes."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts" / "validate_provider_v3_routes_sequential.py"
MARKER = "PROVIDER_V3_SEASON_QUERY_ROLE_V1"

OLD = '''def route_role(route: str) -> str:
    value = str(route or "").strip().casefold()
    if re.search(r"/(?:search|recherche)(?:[/?#]|$)|[?&](?:s|q|query|keyword|search|story)=", value):
        return "search"
'''

NEW = '''def route_role(route: str) -> str:
    value = str(route or "").strip().casefold()
    # PROVIDER_V3_SEASON_QUERY_ROLE_V1
    # `s=` is ambiguous: WordPress-style search uses it as a query, while many
    # provider resolver APIs use `s` + `e` as season/episode coordinates. Treat
    # it as search only when it is not paired with episode semantics.
    try:
        parsed_role = urllib.parse.urlsplit(value)
        role_query = urllib.parse.parse_qs(parsed_role.query, keep_blank_values=True)
    except ValueError:
        role_query = {}
    has_episode_coordinate = any(key in role_query for key in ("e", "ep", "episode", "episode_number"))
    has_season_coordinate = any(key in role_query for key in ("season", "season_number")) or (
        "s" in role_query and has_episode_coordinate
    )
    explicit_search_query = any(key in role_query for key in ("q", "query", "keyword", "search", "story"))
    ambiguous_s_search = "s" in role_query and not has_season_coordinate
    if (
        re.search(r"/(?:search|recherche)(?:[/?#]|$)", value)
        or explicit_search_query
        or ambiguous_s_search
    ):
        return "search"
'''


def patch() -> bool:
    text = TARGET.read_text(encoding="utf-8")
    if MARKER in text:
        validate(text)
        return False
    if text.count(OLD) != 1:
        raise AssertionError(f"season query role anchor count={text.count(OLD)}")
    text = text.replace(OLD, NEW, 1)
    TARGET.write_text(text, encoding="utf-8")
    validate(text)
    return True


def validate(text: str | None = None) -> None:
    value = text if text is not None else TARGET.read_text(encoding="utf-8")
    required = (
        MARKER,
        'has_episode_coordinate = any(key in role_query',
        '"s" in role_query and has_episode_coordinate',
        'ambiguous_s_search = "s" in role_query and not has_season_coordinate',
    )
    for needle in required:
        if needle not in value:
            raise AssertionError(f"season query role contract missing: {needle}")


def main() -> int:
    changed = patch()
    print(
        "PROVIDER_V3_SEASON_QUERY_ROLE_V1_OK "
        f"changed={str(changed).lower()} s_plus_e=season_episode standalone_s=search"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
