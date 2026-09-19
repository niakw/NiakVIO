#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_provider_v3_routes_sequential import derive_observed_route  # noqa: E402


def derive(url: str, fixture: dict):
    return derive_observed_route(
        {"url": url, "final_url": url, "method": "GET"},
        {"fixture": fixture},
    )


route, meta = derive(
    "https://example.test/api?id=1396&type=tv&seasonId=1&episodeId=2",
    {"tmdbId": "1396", "mediaType": "tv", "season": 1, "episode": 2, "title": "Breaking Bad"},
)
assert route == "/api?id={tmdbId}&type=tv&seasonId={season}&episodeId={episode}"
assert meta["reusable"] is True
assert meta["dynamicQueryResidue"] == []

route, meta = derive(
    "https://example.test/cdn/sources?title=Breaking%20Bad&type=tv&tmdbId=1396&year=2008&seed=59620588.XYZ",
    {"tmdbId": "1396", "mediaType": "tv", "title": "Breaking Bad", "year": 2008},
)
assert route is None
assert meta["reusable"] is False
assert {row["key"] for row in meta["dynamicQueryResidue"]} == {"year", "seed"}

route, meta = derive(
    "https://example.test/?tmdbId=157336&type=movie",
    {"tmdbId": "157336", "mediaType": "movie", "title": "Interstellar"},
)
assert route == "/?tmdbId={tmdbId}&type=movie"
assert meta["reusable"] is True
assert meta["dynamicQueryResidue"] == []

print(
    "PROVIDER_V3_DYNAMIC_QUERY_RESIDUE_TEST_OK "
    "season_episode_aliases=abstracted volatile_identity_literals=rejected typed_root=reusable"
)
