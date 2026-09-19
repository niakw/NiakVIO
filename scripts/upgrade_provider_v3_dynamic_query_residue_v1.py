#!/usr/bin/env python3
"""Reject runtime routes that still contain unabstracted content/session query state."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts" / "validate_provider_v3_routes_sequential.py"
MARKER = "PROVIDER_V3_DYNAMIC_QUERY_RESIDUE_V1"

OLD_SEASON = '''        elif season and value == season and key_l in {"s", "season", "season_number"}:
            placeholder = "{season}"
        elif episode and value == episode and key_l in {"e", "ep", "episode", "episode_number"}:
            placeholder = "{episode}"
'''
NEW_SEASON = '''        elif season and value == season and key_l in {"s", "season", "season_number", "seasonid", "season_id"}:
            placeholder = "{season}"
        elif episode and value == episode and key_l in {"e", "ep", "episode", "episode_number", "episodeid", "episode_id"}:
            placeholder = "{episode}"
'''

OLD_ROUTE = '''    route = path
    if rendered_query:
        route += "?" + urllib.parse.urlencode(rendered_query, doseq=True, safe="{}:/")
    fixture_specific = []
'''

NEW_ROUTE = '''    route = path
    if rendered_query:
        route += "?" + urllib.parse.urlencode(rendered_query, doseq=True, safe="{}:/")

    # PROVIDER_V3_DYNAMIC_QUERY_RESIDUE_V1
    # A request observed live is not reusable Provider DATA while it still
    # contains literal content identity or request/session state. Season/episode
    # aliases above are abstracted first; remaining values under these keys must
    # stay diagnostic evidence only until Learning can derive a stable recipe.
    volatile_query_keys = {
        "seed", "token", "access_token", "auth", "signature", "sig", "hash",
        "nonce", "timestamp", "ts", "expires", "expiry", "expire", "key",
    }
    content_identity_query_keys = {
        "imdb", "imdbid", "imdb_id", "year", "releaseyear", "release_year",
        "seasonid", "season_id", "episodeid", "episode_id",
    }
    dynamic_query_residue = []
    for residue_key, residue_value in rendered_query:
        key_l = str(residue_key or "").strip().casefold()
        value_s = str(residue_value or "").strip()
        if not value_s or ("{" in value_s and "}" in value_s):
            continue
        if key_l in volatile_query_keys or key_l in content_identity_query_keys:
            dynamic_query_residue.append({"key": residue_key, "value": value_s})
    if dynamic_query_residue:
        reusable = False

    fixture_specific = []
'''

OLD_META = '''        "reusable": reusable,
        "fixtureSpecificValues": unique(fixture_specific, 12),
    }
'''
NEW_META = '''        "reusable": reusable,
        "fixtureSpecificValues": unique(fixture_specific, 12),
        "dynamicQueryResidue": dynamic_query_residue[:12],
    }
'''


def patch() -> bool:
    text = TARGET.read_text(encoding="utf-8")
    if MARKER in text:
        validate(text)
        return False
    if text.count(OLD_SEASON) != 1:
        raise AssertionError(f"season/episode alias anchor count={text.count(OLD_SEASON)}")
    if text.count(OLD_ROUTE) != 1:
        raise AssertionError(f"route residue anchor count={text.count(OLD_ROUTE)}")
    if text.count(OLD_META) != 1:
        raise AssertionError(f"derivation meta anchor count={text.count(OLD_META)}")
    text = text.replace(OLD_SEASON, NEW_SEASON, 1)
    text = text.replace(OLD_ROUTE, NEW_ROUTE, 1)
    text = text.replace(OLD_META, NEW_META, 1)
    TARGET.write_text(text, encoding="utf-8")
    validate(text)
    return True


def validate(text: str | None = None) -> None:
    value = text if text is not None else TARGET.read_text(encoding="utf-8")
    required = (
        MARKER,
        '"seasonid", "season_id"',
        '"episodeid", "episode_id"',
        "volatile_query_keys = {",
        "content_identity_query_keys = {",
        '"seed", "token"',
        '"imdb", "imdbid", "imdb_id", "year"',
        '"dynamicQueryResidue": dynamic_query_residue[:12]',
        "if dynamic_query_residue:\n        reusable = False",
    )
    for needle in required:
        if needle not in value:
            raise AssertionError(f"dynamic query residue contract missing: {needle}")


def main() -> int:
    changed = patch()
    print(
        "PROVIDER_V3_DYNAMIC_QUERY_RESIDUE_V1_OK "
        f"changed={str(changed).lower()} season_episode_aliases=abstracted "
        "volatile_or_literal_identity=rejected_from_reusable_data"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
