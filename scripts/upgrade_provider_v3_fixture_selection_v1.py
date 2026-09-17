#!/usr/bin/env python3
"""Keep Provider v3 live fixtures semantically aligned with provider capabilities.

Only providers whose *canonical* semantic contract explicitly contains both
``anime`` and ``movie`` receive the Jujutsu Kaisen 0 movie fixture. Anime-only
providers (for example AniKotoTV) must never be widened to movie merely because
the transport/runtime may use the ``tv`` alias for episodic anime.

Once a provider-targeted fixture already covers a semantic type, the queue does
not append the generic fallback for that same type.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / ".github" / "triggers" / "nuvio-client-lab.json"
MANIFEST = ROOT / "manifest.json"
QUEUE = ROOT / "scripts" / "validate_provider_v3_routes_sequential.py"
SLUG = "jujutsu-kaisen-0"
MODERN_QUEUE_MARKER = "# PROVIDER_V3_SEMANTIC_FIXTURE_FALLBACKS_V1"

OLD_QUEUE = '''        for media_type in supported:\n            slug = REPRESENTATIVE[media_type]\n            row = by_slug.get(slug)\n            if row is not None and all(existing["slug"] != slug for existing in selected):\n                selected.append(row)\n'''
NEW_QUEUE = '''        for media_type in supported:\n            # A provider-targeted fixture is stronger than the generic fallback.\n            # Canonical anime+movie providers use an anime feature film for movie\n            # proof; anime-only providers are never widened to movie here.\n            if any(existing["semantic_type"] == media_type for existing in selected):\n                continue\n            slug = REPRESENTATIVE[media_type]\n            row = by_slug.get(slug)\n            if row is not None and all(existing["slug"] != slug for existing in selected):\n                selected.append(row)\n'''


def canonical_types(row: dict) -> set[str]:
    # canonicalSupportedTypes is semantic authority. supportedTypes may contain
    # compatibility/transport aliases and therefore must not widen semantics.
    raw = row.get("canonicalSupportedTypes")
    if not isinstance(raw, list):
        raw = row.get("supportedTypes") or []
    return {str(v or "").strip().casefold() for v in raw if str(v or "").strip()}


def anime_movie_provider_ids(manifest: dict) -> list[str]:
    out: list[str] = []
    for row in manifest.get("scrapers") or []:
        if not isinstance(row, dict):
            continue
        canonical = canonical_types(row)
        # This fixture is only for true canonical anime-film support. Episodic
        # anime transport aliases such as tv are irrelevant to this decision.
        if "anime" in canonical and "movie" in canonical:
            pid = str(row.get("id") or "").strip().casefold()
            if pid and pid not in out:
                out.append(pid)
    return out


def anime_only_provider_ids(manifest: dict) -> set[str]:
    out: set[str] = set()
    for row in manifest.get("scrapers") or []:
        if not isinstance(row, dict):
            continue
        canonical = canonical_types(row)
        if canonical == {"anime"}:
            pid = str(row.get("id") or "").strip().casefold()
            if pid:
                out.add(pid)
    return out


def patch() -> bool:
    changed = False
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    providers = anime_movie_provider_ids(manifest)
    anime_only = anime_only_provider_ids(manifest)
    if "anikototv" not in anime_only:
        raise AssertionError("anikototv must remain canonical anime-only")
    if "anikototv" in providers:
        raise AssertionError("anikototv must never be widened to canonical movie")

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

    # Do not keep live-action Interstellar as an explicit target for providers
    # whose canonical movie lane is specifically part of an anime catalogue.
    provider_set = set(providers)
    for row in fixtures:
        if not isinstance(row, dict) or row.get("slug") != "interstellar":
            continue
        current = [str(v or "").strip() for v in row.get("providers") or []]
        filtered = [v for v in current if v.casefold() not in provider_set]
        if filtered != current:
            row["providers"] = filtered
            changed = True
    corpus["fixtures"] = fixtures
    if changed:
        CORPUS.write_text(json.dumps(corpus, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    queue = QUEUE.read_text(encoding="utf-8")
    if NEW_QUEUE not in queue and MODERN_QUEUE_MARKER not in queue:
        if queue.count(OLD_QUEUE) != 1:
            raise AssertionError(f"fixture queue fallback anchor count={queue.count(OLD_QUEUE)}")
        QUEUE.write_text(queue.replace(OLD_QUEUE, NEW_QUEUE, 1), encoding="utf-8")
        changed = True
    return changed


def validate() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    providers = anime_movie_provider_ids(manifest)
    anime_only = anime_only_provider_ids(manifest)
    if "anikototv" not in anime_only or "anikototv" in providers:
        raise AssertionError("AniKotoTV semantic contract regressed: expected anime-only")

    corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
    fixtures = corpus.get("fixtures") or []
    row = next((v for v in fixtures if isinstance(v, dict) and v.get("slug") == SLUG), None)
    if not row:
        raise AssertionError("anime movie fixture missing")
    fixture = row.get("fixture") or {}
    if fixture.get("tmdbId") != "810693" or fixture.get("mediaType") != "movie" or fixture.get("animeMovie") is not True:
        raise AssertionError("anime movie fixture identity mismatch")
    actual = {str(v).casefold() for v in row.get("providers") or []}
    if actual != set(providers):
        raise AssertionError(f"anime movie fixture provider drift actual={sorted(actual)} expected={sorted(providers)}")
    if "anikototv" in actual:
        raise AssertionError("anime-only AniKotoTV leaked into anime movie fixture")

    interstellar = next((v for v in fixtures if isinstance(v, dict) and v.get("slug") == "interstellar"), {})
    leaked = sorted(set(providers) & {str(v).casefold() for v in interstellar.get("providers") or []})
    if leaked:
        raise AssertionError("anime-movie providers still targeted by Interstellar: " + ",".join(leaked))
    queue = QUEUE.read_text(encoding="utf-8")
    if NEW_QUEUE not in queue and MODERN_QUEUE_MARKER not in queue:
        raise AssertionError("provider queue does not prefer targeted semantic fixtures")


def main() -> int:
    changed = patch()
    validate()
    print(
        "PROVIDER_V3_FIXTURE_SELECTION_V1_OK "
        f"changed={str(changed).lower()} anime_movie={SLUG} tmdb=810693 "
        f"providers={len(anime_movie_provider_ids(json.loads(MANIFEST.read_text(encoding='utf-8'))))} "
        "anikototv=anime-only targeted_fixture_beats_generic=true"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
