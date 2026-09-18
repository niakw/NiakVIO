#!/usr/bin/env python3
"""Evidence-backed route/DATA refresh for Provider v3 slice #19-#28.

This migration is intentionally declarative. It does not mark a route live and it
never converts a blocked/HTTP-only observation into provider validation. The next
batch probe remains the authority for execution and final type proof.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OVERRIDES = ROOT / "provider-overrides.json"
MANIFEST = ROOT / "manifest.json"


def _load() -> dict[str, Any]:
    value = json.loads(OVERRIDES.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError("provider-overrides.json must be an object")
    patches = value.get("provider_patches")
    if not isinstance(patches, dict):
        raise AssertionError("provider-overrides.json missing provider_patches")
    return value


def _current_provider_ids() -> set[str]:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    return {
        str(row.get("id") or "").strip().casefold()
        for row in manifest.get("scrapers") or []
        if isinstance(row, dict) and str(row.get("id") or "").strip()
    }


def _row(patches: dict[str, Any], provider_id: str) -> dict[str, Any]:
    row = patches.get(provider_id)
    if not isinstance(row, dict):
        raise AssertionError(f"missing provider patch row: {provider_id}")
    return row


def patch() -> bool:
    value = _load()
    patches = value["provider_patches"]
    current = _current_provider_ids()
    before = json.dumps(value, ensure_ascii=False, sort_keys=True)

    if "animesama-co" in current:
        animesama = _row(patches, "animesama-co")
        animesama["official_site"] = "https://animesama.co"
        animesama["published_types"] = ["anime"]
        animesama["identity_input"] = {
            "mode": "catalog_search",
            "requires_tmdb_before_run": True,
            "required_fields": ["title", "year", "mediaType"],
        }
        animesama["learned_urls"] = ["https://animesama.co/"]
        animesama["learned_routes"] = [
            "/catalogue/?search={query}",
            "/anime/{id}-{slug}.html",
            "/anime/{id}-{slug}/saison-{season}.html",
            "/anime/{id}-{slug}/saison-{season}/episode-{episode}.html",
        ]
        substitutions = animesama.get("domain_substitutions")
        substitutions = dict(substitutions) if isinstance(substitutions, dict) else {}
        substitutions["anime-sama.store"] = "animesama.co"
        animesama["domain_substitutions"] = substitutions

    if "animezey" in current:
        animezey = _row(patches, "animezey")
        animezey["official_site"] = "https://1.animezeydl.workers.dev"
        animezey["published_types"] = ["movie", "tv"]
        animezey["identity_input"] = {
            "mode": "catalog_search",
            "requires_tmdb_before_run": True,
            "required_fields": ["title", "year", "mediaType"],
        }
        animezey["learned_urls"] = ["https://1.animezeydl.workers.dev/"]
        animezey["learned_routes"] = ["/0:search?q={query}", "/download.aspx"]
        animezey["domain_substitutions"] = {
            "1.animezey23112022.workers.dev": "1.animezeydl.workers.dev",
            "animezey16082023.animezey16082023.workers.dev": "1.animezeydl.workers.dev",
        }
        animezey["output_url_host_rewrites"] = [{
            "fromHost": "animezey16082023.animezey16082023.workers.dev",
            "toHost": "1.animezeydl.workers.dev",
        }]

    if "animoflix" in current:
        animoflix = _row(patches, "animoflix")
        animoflix["learned_routes"] = [
            "/?s={query}",
            "/anime/{slug}/",
            "/anime/{slug}/film/",
            "/anime/{slug}/episode-{episode}/",
            "/anime/{slug}/saison-{season}/episode-{episode}/",
        ]

    changed = json.dumps(value, ensure_ascii=False, sort_keys=True) != before
    if changed:
        OVERRIDES.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return changed


def validate() -> None:
    value = _load()
    patches = value["provider_patches"]
    current = _current_provider_ids()

    if "animesama-co" in current:
        animesama = _row(patches, "animesama-co")
        if animesama.get("official_site") != "https://animesama.co":
            raise AssertionError("animesama-co: current .co terminal not selected")
        if set(animesama.get("published_types") or []) != {"anime"}:
            raise AssertionError("animesama-co: historical movie lane survived current canonical capability")
        stale = {"/film/episode-{episode}.html", "/template-php/defaut/fetch.php"}
        if stale.intersection(set(animesama.get("learned_routes") or [])):
            raise AssertionError("animesama-co: stale live-404 routes survived")
        if "/anime/{id}-{slug}/saison-{season}/episode-{episode}.html" not in (animesama.get("learned_routes") or []):
            raise AssertionError("animesama-co: current episode route missing")

    if "animezey" in current:
        animezey = _row(patches, "animezey")
        if animezey.get("official_site") != "https://1.animezeydl.workers.dev":
            raise AssertionError("animezey: current alternate worker not selected")
        routes = list(animezey.get("learned_routes") or [])
        if "/0:search?q={query}" not in routes or "/1:search" in routes:
            raise AssertionError("animezey: executable search identity route not normalized")

    if "animoflix" in current:
        animoflix = _row(patches, "animoflix")
        for route in animoflix.get("learned_routes") or []:
            text = str(route)
            if "saison-//" in text or "episode-/" in text or "/anime//" in text:
                raise AssertionError(f"animoflix: malformed empty-placeholder route survived: {text}")


def main() -> int:
    changed = patch()
    validate()
    print(
        "PROVIDER_V3_BATCH_ROUTES_V2_OK "
        f"changed={str(changed).lower()} providers=" + ",".join(sorted(_current_provider_ids() & {"animesama-co","animezey","animoflix"})) + " "
        "livePromotion=false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
