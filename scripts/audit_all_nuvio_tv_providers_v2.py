#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from typing import Any

import audit_all_nuvio_tv_providers as base


base.OUTPUT_PATH = base.ROOT / "automation" / "nuvio-tv-global-audit-v2.json"
base.CANDIDATE_PATH = base.ROOT / "automation" / "nuvio-tv-global-candidates-v2.json"
base.STAGING = base.ROOT / "staging" / "nuvio-tv-global-audit-v2"


def fixtures_for(row: dict[str, Any], config: dict[str, Any]) -> list[dict[str, Any]]:
    supported = {
        str(value).strip().casefold()
        for value in (row.get("supportedTypes") or row.get("types") or [])
        if str(value).strip()
    }
    identity = " ".join(
        str(row.get(key) or "")
        for key in ("id", "name", "displayName", "description")
    )

    categories: list[str] = []
    if "movie" in supported:
        categories.append("movie")
    if "tv" in supported:
        categories.append("tv")
    if "anime" in supported:
        categories.append("anime")

    # Some upstream manifests omit or mislabel anime as TV. Preserve a single
    # anime probe only when the declared types do not already give us coverage.
    if not categories:
        if base.ANIME_HINT.search(identity):
            categories.append("anime")
        else:
            categories.extend(("movie", "tv"))

    fixtures: list[dict[str, Any]] = []
    seen: set[tuple[Any, ...]] = set()
    for category in categories:
        fixture = base.first_fixture(config, category)
        key = (
            fixture.get("tmdbId"),
            fixture.get("mediaType"),
            fixture.get("season"),
            fixture.get("episode"),
            category,
        )
        if key in seen:
            continue
        seen.add(key)
        fixtures.append(fixture)
    return fixtures[:3]


base.fixtures_for = fixtures_for


if __name__ == "__main__":
    raise SystemExit(base.main())
