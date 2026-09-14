#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "provider-overrides.json"
PROVIDER = "voiranime"
CURRENT = "https://voir-anime.to"
CURRENT_HOST = "voir-anime.to"
MARKER = "NIAKVIO_VOIRANIME_DOMAIN_AUTHORITY_V1"


def apply_document(data: dict) -> bool:
    patches = data.get("provider_patches")
    if not isinstance(patches, dict) or not isinstance(patches.get(PROVIDER), dict):
        raise AssertionError("voiranime provider patch missing")
    row = patches[PROVIDER]

    legos = list(row.get("provider_lego_scripts") or [])
    required = {
        "scripts/provider_patches/voiranime_homes_runtime_v1.py",
        "scripts/provider_patches/voiranime_anime_runtime_v2.py",
    }
    if not required.issubset(set(legos)):
        raise AssertionError("VoirAnime current movie/anime runtime Legos missing")
    options = row.get("provider_lego_options") or {}
    anime = options.get("scripts/provider_patches/voiranime_anime_runtime_v2.py") or {}
    movie = options.get("scripts/provider_patches/voiranime_homes_runtime_v1.py") or {}
    if str(anime.get("base") or "").rstrip("/") != CURRENT:
        raise AssertionError("VoirAnime anime runtime is not based on voir-anime.to")
    if str(movie.get("movie_site") or "").rstrip("/") != CURRENT:
        raise AssertionError("VoirAnime movie runtime is not based on voir-anime.to")

    before = json.dumps(row, ensure_ascii=False, sort_keys=True)
    row["official_site"] = CURRENT
    row["proof_search_bases"] = [CURRENT]

    for field in ("domain_substitutions", "runtime_domain_replacements"):
        mapping = row.get(field)
        if not isinstance(mapping, dict):
            mapping = {}
        # The current runtime itself is authoritative; it must never be rewritten
        # away before its requests execute.
        mapping.pop(CURRENT_HOST, None)
        for stale in ("voiranime.diy", "voiranime.com", "voiranime.store"):
            mapping[stale] = CURRENT_HOST
        # .homes is a sibling DLE provider with a different runtime contract. Do
        # not silently rewrite it into either canonical implementation.
        mapping.pop("voiranime.homes", None)
        row[field] = mapping

    notes = row.get("notes")
    if isinstance(notes, str):
        notes = [notes]
    elif not isinstance(notes, list):
        notes = []
    notes = [n for n in notes if "NIAKVIO_PROVIDER_VOIRANIME_HOMES_AUTHORITY_V21_10" not in str(n)]
    note = (
        f"{MARKER}: live exact-fixture evidence and both active runtime Legos use {CURRENT}; "
        "stale .diy/.com/.store domains may migrate to .to, while the separate .homes DLE authority is not conflated."
    )
    if note not in notes:
        notes.append(note)
    row["notes"] = notes

    return before != json.dumps(row, ensure_ascii=False, sort_keys=True)


def validate_document(data: dict) -> None:
    row = (data.get("provider_patches") or {}).get(PROVIDER) or {}
    if row.get("official_site") != CURRENT:
        raise AssertionError("VoirAnime canonical site is not current .to")
    if row.get("proof_search_bases") != [CURRENT]:
        raise AssertionError("VoirAnime proof base drift")
    for field in ("domain_substitutions", "runtime_domain_replacements"):
        mapping = row.get(field) or {}
        if CURRENT_HOST in mapping:
            raise AssertionError(f"{field} rewrites current .to authority")
        if "voiranime.homes" in mapping:
            raise AssertionError(f"{field} conflates sibling .homes authority")
        for stale in ("voiranime.diy", "voiranime.com", "voiranime.store"):
            if mapping.get(stale) != CURRENT_HOST:
                raise AssertionError(f"{field} missing {stale} -> {CURRENT_HOST}")
    text = json.dumps(row, ensure_ascii=False)
    if MARKER not in text:
        raise AssertionError("VoirAnime current authority marker missing")


def main() -> int:
    data = json.loads(PATH.read_text(encoding="utf-8"))
    changed = apply_document(data)
    validate_document(data)
    if changed:
        PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"VOIRANIME_DOMAIN_AUTHORITY_V1_OK changed={str(changed).lower()} current={CURRENT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
