#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import resolve_provider_hubs as resolver

PRIMARY = "https://primary-hub.example/"
SECONDARY = "https://secondary-hub.example/"
PRIMARY_TERMINAL = "https://demo-primary.example/"
SECONDARY_TERMINAL = "https://demo-secondary.example/"

cfg = {
    "aliases": ["demo"],
    "resolver": "official_outbound",
    "official_link_labels": ["official"],
    "sources": [
        {
            "type": "hub",
            "url": PRIMARY,
            "priority": 40,
            "role": "primary",
            "resolver": "service_catalogue",
            "official_link_labels": ["catalogue"],
        },
        {
            "type": "hub",
            "url": SECONDARY,
            "priority": 120,
            "role": "fallback",
            "resolver": "alias_outbound",
            "official_link_labels": ["secondary"],
        },
    ],
}

original_fetch = resolver.fetch
original_choose = resolver.choose_official
seen: list[tuple[str, str, tuple[str, ...]]] = []

def fake_fetch(url: str, timeout: float = 10.0):
    return 200, url, "<html></html>", {"Content-Type": "text/html"}

def fake_choose(provider_id: str, source_cfg: dict, final: str, document: str):
    seen.append(
        (
            final,
            str(source_cfg.get("resolver") or ""),
            tuple(source_cfg.get("official_link_labels") or []),
        )
    )
    if final == PRIMARY:
        return ([{
            "url": PRIMARY_TERMINAL,
            "label": "primary",
            "score": 20,
            "document_index": 0,
        }], PRIMARY_TERMINAL)
    if final == SECONDARY:
        return ([{
            "url": SECONDARY_TERMINAL,
            "label": "fallback",
            "score": 100,
            "document_index": 0,
        }], SECONDARY_TERMINAL)
    raise AssertionError(final)

try:
    resolver.fetch = fake_fetch
    resolver.choose_official = fake_choose
    candidates, observations = resolver.gather_candidates("demo", cfg, {}, "quick", 0.1)
finally:
    resolver.fetch = original_fetch
    resolver.choose_official = original_choose

assert [row["url"] for row in candidates[:2]] == [
    PRIMARY_TERMINAL.rstrip("/"),
    SECONDARY_TERMINAL.rstrip("/"),
], candidates
assert candidates[0]["source_fallback"] is False, candidates
assert candidates[1]["source_fallback"] is True, candidates
assert candidates[1]["source_role"] == "fallback", candidates
assert any(row[1] == "service_catalogue" and "catalogue" in row[2] for row in seen), seen
assert any(row[1] == "alias_outbound" and "secondary" in row[2] for row in seen), seen
assert {row["resolver"] for row in observations} == {"service_catalogue", "alias_outbound"}, observations

# If the primary hub itself is inaccessible, the secondary source remains a
# first-class address authority and is promoted without falling back to search
# or stale provider history.
seen.clear()

def fallback_fetch(url: str, timeout: float = 10.0):
    if url == PRIMARY:
        raise OSError("primary unavailable")
    return 200, url, "<html></html>", {"Content-Type": "text/html"}

try:
    resolver.fetch = fallback_fetch
    resolver.choose_official = fake_choose
    candidates, observations = resolver.gather_candidates("demo", cfg, {}, "quick", 0.1)
finally:
    resolver.fetch = original_fetch
    resolver.choose_official = original_choose

assert [row["url"] for row in candidates] == [SECONDARY_TERMINAL.rstrip("/")], candidates
assert candidates[0]["source_fallback"] is True, candidates
assert any(row.get("url") == PRIMARY and "error" in row for row in observations), observations
assert any(row.get("url") == SECONDARY and row.get("resolver") == "alias_outbound" for row in observations), observations

print("provider hub heterogeneous multi-source fallback contract passed")
