#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CURRENT_PROVIDER_COUNT = 46
CANONICAL = {"movie", "tv", "anime"}
TRANSPORT = CANONICAL


def values(raw: object, label: str, allowed: set[str]) -> list[str]:
    assert isinstance(raw, list) and raw, f"{label}: non-empty media type list required"
    out: list[str] = []
    for value in raw:
        item = str(value or "").strip().casefold()
        assert item in allowed, f"{label}: invalid media type {item!r}"
        assert item not in out, f"{label}: duplicate media type {item!r}"
        out.append(item)
    return out


def transport_for(canonical: list[str]) -> list[str]:
    wanted = list(canonical)
    if "anime" in canonical and "tv" not in wanted:
        wanted.append("tv")
    return wanted


catalog = json.loads((ROOT / "provider_catalog.json").read_text(encoding="utf-8"))
assert catalog.get("sourceOfTruth") is True
semantics: dict[str, list[str]] = {}
for provider in catalog.get("providers") or []:
    scraper = provider.get("scraper") if isinstance(provider, dict) else None
    assert isinstance(scraper, dict)
    provider_id = str(scraper.get("id") or provider.get("canonicalId") or "").strip().casefold()
    assert provider_id and provider_id not in semantics
    semantics[provider_id] = values(
        scraper.get("canonicalSupportedTypes") or scraper.get("supportedTypes"),
        f"provider_catalog.json:{provider_id}",
        CANONICAL,
    )
assert len(semantics) == CURRENT_PROVIDER_COUNT, len(semantics)

projected = 0
anime_only = 0
canonical_movie_anime = 0
for relative in ("manifest.json", "vf/manifest.json", "no-anime/manifest.json", "vf-no-anime/manifest.json"):
    path = ROOT / relative
    if not path.is_file():
        continue
    manifest = json.loads(path.read_text(encoding="utf-8"))
    ids: set[str] = set()
    for row in manifest.get("scrapers") or []:
        provider_id = str(row.get("id") or "").strip().casefold()
        assert provider_id and provider_id not in ids, f"{relative}: duplicate provider {provider_id}"
        ids.add(provider_id)
        assert provider_id in semantics, f"{relative}:{provider_id}: missing current semantics"
        canonical = semantics[provider_id]
        transport = values(row.get("supportedTypes"), f"{relative}:{provider_id}:supportedTypes", TRANSPORT)
        explicit = row.get("canonicalSupportedTypes")
        if explicit:
            assert values(
                explicit,
                f"{relative}:{provider_id}:canonicalSupportedTypes",
                CANONICAL,
            ) == canonical
        wanted = transport_for(canonical)
        assert transport == wanted, (relative, provider_id, canonical, transport, wanted)
        assert ("movie" in transport) == ("movie" in canonical), (
            relative,
            provider_id,
            canonical,
            transport,
        )
        if "anime" in canonical:
            assert "tv" in transport, (relative, provider_id, transport)
        projected += 1
        anime_only += int(canonical == ["anime"])
        canonical_movie_anime += int("movie" in canonical and "anime" in canonical)
    assert ids <= set(semantics), f"{relative}: projection escaped current Hub46"

assert projected >= CURRENT_PROVIDER_COUNT
assert anime_only > 0

materializer = (ROOT / "scripts/materialize_provider_v3_all.py").read_text(encoding="utf-8")
assert 'if "anime" in canonical and "tv" not in wanted:' in materializer
assert 'wanted.append("tv")' in materializer
assert 'wanted.append("series")' not in materializer
assert 'item in {"movie", "tv", "anime", "series"}' not in materializer
assert 'for compatible in ("tv", "movie"):' not in materializer
assert 'wanted = ["anime", "tv", "movie"]' not in materializer

enforcer = (ROOT / "scripts/enforce_provider_v3_semantic_transport_contract_v5.py").read_text(encoding="utf-8")
assert 'def anime_transport(canonical: list[str]) -> list[str]:' in enforcer
anime_transport_body = enforcer.split('def anime_transport(canonical: list[str]) -> list[str]:', 1)[1].split('\ndef catalog_semantic_types()', 1)[0]
assert 'if "anime" in canonical and "tv" not in wanted:' in anime_transport_body
assert 'wanted.append("tv")' in anime_transport_body
assert 'wanted.append("series")' not in anime_transport_body
assert '"series"' not in anime_transport_body
assert 'expected=46' in enforcer

reapply = (ROOT / "scripts/reapply_published_overrides.py").read_text(encoding="utf-8")
assert 'Movie is not a generic' in reapply
assert 'transport.append("tv")' in reapply
assert 'transport.append("series")' not in reapply

machine = json.loads((ROOT / "automation/provider-v3-architecture.json").read_text(encoding="utf-8"))
assert machine["media_types"]["anime_only_transport_compatibility"] == ["anime", "tv"]

print(
    "provider anime semantic/transport contract passed "
    f"providers={len(semantics)} projected_rows={projected} anime_only={anime_only} movie_anime={canonical_movie_anime} "
    "rule=no-artificial-movie+anime-tv-alias+no-series-synthesis"
)
