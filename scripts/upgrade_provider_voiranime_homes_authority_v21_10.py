#!/usr/bin/env python3
"""V21.10: bind canonical VoirAnime to the current .homes catalogue authority.

The official VoirAnime hub currently resolves to voiranime.homes. NiakVIO already
has a separately recovered `voiranime-homes` provider whose DATA proves the
Datalife-style catalogue flow:

  POST /engine/ajax/search.php -> provider-local newsid
  GET  /engine/ajax/manga_episodes_api.php?id={id} -> dynamic player URLs

The canonical `voiranime` entry was still pointed at voiranime.diy and therefore
could never use that proven structured flow. This migration reuses the sibling
DATA plan rather than embedding/executing upstream JavaScript or persisting a
signed player/media URL. Hub remains address authority only.

Only the currently proven anime lane is copied into executable structured plans.
The declared movie/anime-film lane stays repair debt until a fresh live proof
qualifies it; semantic types are never shrunk from the provider catalogue.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OVERRIDES = ROOT / "provider-overrides.json"
TARGET = "voiranime"
SOURCE = "voiranime-homes"
HUB = "https://voiranime.org.uk/"
SITE = "https://voiranime.homes"
MARKER = "NIAKVIO_PROVIDER_VOIRANIME_HOMES_AUTHORITY_V21_10"


def _unique(values: list[str]) -> list[str]:
    out: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if text and text not in out:
            out.append(text)
    return out


def _anime_only_plans(rows: Any) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for raw in rows or []:
        if not isinstance(raw, dict):
            continue
        row = copy.deepcopy(raw)
        row["semanticTypes"] = ["anime"]
        out.append(row)
    return out


def apply_document(data: dict[str, Any]) -> bool:
    patches = data.get("provider_patches")
    if not isinstance(patches, dict):
        raise AssertionError("provider_patches missing")
    target = patches.get(TARGET)
    source = patches.get(SOURCE)
    if not isinstance(target, dict) or not isinstance(source, dict):
        raise AssertionError("VoirAnime canonical/sibling provider patches missing")

    source_search = _anime_only_plans(source.get("search_request_plan"))
    source_values = _anime_only_plans(source.get("provider_value_plan"))
    if not source_search or not source_values:
        raise AssertionError("voiranime-homes proven structured DATA plan missing")

    # Require the exact stable shape proved by the sibling before copying it.
    search_text = json.dumps(source_search, ensure_ascii=False, sort_keys=True)
    value_text = json.dumps(source_values, ensure_ascii=False, sort_keys=True)
    for needle in ("/engine/ajax/search.php", '"query": "{query}"', '"page": "1"'):
        if needle not in search_text:
            raise AssertionError(f"voiranime-homes search authority missing {needle}")
    for needle in ("/engine/ajax/manga_episodes_api.php?id={id}", '"role": "detail"'):
        if needle not in value_text:
            raise AssertionError(f"voiranime-homes value authority missing {needle}")

    before = json.dumps(target, ensure_ascii=False, sort_keys=True)

    target["official_hub"] = HUB
    target["official_site"] = SITE
    substitutions = target.get("domain_substitutions")
    if not isinstance(substitutions, dict):
        substitutions = {}
    substitutions["voiranime.diy"] = "voiranime.homes"
    target["domain_substitutions"] = substitutions

    runtime_replacements = target.get("runtime_domain_replacements")
    if not isinstance(runtime_replacements, dict):
        runtime_replacements = {}
    runtime_replacements["voiranime.diy"] = "voiranime.homes"
    target["runtime_domain_replacements"] = runtime_replacements

    target["identity_input"] = copy.deepcopy(source.get("identity_input") or {
        "mode": "catalog_search",
        "requires_tmdb_before_run": True,
        "required_fields": ["title", "mediaType"],
    })
    target["search_request_plan"] = source_search
    target["provider_value_plan"] = source_values
    target["proof_search_bases"] = [SITE]
    target["proof_protected_hosts"] = _unique(
        list(target.get("proof_protected_hosts") or [])
        + list(source.get("proof_protected_hosts") or [])
        + ["vidzy.live", "vidzy.cc"]
    )

    learned = list(target.get("candidate_learned_routes") or [])
    learned.extend([
        "/engine/ajax/search.php",
        "/index.php?newsid={id}",
        "/engine/ajax/manga_episodes_api.php?id={id}",
    ])
    target["candidate_learned_routes"] = _unique(learned)

    notes = target.get("notes")
    if isinstance(notes, str):
        notes = [notes]
    elif not isinstance(notes, list):
        notes = []
    note = (
        f"{MARKER}: official hub {HUB} resolves to {SITE}; reuse the proven "
        "voiranime-homes DLE DATA path (search -> provider-local newsid -> episodes API). "
        "Signed Vidzy/player URLs are runtime output only and are never persisted."
    )
    if note not in notes:
        notes.append(note)
    target["notes"] = notes

    capabilities = data.get("provider_capabilities")
    if isinstance(capabilities, dict) and isinstance(capabilities.get(TARGET), dict):
        cap = capabilities[TARGET]
        origins = list(cap.get("observed_origins") or [])
        cap["observed_origins"] = _unique(origins + [SITE, "https://vidzy.live", "https://vidzy.cc"])

    after = json.dumps(target, ensure_ascii=False, sort_keys=True)
    return before != after


def validate_document(data: dict[str, Any]) -> None:
    patches = data.get("provider_patches") or {}
    target = patches.get(TARGET) or {}
    if target.get("official_hub") != HUB:
        raise AssertionError("VoirAnime official hub changed")
    if target.get("official_site") != SITE:
        raise AssertionError("VoirAnime current site is not voiranime.homes")
    if (target.get("domain_substitutions") or {}).get("voiranime.diy") != "voiranime.homes":
        raise AssertionError("stale voiranime.diy substitution missing")

    search = target.get("search_request_plan") or []
    values = target.get("provider_value_plan") or []
    if not search or not values:
        raise AssertionError("VoirAnime structured search/value plans missing")
    for row in search + values:
        if row.get("semanticTypes") != ["anime"]:
            raise AssertionError("V21.10 may execute only the currently proven anime lane")

    text = json.dumps(target, ensure_ascii=False, sort_keys=True)
    for needle in (
        "/engine/ajax/search.php",
        "/engine/ajax/manga_episodes_api.php?id={id}",
        "newsid={id}",
        "vidzy.cc",
        MARKER,
    ):
        if needle not in text:
            raise AssertionError(f"VoirAnime V21.10 missing {needle}")
    for forbidden in ("master.m3u8?", "embdmstrplayer.com/v2/", "?t=eES", "token="):
        if forbidden.casefold() in text.casefold():
            raise AssertionError(f"ephemeral player/media value persisted: {forbidden}")


def main() -> int:
    data = json.loads(OVERRIDES.read_text(encoding="utf-8"))
    changed = apply_document(data)
    validate_document(data)
    if changed:
        OVERRIDES.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"PROVIDER_VOIRANIME_HOMES_AUTHORITY_V21_10_OK changed={str(changed).lower()} "
        "hub_address_only=1 homes_dle_reused=1 provider_local_newsid=1 signed_media_persisted=0 "
        "anime_lane_only_until_live_movie_proof=1"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
