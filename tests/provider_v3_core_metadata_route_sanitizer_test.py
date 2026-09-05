#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from sanitize_provider_v3_core_metadata_routes import (  # noqa: E402
    derive_runtime_family,
    is_tmdb_url_or_route,
)

KNOWLEDGE = ROOT / "automation" / "provider-v3-static-knowledge.json"
TMDB_ROUTE = re.compile(
    r"api\.themoviedb\.org|themoviedb\.org|^/api\.themoviedb\.org|"
    r"^/3(?:/?$|/(?:movie|tv|find)(?:/|$))|"
    r"(?:api_key=|tmdb_api_key|tmdb_access_token).*tmdb",
    re.I,
)


def iter_strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for child in value:
            yield from iter_strings(child)
    elif isinstance(value, dict):
        for child in value.values():
            yield from iter_strings(child)


def unit_contract() -> None:
    assert is_tmdb_url_or_route("https://api.themoviedb.org/3/tv/123?api_key=secret")
    assert is_tmdb_url_or_route("/api.themoviedb.org/3/movie/{tmdbId}")
    assert is_tmdb_url_or_route("/3/")
    assert is_tmdb_url_or_route("/3/tv/")
    assert is_tmdb_url_or_route("/3/movie/{tmdbId}")
    assert is_tmdb_url_or_route("/3/find/{imdbId}")
    assert is_tmdb_url_or_route("/tv/{tmdbId}/season/?api_key=${TMDB_API_KEY")
    # Provider-owned API v3 namespaces are not Core TMDB transport.
    assert not is_tmdb_url_or_route("/api/3/tv/{id}")

    assert derive_runtime_family({
        "strategy": "api_stream_resolver",
        "sourceRuntimeFamily": "unknown",
        "routes": ["/api/search?q={query}", "/api/source/{id}"],
    }) == "catalogue-json-html-detail"
    assert derive_runtime_family({
        "strategy": "mixed_embed_resolver",
        "sourceRuntimeFamily": "unknown",
        "routes": ["/watch/{slug}", "/embed/{id}"],
    }) == "catalogue-html-embed"
    assert derive_runtime_family({
        "strategy": "direct_media",
        "sourceRuntimeFamily": "unknown",
        "routes": ["/moviebox/{media}/{id}"],
    }) == "tmdb-direct-api"
    assert derive_runtime_family({
        "strategy": "html_scraper",
        "sourceRuntimeFamily": "unknown",
        "routes": ["/movie/{slug}"],
    }) == "catalogue-html"
    assert derive_runtime_family({
        "strategy": "quarantined",
        "sourceRuntimeFamily": "unknown",
        "routes": [],
    }) == "unknown"


def main() -> int:
    unit_contract()
    payload = json.loads(KNOWLEDGE.read_text(encoding="utf-8"))
    providers = payload.get("providers")
    assert isinstance(providers, dict) and len(providers) == 96
    assert payload.get("coreMetadataTransportSanitized") is True
    assert payload.get("coreMetadataTransportOwner") == "core"
    assert payload.get("runtimeFamilyFinalized") is True

    offenders = []
    active_unknown = []
    for provider_id, row in providers.items():
        model = row.get("model") if isinstance(row, dict) else None
        knowledge = row.get("knowledge") if isinstance(row, dict) else None
        for section_name, section in (("model", model), ("knowledge", knowledge)):
            if not isinstance(section, dict):
                continue
            for key in ("routes", "routeFragments", "observedUrls", "origins"):
                if key not in section:
                    continue
                for raw in iter_strings(section.get(key)):
                    text = raw.strip().replace("\\/", "/")
                    if is_tmdb_url_or_route(text) or TMDB_ROUTE.search(text):
                        offenders.append((provider_id, section_name, key, raw))
        recipe = model.get("apiRecipe") if isinstance(model, dict) else None
        if isinstance(recipe, dict):
            for raw in iter_strings(recipe):
                if is_tmdb_url_or_route(raw):
                    offenders.append((provider_id, "model", "apiRecipe", raw))
        if isinstance(model, dict):
            strategy = str(model.get("strategy") or "unknown").strip().casefold()
            family = str(model.get("sourceRuntimeFamily") or "unknown").strip().casefold()
            if strategy != "quarantined" and family == "unknown":
                active_unknown.append(provider_id)

    assert not offenders, "Core-owned TMDB transport leaked into Provider DATA: " + repr(offenders[:12])
    assert not active_unknown, "active Provider DATA still has unknown family: " + repr(active_unknown)
    print(
        "PROVIDER_V3_CORE_METADATA_ROUTE_SANITIZER_TEST_OK "
        "providers=96 tmdb_owner=core active_unknown=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
