#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import refresh_authoritative_hub_domains as refresh
import resolve_provider_hubs as resolver

HUB = "https://papadustream.info/acces/"
NEW = "https://papadustream-new.watch"

cfg = {
    "hub": HUB,
    "resolver": "official_outbound",
    "aliases": ["papadustream"],
    "official_link_labels": ["Accéder", "site officiel", "adresse officielle"],
    "allowed_terminal_hosts": ["papadustream-v2.watch"],
    "blocked_hosts": [],
    "sources": [
        {"type": "hub", "url": HUB, "priority": 100},
    ],
}

calls: list[str] = []
original_fetch = resolver.fetch


def fake_fetch(url: str, timeout: float = 10.0):
    calls.append(url)
    if url == HUB:
        return (
            200,
            HUB,
            '<html><body><a href="https://papadustream-new.watch/">Accéder au site officiel</a></body></html>',
            {"Content-Type": "text/html; charset=UTF-8"},
        )
    raise AssertionError(f"terminal must not be fetched during domain refresh: {url}")


try:
    resolver.fetch = fake_fetch
    item = refresh.resolve_authoritative_hub_domain(
        "papadustream",
        cfg,
        {},
        "quick",
        0.2,
    )
finally:
    resolver.fetch = original_fetch

assert calls == [HUB], calls
assert item["status"] == "site_authoritative", item
assert item["official_site"] == NEW, item
assert item["site_final_url"] == NEW, item
assert item["terminal_probe_skipped"] is True, item
assert item["site_validations"] == [], item
assert item["reason"] == "authoritative_hub_primary_domain_observed_no_terminal_probe", item

# Regression: an authoritative hub redirect is itself sufficient address evidence.
redirect_cfg = {
    "hub": "https://example-hub.invalid/",
    "resolver": "redirect",
    "aliases": ["papadustream"],
    "blocked_hosts": [],
    "sources": [
        {"type": "redirect", "url": "https://example-hub.invalid/", "priority": 100},
    ],
}
redirect_observations = [
    {
        "source_type": "redirect",
        "url": "https://example-hub.invalid/",
        "status": 302,
        "final_url": "https://papadustream-latest.watch/",
    }
]
rows = refresh._redirect_candidates_from_source_observations(redirect_cfg, redirect_observations)
assert rows and rows[0]["url"] == "https://papadustream-latest.watch", rows
assert rows[0]["source_redirect"] is True, rows


# Regression: some providers expose their official site as the address hub itself.
# The host remains a valid terminal only when the current registry explicitly
# declares it as direct/allowed terminal authority.
same_host_cfg = {
    "hub": "https://4khdhub.one/",
    "resolver": "alias_outbound",
    "aliases": ["4khdhub"],
    "terminal_aliases": ["4khdhub"],
    "direct_candidates": ["https://4khdhub.one/"],
    "allowed_terminal_hosts": ["4khdhub.one"],
    "blocked_hosts": ["hdhub4u.ms", "hdhub4u.bi"],
    "sources": [
        {"type": "hub", "url": "https://4khdhub.one/", "priority": 120},
    ],
}
candidate = {
    "url": "https://4khdhub.one/",
    "source_type": "hub",
    "label": "4KHDHub",
}
assert refresh._safe_authoritative_candidate("4khdhub", same_host_cfg, candidate) is True
assert resolver.candidate_score(
    "4khdhub",
    same_host_cfg,
    "https://4khdhub.one/",
    "4KHDHub",
    0,
    1,
) >= 0

# Without explicit terminal authority, a discovery-only hub host remains rejected.
source_only_cfg = {
    "hub": "https://hub.example/",
    "resolver": "official_outbound",
    "aliases": ["provider"],
    "sources": [{"type": "hub", "url": "https://hub.example/", "priority": 100}],
}
source_only = {"url": "https://hub.example/", "source_type": "hub", "label": "Provider"}
assert refresh._safe_authoritative_candidate("provider", source_only_cfg, source_only) is False
assert resolver.candidate_score(
    "provider",
    source_only_cfg,
    "https://hub.example/",
    "Provider",
    0,
    1,
) < 0

print("authoritative hub domain refresh explicit-terminal co-location contract passed")
print("authoritative hub domain refresh skips terminal validation and accepts current hub destination")
