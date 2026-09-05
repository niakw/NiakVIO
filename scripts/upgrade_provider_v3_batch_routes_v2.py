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


def _load() -> dict[str, Any]:
    value = json.loads(OVERRIDES.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError("provider-overrides.json must be an object")
    patches = value.get("provider_patches")
    if not isinstance(patches, dict):
        raise AssertionError("provider-overrides.json missing provider_patches")
    return value


def _row(patches: dict[str, Any], provider_id: str) -> dict[str, Any]:
    row = patches.get(provider_id)
    if not isinstance(row, dict):
        raise AssertionError(f"missing provider patch row: {provider_id}")
    return row


def patch() -> bool:
    value = _load()
    patches = value["provider_patches"]
    before = json.dumps(value, ensure_ascii=False, sort_keys=True)

    # AnimeSama.co is a current DLE-style site distinct from anime-sama.to/store.
    # The old /film/episode-1.html + template-php fetch plan is live-404. Keep
    # current observed detail/season/episode shapes as candidates; the batch probe
    # must execute them before any route can become final authority.
    animesama = _row(patches, "animesama-co")
    animesama["official_site"] = "https://animesama.co"
    animesama["published_types"] = ["movie", "anime"]
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

    # AnimeZeY's operator-published alternate worker is current and the old
    # /1:search plan cannot execute because it has no query identity. /0:search?q=
    # is an operator-observed search shape. It remains candidate DATA until the
    # runtime probe reaches it and proves coherent output.
    animezey = _row(patches, "animezey")
    animezey["official_site"] = "https://1.animezeydl.workers.dev"
    animezey["published_types"] = ["movie", "tv"]
    animezey["identity_input"] = {
        "mode": "catalog_search",
        "requires_tmdb_before_run": True,
        "required_fields": ["title", "year", "mediaType"],
    }
    animezey["learned_urls"] = ["https://1.animezeydl.workers.dev/"]
    animezey["learned_routes"] = [
        "/0:search?q={query}",
        "/download.aspx",
    ]
    animezey["domain_substitutions"] = {
        "1.animezey23112022.workers.dev": "1.animezeydl.workers.dev",
        "animezey16082023.animezey16082023.workers.dev": "1.animezeydl.workers.dev",
    }
    animezey["output_url_host_rewrites"] = [
        {
            "fromHost": "animezey16082023.animezey16082023.workers.dev",
            "toHost": "1.animezeydl.workers.dev",
        }
    ]

    # AniMoFlix is currently HTTP-blocked on its known terminal. Do not invent a
    # replacement host. Remove only route templates that were observed rendering
    # empty placeholders (e.g. /saison-//episode-/), so diagnostics spend their
    # budget on syntactically valid provider paths.
    animoflix = _row(patches, "animoflix")
    animoflix["learned_routes"] = [
        "/?s={query}",
        "/anime/{slug}/",
        "/anime/{slug}/film/",
        "/anime/{slug}/episode-{episode}/",
        "/anime/{slug}/saison-{season}/episode-{episode}/",
    ]

    after = json.dumps(value, ensure_ascii=False, sort_keys=True)
    changed = after != before
    if changed:
        OVERRIDES.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return changed


def validate() -> None:
    value = _load()
    patches = value["provider_patches"]

    animesama = _row(patches, "animesama-co")
    if animesama.get("official_site") != "https://animesama.co":
        raise AssertionError("animesama-co: current .co terminal not selected")
    stale = {"/film/episode-{episode}.html", "/template-php/defaut/fetch.php"}
    if stale.intersection(set(animesama.get("learned_routes") or [])):
        raise AssertionError("animesama-co: stale live-404 routes survived")
    if "/anime/{id}-{slug}/saison-{season}/episode-{episode}.html" not in (animesama.get("learned_routes") or []):
        raise AssertionError("animesama-co: current episode route missing")

    animezey = _row(patches, "animezey")
    if animezey.get("official_site") != "https://1.animezeydl.workers.dev":
        raise AssertionError("animezey: current alternate worker not selected")
    routes = list(animezey.get("learned_routes") or [])
    if "/0:search?q={query}" not in routes or "/1:search" in routes:
        raise AssertionError("animezey: executable search identity route not normalized")

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
        f"changed={str(changed).lower()} providers=animesama-co,animezey,animoflix "
        "livePromotion=false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
