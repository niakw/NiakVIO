#!/usr/bin/env python3
from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import provider_upstream_semantic_guard as guard

thor = {"title": "Thor", "year": 2011, "mediaType": "movie"}
assert guard.coflix_candidate_matches_fixture("thor-vf", thor)
assert guard.coflix_candidate_matches_fixture("thor-vostfr", thor)
assert guard.coflix_candidate_matches_fixture("thor-2011-vf", thor)
assert not guard.coflix_candidate_matches_fixture("hulk-vs-thor-vf", thor)
assert not guard.coflix_candidate_matches_fixture("thor-love-and-thunder-vf", thor)
assert not guard.coflix_candidate_matches_fixture("thor-god-of-thunder-vf", thor)

hotd = {"title": "House of the Dragon", "year": 2022, "mediaType": "tv"}
assert guard._norm("House of the Dragon") == "house of the dragon"
assert guard._url_route_key("https://vidzy.org/embed-x94wdxjln7ay.html") == "vidzy.org/embed-x94wdxjln7ay.html"

print("PROVIDER_UPSTREAM_SEMANTIC_GUARD_TEST_OK")
