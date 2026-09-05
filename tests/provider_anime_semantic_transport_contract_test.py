#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANONICAL = {"movie", "tv", "anime"}


def types(raw: object, label: str) -> list[str]:
    assert isinstance(raw, list) and raw, f"{label}: non-empty media type list required"
    out: list[str] = []
    for value in raw:
        item = str(value or "").strip().casefold()
        assert item in CANONICAL, f"{label}: invalid media type {item!r}"
        assert item not in out, f"{label}: duplicate media type {item!r}"
        out.append(item)
    return out


def transport_for(canonical: list[str]) -> list[str]:
    wanted = list(canonical)
    if "anime" in wanted:
        for compatible in ("tv", "movie"):
            if compatible not in wanted:
                wanted.append(compatible)
    return wanted


catalog = json.loads((ROOT / "provider_catalog.json").read_text(encoding="utf-8"))
assert catalog.get("sourceOfTruth") is True
semantics: dict[str, list[str]] = {}
for provider in catalog.get("providers") or []:
    assert isinstance(provider, dict)
    scraper = provider.get("scraper")
    assert isinstance(scraper, dict)
    provider_id = str(scraper.get("id") or provider.get("canonicalId") or "").strip().casefold()
    assert provider_id and provider_id not in semantics
    semantics[provider_id] = types(
        scraper.get("canonicalSupportedTypes") or scraper.get("supportedTypes"),
        f"provider_catalog.json:{provider_id}",
    )
assert len(semantics) == 96, len(semantics)

anime_only = 0
anime_mixed = 0
manifest_anime = 0
for relative in ("manifest.json", "vf/manifest.json"):
    manifest = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    for row in manifest.get("scrapers") or []:
        assert isinstance(row, dict)
        provider_id = str(row.get("id") or "").strip().casefold()
        assert provider_id in semantics, f"{relative}:{provider_id}: missing provider_catalog semantics"
        canonical = semantics[provider_id]
        if "anime" not in canonical:
            continue
        manifest_anime += 1
        anime_only += int(canonical == ["anime"])
        anime_mixed += int(len(canonical) > 1)
        explicit = types(row.get("canonicalSupportedTypes"), f"{relative}:{provider_id}:canonicalSupportedTypes")
        transport = types(row.get("supportedTypes"), f"{relative}:{provider_id}:supportedTypes")
        assert explicit == canonical, (
            f"{relative}:{provider_id}: canonical anime semantics drift",
            explicit,
            canonical,
        )
        wanted = transport_for(canonical)
        assert transport == wanted, (
            f"{relative}:{provider_id}: anime transport must preserve canonical order then add TV/movie lanes",
            transport,
            wanted,
        )

assert manifest_anime > 0, "expected anime-capable providers in projections"
assert anime_only > 0, "expected at least one canonically anime-only provider"
assert anime_mixed > 0, "expected at least one mixed canonical provider containing anime"

core = (ROOT / "scripts" / "provider_patches" / "global_media_type_resolution_v1.py").read_text(encoding="utf-8")
assert 'if(canonical==="anime")return namespace==="movie"?"movie":"tv";' in core
assert 'return"anime";\n  }\n  return canonical==="movie"?"movie":"tv";' not in core
assert 'tmdb-data-contract-launch-gate-v27-anime-semantic-transport' in core

materializer = (ROOT / "scripts" / "materialize_provider_v3_all.py").read_text(encoding="utf-8")
assert "def normalize_anime_transport_compatibility(" in materializer
assert 'if "anime" not in canonical:' in materializer
assert 'for compatible in ("tv", "movie"):' in materializer
assert 'if set(canonical) != {"anime"}:' not in materializer

enforcer = (ROOT / "scripts" / "enforce_provider_v3_semantic_transport_contract_v5.py").read_text(encoding="utf-8")
assert "def catalog_semantic_types()" in enforcer
assert 'normalize_manifest(ROOT / "manifest.json", semantics)' in enforcer
assert 'normalize_manifest(ROOT / "vf" / "manifest.json", semantics)' in enforcer

finalizer = (ROOT / "scripts" / "finalize_gowaru_provider_v3_source_plans.py").read_text(encoding="utf-8")
assert 'value = value.strip().rstrip(";,)]")' in finalizer
assert 'value = value.strip().rstrip(";,)]}")' not in finalizer

print(
    "provider anime semantic/transport contract passed "
    f"catalog=96 projected_anime_rows={manifest_anime} anime_only={anime_only} mixed_anime={anime_mixed} "
    "transport=canonical+tv+movie"
)
