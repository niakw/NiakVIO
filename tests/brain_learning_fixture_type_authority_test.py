#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import run_brain_learning_queue as queue  # noqa: E402

empty_candidate = {"metadata": {}}
anime_manifest = {
    "scrapers": [
        {"id": "AnimeSalt", "types": ["anime", "tv"]},
        {"id": "moviebox", "types": ["movie", "tv"]},
    ]
}
assert queue.declared_type(
    "animesalt",
    empty_candidate,
    manifest=anime_manifest,
    census={},
) == "anime"
assert queue.declared_type(
    "moviebox",
    empty_candidate,
    manifest=anime_manifest,
    census={},
) == "movie"

# Current census lanes are the fallback catalogue authority when a provider is
# temporarily absent from a filtered manifest.
assert queue.declared_type(
    "animevost-fr",
    empty_candidate,
    manifest={"scrapers": []},
    census={"providers": [{"provider": "animevost-fr", "declaredLanes": ["anime", "tv"]}]},
) == "anime"

# Candidate metadata is only the final fallback; missing metadata must never
# silently become movie.
assert queue.declared_type(
    "tv-only",
    {"metadata": {"supportedTypes": ["tv"]}},
    manifest={"scrapers": []},
    census={"providers": []},
) == "tv"
try:
    queue.declared_type(
        "unknown",
        empty_candidate,
        manifest={"scrapers": []},
        census={"providers": []},
    )
except ValueError as exc:
    assert "no authoritative declared media type" in str(exc), exc
else:
    raise AssertionError("unknown Learning provider silently defaulted to movie")

config = {
    "fixtures": {
        "movie": [{"label": "Oppenheimer", "mediaType": "movie"}],
        "anime": [{"label": "Hell Mode S01E01", "mediaType": "anime"}],
    }
}
state = {}
fixture = queue.choose_fixture(config, state, "anime")
assert fixture["mediaType"] == "anime"
assert fixture["label"] == "Hell Mode S01E01"

try:
    queue.choose_fixture(
        {"fixtures": {"movie": [{"label": "Oppenheimer", "mediaType": "movie"}]}},
        {},
        "anime",
    )
except ValueError as exc:
    assert "no Learning fixtures for declared type: anime" in str(exc), exc
else:
    raise AssertionError("anime Learning silently fell back to a movie fixture")

print("Brain Learning fixture media-type authority contract passed")
