#!/usr/bin/env python3
"""Make typed resolver execution authority match positive terminal proof.

A provider may expose a typed TMDB endpoint for more than one media type while only
one type is currently productive.  The executable recipe must not retain a zero-
stream sibling route: doing so prevents the V7 classifier from recognizing the
positive typed lane and can leave ProviderBase behind the generic recipe gates.

This migration is deliberately narrow:
- for recipes without a search phase, movie/episode candidates must be terminal
  requests from positive tasks;
- search-based/multi-hop recipe selection is unchanged;
- a proof-classified typed resolver owns identity input and therefore uses TMDB
  directly instead of inheriting stale catalogue-search routes from older DATA.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECOVERY = ROOT / "scripts" / "recover_provider_routes_from_upstreams.py"
MATERIALIZER = ROOT / "scripts" / "materialize_provider_v3_all.py"
RECOVERY_MARKER = "ROUTE_RECOVERY_TYPED_POSITIVE_ONLY_V8"
IDENTITY_MARKER = "PROVIDER_TYPED_RESOLVER_IDENTITY_V8"


def once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise AssertionError(f"{label}: expected one anchor, got {count}")
    return text.replace(old, new, 1)


def patch_recovery() -> bool:
    text = RECOVERY.read_text(encoding="utf-8")
    if RECOVERY_MARKER in text:
        validate_recovery(text)
        return False
    if "ROUTE_RECOVERY_BODY_SEARCH_RECIPE_V6" not in text or "ROUTE_RECOVERY_TYPED_RESOLVER_API_V7" not in text:
        raise AssertionError("V8 requires V6 causal recipe and V7 typed classifier migrations first")

    anchor = "def build_simple_api_recipe(records: list[dict[str, Any]]) -> dict[str, Any] | None:\n"
    helper = '''# ROUTE_RECOVERY_TYPED_POSITIVE_ONLY_V8\ndef _typed_terminal_positive(row: dict[str, Any]) -> bool:\n    return bool(\n        (int(row.get("taskStreamCount") or 0) > 0 or int(row.get("taskRawStreamCount") or 0) > 0)\n        and row.get("taskLastRequestIndex") is not None\n        and int(row.get("requestIndex") or 0) == int(row.get("taskLastRequestIndex"))\n        and row.get("requestSpecReusable") is True\n        and row.get("providerValueCorrelation") is not True\n    )\n\n\n'''
    text = once(text, anchor, helper + anchor, "typed-positive-helper")

    text = once(
        text,
        '''        if _repair_recipe_origin_allowed(row)\n        and row.get("semanticType") == "movie"\n''',
        '''        if _repair_recipe_origin_allowed(row)\n        and row.get("semanticType") == "movie"\n        and (search is not None or _typed_terminal_positive(row))\n''',
        "movie-positive-terminal",
    )
    text = once(
        text,
        '''        if _repair_recipe_origin_allowed(row)\n        and row.get("semanticType") == "tv"\n''',
        '''        if _repair_recipe_origin_allowed(row)\n        and row.get("semanticType") == "tv"\n        and (search is not None or _typed_terminal_positive(row))\n''',
        "episode-positive-terminal",
    )

    RECOVERY.write_text(text, encoding="utf-8")
    validate_recovery(text)
    return True


def patch_materializer() -> bool:
    text = MATERIALIZER.read_text(encoding="utf-8")
    if IDENTITY_MARKER in text:
        validate_materializer(text)
        return False
    anchor = '''def identity_input(\n    patch: dict[str, Any],\n    routes: list[str] | None = None,\n    api_recipe: dict[str, Any] | None = None,\n) -> dict[str, Any]:\n    raw = patch.get("identity_input")\n'''
    replacement = '''def identity_input(\n    patch: dict[str, Any],\n    routes: list[str] | None = None,\n    api_recipe: dict[str, Any] | None = None,\n) -> dict[str, Any]:\n    # PROVIDER_TYPED_RESOLVER_IDENTITY_V8\n    # Fresh terminal stream proof for a typed TMDB resolver is stronger than\n    # stale catalogue/search routes carried as historical candidate knowledge.\n    if isinstance(api_recipe, dict) and str(api_recipe.get("recipeKind") or "") == "typed-resolver-api":\n        return {\n            "mode": "tmdb_direct",\n            "requiresTmdbBeforeRun": False,\n            "requiredFields": ["tmdbId", "mediaType"],\n        }\n    raw = patch.get("identity_input")\n'''
    text = once(text, anchor, replacement, "typed-identity-authority")
    MATERIALIZER.write_text(text, encoding="utf-8")
    validate_materializer(text)
    return True


def validate_recovery(text: str | None = None) -> None:
    value = text if text is not None else RECOVERY.read_text(encoding="utf-8")
    for needle in (
        RECOVERY_MARKER,
        "def _typed_terminal_positive",
        "and (search is not None or _typed_terminal_positive(row))",
        'recipe["recipeKind"] = "typed-resolver-api"',
    ):
        if needle not in value:
            raise AssertionError(f"V8 recovery missing: {needle}")
    if value.count("and (search is not None or _typed_terminal_positive(row))") != 2:
        raise AssertionError("V8 typed positive gate must cover movie and episode candidates exactly")


def validate_materializer(text: str | None = None) -> None:
    value = text if text is not None else MATERIALIZER.read_text(encoding="utf-8")
    for needle in (
        IDENTITY_MARKER,
        'str(api_recipe.get("recipeKind") or "") == "typed-resolver-api"',
        '"mode": "tmdb_direct"',
        '"requiresTmdbBeforeRun": False',
        '["tmdbId", "mediaType"]',
    ):
        if needle not in value:
            raise AssertionError(f"V8 materializer missing: {needle}")


def main() -> int:
    changed = patch_recovery() | patch_materializer()
    validate_recovery()
    validate_materializer()
    print(
        f"PROVIDER_REPAIR_V8_OK changed={str(changed).lower()} "
        "typed_zero_route_rejected=1 typed_positive_terminal_required=1 "
        "typed_identity_tmdb_direct=1 search_multihop_unchanged=1"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
