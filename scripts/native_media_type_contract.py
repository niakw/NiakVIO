#!/usr/bin/env python3
"""Canonical media-type boundary for NiakVIO/Nuvio evidence and provider calls.

Client aliases describe how Nuvio surfaced an item; they do not own the final
content identity.

Rules:
- series/show/other are TV-series aliases by default;
- movie -> movie, tv -> tv, anime -> anime;
- trusted metadata may refine a tv/series-shaped input to anime;
- Animation alone is not sufficient: Western animation must remain tv/movie.
"""
from __future__ import annotations

from typing import Any

CANONICAL_MEDIA_TYPES = frozenset({"movie", "tv", "anime"})
TV_ALIASES = frozenset({"series", "show", "other"})
ANIMATION_GENRE_ID = 16


def _strings(value: Any) -> set[str]:
    if isinstance(value, (list, tuple, set)):
        return {str(item or "").strip().casefold() for item in value if str(item or "").strip()}
    text = str(value or "").strip().casefold()
    return {text} if text else set()


def tmdb_metadata_indicates_anime(metadata: dict[str, Any] | None) -> bool:
    row = metadata if isinstance(metadata, dict) else {}

    # A prior trusted resolver may already have classified the work.
    explicit = str(
        row.get("canonicalMediaType")
        or row.get("canonical_media_type")
        or row.get("category")
        or ""
    ).strip().casefold()
    if explicit == "anime":
        return True

    keyword_rows = row.get("keywords")
    if isinstance(keyword_rows, dict):
        keyword_rows = keyword_rows.get("results") or keyword_rows.get("keywords") or []
    keyword_names = {
        str(item.get("name") or "").strip().casefold()
        for item in (keyword_rows or [])
        if isinstance(item, dict)
    }
    keyword_names.update(_strings(row.get("keywordNames") or row.get("keyword_names")))
    if "anime" in keyword_names:
        return True

    genre_rows = row.get("genres") or []
    genre_ids = {
        int(item.get("id"))
        for item in genre_rows
        if isinstance(item, dict) and str(item.get("id") or "").isdigit()
    }
    genre_ids.update(
        int(value)
        for value in (row.get("genre_ids") or row.get("genreIds") or [])
        if str(value or "").isdigit()
    )
    genre_names = {
        str(item.get("name") or "").strip().casefold()
        for item in genre_rows
        if isinstance(item, dict) and str(item.get("name") or "").strip()
    }
    animated = ANIMATION_GENRE_ID in genre_ids or "animation" in genre_names

    original_language = str(row.get("original_language") or row.get("originalLanguage") or "").strip().casefold()
    origin_countries = _strings(row.get("origin_country") or row.get("originCountry"))
    production_countries = {
        str(item.get("iso_3166_1") or "").strip().casefold()
        for item in (row.get("production_countries") or row.get("productionCountries") or [])
        if isinstance(item, dict)
    }
    japanese_origin = (
        original_language == "ja"
        or "jp" in origin_countries
        or "jp" in production_countries
    )
    return animated and japanese_origin


def canonical_media_type(
    value: Any,
    *,
    category: Any = None,
    metadata: dict[str, Any] | None = None,
) -> str:
    raw = str(value or "movie").strip().casefold()
    category_raw = str(category or "").strip().casefold()

    # Content identity beats client presentation. Nuvio may expose Naruto or
    # Jujutsu Kaisen as a generic series/tv item; a trusted anime classification
    # must remain anime all the way to the provider request.
    if category_raw == "anime" or tmdb_metadata_indicates_anime(metadata):
        return "anime"

    if raw in TV_ALIASES:
        raw = "tv"
    if raw not in CANONICAL_MEDIA_TYPES:
        raise ValueError(
            f"unsupported media type {raw!r}; expected movie|tv|anime "
            "or a TV-series input alias series|show|other"
        )
    return raw


def fixture_media_type(fixture: dict[str, Any]) -> str:
    metadata = fixture.get("tmdbMetadata") or fixture.get("tmdb_metadata") or fixture.get("metadata")
    return canonical_media_type(
        fixture.get("mediaType") or fixture.get("type") or fixture.get("category") or "movie",
        category=fixture.get("category"),
        metadata=metadata if isinstance(metadata, dict) else fixture,
    )
