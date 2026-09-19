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



# Regression: a registry-pinned current direct terminal must outrank a stale hub
# card, but only when the provider opts into explicit_current authority.
pinned_hub = "https://kehflix.example.wiki/"
pinned_current = "https://kehflix.example.com"
pinned_stale = "https://kehflix.example.lol"
pinned_cfg = {
    "hub": pinned_hub,
    "direct": pinned_current + "/",
    "direct_authority": "explicit_current",
    "allowed_terminal_hosts": ["kehflix.example.com"],
    "sources": [{"type": "hub", "url": pinned_hub, "priority": 120}],
}
calls = []
original_fetch = resolver.fetch

def fake_pinned_fetch(url: str, timeout: float = 10.0):
    calls.append(url)
    if url == pinned_hub:
        return (
            200,
            pinned_hub,
            f'<html><body><a href="{pinned_stale}/">old card</a></body></html>',
            {"Content-Type": "text/html; charset=UTF-8"},
        )
    raise AssertionError(f"terminal must not be fetched during pinned refresh: {url}")

try:
    resolver.fetch = fake_pinned_fetch
    pinned = refresh.resolve_authoritative_hub_domain(
        "kehflix-demo", pinned_cfg, {}, "quick", 0.2
    )
finally:
    resolver.fetch = original_fetch

assert calls == [pinned_hub], calls
assert pinned["official_site"] == pinned_current, pinned
assert pinned["reason"] == "registry_explicit_current_terminal_authority", pinned
assert pinned["site_candidates"][0]["registry_explicit_current"] is True, pinned

print("authoritative hub domain refresh skips terminal validation and accepts current hub destination")
