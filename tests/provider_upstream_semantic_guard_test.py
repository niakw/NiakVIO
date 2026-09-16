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

assert guard._norm("House of the Dragon") == "house of the dragon"
assert guard._url_route_key("https://vidzy.org/embed-x94wdxjln7ay.html") == "vidzy.embed/embed-x94wdxjln7ay.html"
assert guard._url_route_key("https://vidzy.live/embed-x94wdxjln7ay.html") == "vidzy.embed/embed-x94wdxjln7ay.html"
assert guard._url_route_key("https://u14.vidzy.cc/hls2/a/b/master.m3u8") == "u14.vidzy.cc/hls2/a/b/master.m3u8"

print("PROVIDER_UPSTREAM_SEMANTIC_GUARD_TEST_OK")
