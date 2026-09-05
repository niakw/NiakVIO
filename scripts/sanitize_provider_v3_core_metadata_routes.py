#!/usr/bin/env python3
"""Remove Core-owned TMDB transport details from Provider v3 static DATA.

Provider DATA may describe the provider's own request chain, but TMDB metadata
lookup and credentials belong to Core. Static extraction from upstream provider
JavaScript can otherwise leak TMDB request fragments into provider routes and
make the generic reader misclassify them as provider endpoints.

This sanitizer also finalizes a deterministic generic runtime family when the
static extractor left an active provider at ``unknown`` despite having enough
strategy/route DATA to select the common ProviderBase reader safely.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_KNOWLEDGE = ROOT / "automation" / "provider-v3-static-knowledge.json"
TMDB_HOSTS = frozenset({"api.themoviedb.org", "www.themoviedb.org", "themoviedb.org"})
TMDB_ERASED_HOST_RE = re.compile(r"^/+(?:api\.)?themoviedb\.org(?:/|$)", re.I)
TMDB_API_ROUTE_RE = re.compile(
    r"^/3/(?:\{media\}|\{type\}|movie|tv)/\{tmdb(?:_?id)?\}.*(?:[?&])api_key=",
    re.I,
)
TMDB_BARE_API_ROUTE_RE = re.compile(
    r"^/3/(?:\{media\}|\{type\}|movie|tv)/(?:\{tmdb(?:_?id)?\}|\d+)(?:[/?#]|$)",
    re.I,
)
# Exact TMDB v3 path stubs are non-executable provider DATA even after the
# original host/expression was lost by historical static extraction.  A real
# provider endpoint such as /api/3/tv/... is deliberately not matched.
TMDB_CANONICAL_STUB_RE = re.compile(
    r"^/3(?:/?$|/(?:movie|tv|find)(?:/|$))",
    re.I,
)
TMDB_CREDENTIAL_TOKEN_RE = re.compile(r"(?:api_key=|tmdb_api_key|tmdb_access_token|\$\{tmdb_api_key)", re.I)
SEARCH_ROUTE_RE = re.compile(
    r"\{query\}|/(?:search|recherche)(?:[/?#]|$)|[?&](?:s|q|query|keyword|search|story)=|/template-php/[^?#]*fetch\.php",
    re.I,
)
PLAYER_ROUTE_RE = re.compile(r"/(?:player|embed|play|watch|video)(?:[/?#.-]|$)", re.I)
API_ROUTE_RE = re.compile(r"/(?:api|v\d+)(?:[/?#.-]|$)", re.I)
DIRECT_ROUTE_RE = re.compile(
    r"\{(?:tmdbid|tmdb_id|media|type)\}|(?:[?&])tmdb=|/(?:stream|streams|source|sources)(?:[/?#.-]|$)",
    re.I,
)
FORM_ROUTE_RE = re.compile(r"/template-php/[^?#]*fetch\.php(?:[?#]|$)", re.I)


def load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: object required")
    return payload


def iter_strings(value: object) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for child in value:
            yield from iter_strings(child)
    elif isinstance(value, dict):
        for child in value.values():
            yield from iter_strings(child)


def normalized(value: object) -> str:
    return str(value or "").strip().replace("\\/", "/")


def is_explicit_tmdb_transport(value: object) -> bool:
    text = normalized(value)
    if not text:
        return False
    low = text.casefold()
    if "api.themoviedb.org" in low or "themoviedb.org" in low:
        return True
    if TMDB_ERASED_HOST_RE.match(text):
        return True
    if TMDB_API_ROUTE_RE.search(text):
        return True
    try:
        parsed = urlsplit(text)
    except ValueError:
        return False
    return str(parsed.hostname or "").casefold() in TMDB_HOSTS


def is_tmdb_url_or_route(value: object, *, strip_bare_api_route: bool = False) -> bool:
    text = normalized(value)
    if not text:
        return False
    if is_explicit_tmdb_transport(text):
        return True
    # Historical extraction sometimes erased the TMDB host and even the final
    # JS template expression, leaving only /3/tv/, /3/movie/, /3/find/ or /3/.
    # Those canonical stubs are never useful executable Provider DATA.
    if TMDB_CANONICAL_STUB_RE.match(text):
        return True
    if TMDB_CREDENTIAL_TOKEN_RE.search(text) and ("/3/" in text or "tmdb" in text.casefold()):
        return True
    return bool(strip_bare_api_route and TMDB_BARE_API_ROUTE_RE.search(text))


def clean_list(values: object, *, strip_bare_api_routes: bool = False) -> tuple[list[str], int]:
    if not isinstance(values, list):
        return [], 0
    out: list[str] = []
    removed = 0
    for raw in values:
        text = str(raw or "").strip()
        if not text:
            continue
        if is_tmdb_url_or_route(text, strip_bare_api_route=strip_bare_api_routes):
            removed += 1
            continue
        if text not in out:
            out.append(text)
    return out, removed


def assert_recipe_is_provider_owned(provider_id: str, recipe: object, *, strip_bare_api_routes: bool = False) -> None:
    if not isinstance(recipe, dict):
        return
    for key, raw in recipe.items():
        if isinstance(raw, str) and is_tmdb_url_or_route(raw, strip_bare_api_route=strip_bare_api_routes):
            raise AssertionError(
                f"{provider_id}: apiRecipe.{key} contains Core-owned TMDB transport: {raw}"
            )


def derive_runtime_family(model: dict[str, Any]) -> str:
    current = str(model.get("sourceRuntimeFamily") or "unknown").strip().casefold() or "unknown"
    if current != "unknown":
        return current
    strategy = str(model.get("strategy") or "unknown").strip().casefold()
    if strategy == "quarantined":
        return "unknown"

    routes = [str(value or "").strip() for value in model.get("routes") or [] if str(value or "").strip()]
    joined = "\n".join(routes)
    recipe = model.get("apiRecipe") if isinstance(model.get("apiRecipe"), dict) else None
    has_search = bool(SEARCH_ROUTE_RE.search(joined))
    has_player = bool(PLAYER_ROUTE_RE.search(joined))
    has_api = bool(API_ROUTE_RE.search(joined))
    has_direct = bool(DIRECT_ROUTE_RE.search(joined))
    has_form = bool(FORM_ROUTE_RE.search(joined))

    if has_form:
        return "catalogue-form-html-embed" if has_player or strategy in {"mixed_embed_resolver", "iframe_player"} else "catalogue-form-html"
    if has_search:
        if strategy == "api_stream_resolver" or "/api/search" in joined.casefold():
            return "catalogue-json-html-detail"
        if has_player or strategy in {"mixed_embed_resolver", "iframe_player"}:
            return "catalogue-html-embed"
        return "catalogue-html"
    if recipe:
        return "tmdb-direct-api"
    # Some known API resolvers (Cineby/VidEasy) use endpoint names such as
    # /seed and /cdn/sources-with-title rather than a literal /api prefix.
    # Strategy ownership plus a non-empty route plan is sufficient here.
    if strategy == "api_stream_resolver" and routes:
        return "tmdb-direct-api"
    if strategy in {"mixed_embed_resolver", "iframe_player"} and routes:
        return "catalogue-html-embed"
    if strategy == "html_scraper" and routes:
        return "catalogue-html"
    if strategy == "direct_media" and routes:
        return "tmdb-direct-api" if has_direct or has_api else "catalogue-html"
    if strategy == "official_domain_hub" and routes:
        return "catalogue-html"
    return "unknown"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--knowledge", type=Path, default=DEFAULT_KNOWLEDGE)
    args = parser.parse_args()
    path = args.knowledge.resolve()
    payload = load(path)
    providers = payload.get("providers")
    if not isinstance(providers, dict) or len(providers) != 96:
        raise ValueError("expected durable knowledge for exactly 96 providers")

    removed = 0
    touched = 0
    bare_route_touched = 0
    family_derived = 0
    unresolved_active: list[str] = []
    for provider_id, row in providers.items():
        if not isinstance(row, dict):
            continue
        local_removed = 0
        model = row.get("model") if isinstance(row.get("model"), dict) else {}
        knowledge = row.get("knowledge") if isinstance(row.get("knowledge"), dict) else {}

        # Correlate ambiguous historical routes with explicit evidence, while
        # canonical TMDB v3 stubs are always removed by clean_list().
        explicit_tmdb_evidence = any(
            is_explicit_tmdb_transport(raw)
            for raw in iter_strings({"model": model, "knowledge": knowledge})
        )
        bare_before = sum(
            1
            for raw in iter_strings({"model": model, "knowledge": knowledge})
            if TMDB_BARE_API_ROUTE_RE.search(normalized(raw))
            and not is_explicit_tmdb_transport(raw)
        )

        for container, key in (
            (model, "routes"),
            (model, "observedUrls"),
            (model, "origins"),
            (knowledge, "routes"),
            (knowledge, "routeFragments"),
            (knowledge, "observedUrls"),
        ):
            cleaned, count = clean_list(
                container.get(key),
                strip_bare_api_routes=explicit_tmdb_evidence,
            )
            if isinstance(container.get(key), list):
                container[key] = cleaned
            local_removed += count

        assert_recipe_is_provider_owned(
            provider_id,
            model.get("apiRecipe"),
            strip_bare_api_routes=explicit_tmdb_evidence,
        )

        before_family = str(model.get("sourceRuntimeFamily") or "unknown").strip().casefold() or "unknown"
        after_family = derive_runtime_family(model)
        if before_family == "unknown" and after_family != "unknown":
            model["sourceRuntimeFamily"] = after_family
            if str(knowledge.get("runtimeFamily") or "unknown").strip().casefold() == "unknown":
                knowledge["runtimeFamily"] = after_family
            family_derived += 1
        strategy = str(model.get("strategy") or "unknown").strip().casefold()
        if strategy != "quarantined" and str(model.get("sourceRuntimeFamily") or "unknown").strip().casefold() == "unknown":
            unresolved_active.append(provider_id)

        row["model"] = model
        row["knowledge"] = knowledge
        if local_removed:
            touched += 1
            removed += local_removed
        if explicit_tmdb_evidence and bare_before:
            bare_route_touched += 1

    if unresolved_active:
        raise AssertionError(
            "active Provider DATA still has unknown sourceRuntimeFamily: "
            + ",".join(sorted(unresolved_active))
        )

    payload["coreMetadataTransportSanitized"] = True
    payload["coreMetadataTransportOwner"] = "core"
    payload["coreMetadataBareRoutePolicy"] = "canonical-tmdb-v3-stubs-always-strip"
    payload["runtimeFamilyFinalized"] = True
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        "PROVIDER_V3_CORE_METADATA_ROUTE_SANITIZE_OK "
        f"providers={len(providers)} touched={touched} removed={removed} "
        f"bare_route_touched={bare_route_touched} family_derived={family_derived} "
        "active_unknown=0 tmdb_owner=core"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
