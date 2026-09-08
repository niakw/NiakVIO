#!/usr/bin/env python3
"""Classify proof-backed typed resolver APIs and keep the recognition worker compatible.

The classifier is evidence-driven. A typed resolver API is only marked when the
selected movie/episode request uses TMDB identity directly, is reusable, terminal
in a positive task, and does not depend on a value learned from an earlier provider
response. Multi-hop/player/search providers are therefore not flattened.

This migration also applies the safe worker package-resolution fix so temp-copied
upstream providers can resolve NiakVIO's pinned npm dependencies while sensitive
Node built-ins remain blocked.
"""
from __future__ import annotations

from pathlib import Path

import upgrade_provider_worker_module_resolution_v1 as worker_modules

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts" / "recover_provider_routes_from_upstreams.py"
MARKER = "ROUTE_RECOVERY_TYPED_RESOLVER_API_V7"


def once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise AssertionError(f"{label}: expected one anchor, got {count}")
    return text.replace(old, new, 1)


def patch() -> bool:
    text = TARGET.read_text(encoding="utf-8")
    changed = False
    if MARKER not in text:
        anchor = '    route_keys = {"searchRoute", "movieRoute", "episodeRoute", "directRoute"}\n'
        insertion = '''    # ROUTE_RECOVERY_TYPED_RESOLVER_API_V7
    def _typed_resolver_terminal(row: dict[str, Any]) -> bool:
        route = str(row.get("route") or "")
        return bool(
            "{tmdbId}" in route
            and "{id}" not in route
            and row.get("providerValueCorrelation") is not True
            and row.get("requestSpecReusable") is True
            and (int(row.get("taskStreamCount") or 0) > 0 or int(row.get("taskRawStreamCount") or 0) > 0)
            and row.get("taskLastRequestIndex") is not None
            and int(row.get("requestIndex") or 0) == int(row.get("taskLastRequestIndex"))
            and str(row.get("origin") or "").startswith(("http://", "https://"))
        )

    typed_rows: list[dict[str, Any]] = []
    if movie_candidates:
        typed_rows.append(sorted(movie_candidates, key=lambda row: int(row.get("requestIndex") or 0))[-1])
    if episode_candidates:
        typed_rows.append(sorted(episode_candidates, key=lambda row: int(row.get("requestIndex") or 0))[-1])
    if not search and typed_rows and all(_typed_resolver_terminal(row) for row in typed_rows):
        recipe["recipeKind"] = "typed-resolver-api"

''' + anchor
        text = once(text, anchor, insertion, "typed-resolver-classifier")
        TARGET.write_text(text, encoding="utf-8")
        changed = True

    changed = worker_modules.patch() or changed
    validate()
    return changed


def validate(text: str | None = None) -> None:
    value = text if text is not None else TARGET.read_text(encoding="utf-8")
    for needle in (
        MARKER,
        'recipe["recipeKind"] = "typed-resolver-api"',
        'row.get("providerValueCorrelation") is not True',
        'row.get("requestSpecReusable") is True',
        'int(row.get("requestIndex") or 0) == int(row.get("taskLastRequestIndex"))',
        '"{tmdbId}" in route',
    ):
        if needle not in value:
            raise AssertionError(f"typed resolver classifier missing: {needle}")
    worker_modules.validate()


def main() -> int:
    changed = patch()
    print(
        f"PROVIDER_REPAIR_V7_OK changed={str(changed).lower()} "
        "typed_resolver_classifier=1 prior_response_dependency_rejected=1 "
        "terminal_positive_required=1 pinned_worker_packages=1 blocked_builtins_preserved=1"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
