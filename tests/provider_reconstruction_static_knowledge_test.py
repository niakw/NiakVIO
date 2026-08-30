#!/usr/bin/env python3
"""Regression tests for one-shot clean ProviderBase static knowledge reconstruction."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import discover_candidates as discovery  # noqa: E402


alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+/="
source = (
    "const alphabet=" + repr(alphabet) + ";"
    "const a='l3nLyxjJAc1IyxiVC2vHCMnOlW';"  # /search-bar/search/
    "const b='l2fWAs92mq';"                 # /api/v1
    "const c='l2vWAxnVzguV';"               # /episode/
    "const d='l3n0CMvHBs8';"                # /stream/
    "const bad='https://api.pur/';"
    "const good='https://api.purstream.id/api/v1';"
).encode()

knowledge = discovery.upstream_knowledge(
    "purstream",
    {"id": "purstream", "name": "Purstream", "supportedTypes": ["movie", "tv"]},
    source,
)

assert knowledge["codeExecuted"] is False
assert knowledge["decodedStaticStringCount"] >= 4
assert "/search-bar/search/{query}" in knowledge["routes"], knowledge["routes"]
assert "/api/v1" in knowledge["routes"], knowledge["routes"]
assert "/episode/" in knowledge["routeFragments"], knowledge["routeFragments"]
assert "/stream/" in knowledge["routeFragments"], knowledge["routeFragments"]
assert "api.purstream.id" in knowledge["hosts"], knowledge["hosts"]
assert "api.pur" not in knowledge["hosts"], knowledge["hosts"]
assert all("https://api.pur/" not in value for value in knowledge["observedUrls"])

assert discovery.normalize_route_literal("/search.php?q=") == "/search.php?q={query}"
assert discovery.normalize_route_literal("/stream/{id}/episode?season=&episode=") == (
    "/stream/{id}/episode?season={season}&episode={episode}"
)

semantic_entry = discovery.reconstruction_manifest_entry(
    "animekai",
    {"id": "animekai", "supportedTypes": ["movie", "tv"]},
    {"provider_patches": {"animekai": {"published_types": ["anime"]}}},
)
assert semantic_entry["supportedTypes"] == ["movie", "tv"]
assert semantic_entry["canonicalSupportedTypes"] == ["anime"]

script = (ROOT / "scripts" / "discover_candidates.py").read_text(encoding="utf-8")
assert "--force-clean-reconstruction" in script
assert "if pending_clean and not force_clean_reconstruction:" in script

print("static clean ProviderBase reconstruction knowledge tests passed")
