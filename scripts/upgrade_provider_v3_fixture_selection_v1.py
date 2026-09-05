#!/usr/bin/env python3
"""Keep Provider v3 live fixtures semantically aligned with provider capabilities.

Anime-specialized providers that expose canonical ``movie`` support mean anime
feature films, not arbitrary live-action cinema. Their movie proof therefore uses
Jujutsu Kaisen 0 rather than Interstellar. Also, once a provider-targeted fixture
already covers a semantic type, the queue must not append the generic fallback for
that same type.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / ".github" / "triggers" / "nuvio-client-lab.json"
MANIFEST = ROOT / "manifest.json"
QUEUE = ROOT / "scripts" / "validate_provider_v3_routes_sequential.py"
SLUG = "jujutsu-kaisen-0"

OLD_QUEUE = '''        for media_type in supported:\n            slug = REPRESENTATIVE[media_type]\n            row = by_slug.get(slug)\n            if row is not None and all(existing["slug"] != slug for existing in selected):\n                selected.append(row)\n'''
NEW_QUEUE = '''        for media_type in supported:\n            # A provider-targeted fixture is stronger than the generic fallback.\n            # In particular, anime-specialized providers use an anime feature film\n            # for canonical movie proof instead of being forced through Interstellar.\n            if any(existing["semantic_type"] == media_type for existing in selected):\n                continue\n            slug = REPRESENTATIVE[media_type]\n            row = by_slug.get(slug)\n            if row is not None and all(existing["slug"] != slug for existing in selected):\n                selected.append(row)\n'''


def anime_movie_provider_ids(manifest: dict) -> list[str]:
    out: list[str] = []
    for row in manifest.get("scrapers") or []:
        if not isinstance(row, dict):
            continue
        canonical = {
            str(v or "").strip().casefold()
            for v in (row.get("canonicalSupportedTypes") or row.get("supportedTypes") or [])
        }
        # Specialized anime catalogues expose anime + movie, but not canonical TV.
        if "anime" in canonical and "movie" in canonical and "tv" not in canonical:
            pid = str(row.get("id") or "").strip().casefold()
            if pid and pid not in out:
                out.append(pid)
    return out


def patch() -> bool:
    changed = False
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    providers = anime_movie_provider_ids(manifest)
    if "anikototv" not in providers:
        raise AssertionError("anikototv must be covered by anime-movie fixture selection")

    corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
    fixtures = corpus.get("fixtures")
    if not isinstance(fixtures, list):
        raise AssertionError("nuvio-client-lab fixtures must be an array")
    wanted = {
        "slug": SLUG,
        "providers": providers,
        "fixture": {
            "tmdbId": "810693",
            "mediaType": "movie",
            "title": "Jujutsu Kaisen 0",
            "year": 2021,
            "category": "movie",
            "expectedDurationMinutes": 105,
            "aliases": ["Jujutsu Kaisen 0", "Gekijouban Jujutsu Kaisen 0"],
            "animeMovie": True,
        },
    }
    index = next((i for i, row in enumerate(fixtures) if isinstance(row, dict) and row.get("slug") == SLUG), None)
    if index is None:
        fixtures.append(wanted)
        changed = True
    elif fixtures[index] != wanted:
        fixtures[index] = wanted
        changed = True

    # Do not keep live-action Interstellar as an explicit target for these
    # anime-specialized providers; JJK0 is now their movie fixture.
    for row in fixtures:
        if not isinstance(row, dict) or row.get("slug") != "interstellar":
            continue
        current = [str(v or "").strip() for v in row.get("providers") or []]
        filtered = [v for v in current if v.casefold() not in set(providers)]
        if filtered != current:
            row["providers"] = filtered
            changed = True
    corpus["fixtures"] = fixtures
    if changed:
        CORPUS.write_text(json.dumps(corpus, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    queue = QUEUE.read_text(encoding="utf-8")
    if NEW_QUEUE not in queue:
        if queue.count(OLD_QUEUE) != 1:
            raise AssertionError(f"fixture queue fallback anchor count={queue.count(OLD_QUEUE)}")
        QUEUE.write_text(queue.replace(OLD_QUEUE, NEW_QUEUE, 1), encoding="utf-8")
        changed = True
    return changed


def validate() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    providers = anime_movie_provider_ids(manifest)
    corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
    fixtures = corpus.get("fixtures") or []
    row = next((v for v in fixtures if isinstance(v, dict) and v.get("slug") == SLUG), None)
    if not row:
        raise AssertionError("anime movie fixture missing")
    fixture = row.get("fixture") or {}
    if fixture.get("tmdbId") != "810693" or fixture.get("mediaType") != "movie" or fixture.get("animeMovie") is not True:
        raise AssertionError("anime movie fixture identity mismatch")
    actual = {str(v).casefold() for v in row.get("providers") or []}
    if not set(providers).issubset(actual):
        raise AssertionError("anime movie fixture does not cover every anime-specialized movie provider")
    interstellar = next((v for v in fixtures if isinstance(v, dict) and v.get("slug") == "interstellar"), {})
    leaked = sorted(set(providers) & {str(v).casefold() for v in interstellar.get("providers") or []})
    if leaked:
        raise AssertionError("anime-specialized providers still targeted by Interstellar: " + ",".join(leaked))
    queue = QUEUE.read_text(encoding="utf-8")
    if NEW_QUEUE not in queue:
        raise AssertionError("provider queue does not prefer targeted semantic fixtures")


def main() -> int:
    changed = patch()
    validate()
    print(
        "PROVIDER_V3_FIXTURE_SELECTION_V1_OK "
        f"changed={str(changed).lower()} anime_movie={SLUG} tmdb=810693 "
        "targeted_fixture_beats_generic=true"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
