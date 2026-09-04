#!/usr/bin/env python3
"""Remove Core-owned TMDB transport details from Provider v3 static DATA.

Provider DATA may describe the provider's own request chain, but TMDB metadata
lookup and credentials belong to Core. Static extraction from upstream provider
JavaScript can otherwise leak TMDB request fragments into provider routes and
make the generic reader misclassify them as provider endpoints.

Bare ``/3/movie|tv/...`` fragments are ambiguous in isolation, so they are only
removed when the same provider row contains explicit TMDB transport evidence
(host/api-key URL). This avoids deleting a legitimate provider API v3 route.
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
    if is_explicit_tmdb_transport(text):
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
    for provider_id, row in providers.items():
        if not isinstance(row, dict):
            continue
        local_removed = 0
        model = row.get("model") if isinstance(row.get("model"), dict) else {}
        knowledge = row.get("knowledge") if isinstance(row.get("knowledge"), dict) else {}

        # Correlate ambiguous /3/movie|tv fragments with explicit TMDB evidence
        # from the same extracted provider row before deleting that evidence.
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

        row["model"] = model
        row["knowledge"] = knowledge
        if local_removed:
            touched += 1
            removed += local_removed
        if explicit_tmdb_evidence and bare_before:
            bare_route_touched += 1

    payload["coreMetadataTransportSanitized"] = True
    payload["coreMetadataTransportOwner"] = "core"
    payload["coreMetadataBareRoutePolicy"] = "strip-only-with-explicit-tmdb-evidence"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        "PROVIDER_V3_CORE_METADATA_ROUTE_SANITIZE_OK "
        f"providers={len(providers)} touched={touched} removed={removed} "
        f"bare_route_touched={bare_route_touched} tmdb_owner=core"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
