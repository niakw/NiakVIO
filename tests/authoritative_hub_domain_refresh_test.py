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

# Regression: a curated direct address may itself become yesterday's URL. In
# quick mode we may follow that redirect as address evidence, but we must not
# fetch the newly discovered terminal a second time.
direct_old = "https://v2.animevostfr.example/"
direct_new = "https://animevostfr.example"
direct_cfg = {
    "hub": None,
    "aliases": ["animevostfr"],
    "direct_candidates": [direct_old],
    "allowed_terminal_hosts": ["v2.animevostfr.example", "animevostfr.example"],
    "sources": [{"type": "search", "query": "animevostfr lien", "priority": 35}],
}
calls = []
original_fetch = resolver.fetch

def fake_direct_redirect_fetch(url: str, timeout: float = 10.0):
    calls.append(url)
    if url == direct_old.rstrip("/"):
        return (200, direct_new + "/", "<html></html>", {"Content-Type": "text/html"})
    if url == direct_old:
        return (200, direct_new + "/", "<html></html>", {"Content-Type": "text/html"})
    raise AssertionError(f"new terminal must not be fetched during redirect discovery: {url}")

try:
    resolver.fetch = fake_direct_redirect_fetch
    direct_item = refresh.resolve_authoritative_hub_domain(
        "animevostfr", direct_cfg, {}, "quick", 0.2
    )
finally:
    resolver.fetch = original_fetch

assert calls == [direct_old.rstrip("/")], calls
assert direct_item["status"] == "site_authoritative", direct_item
assert direct_item["official_site"] == direct_new, direct_item
assert direct_item["selected_source_type"] == "source_redirect", direct_item
assert direct_item["site_candidates"][0]["source_redirect"] is True, direct_item
assert refresh.has_domain_refresh_source(direct_cfg, "quick") is True
assert refresh.has_domain_refresh_source({"search_queries": ["demo"]}, "quick") is False
assert refresh.has_domain_refresh_source({"search_queries": ["demo"]}, "deep") is True

# A high-scoring community/reference hub remains useful discovery evidence, but
# cannot replace a declared direct address or become Domain publication
# authority by itself.
supp_direct = "https://sadisflix-current.example/"
supp_hub = "https://community-index.example/sadisflix"
supp_new = "https://sadisflix-new.example"
supp_cfg = {
    "hub": None,
    "aliases": ["sadisflix"],
    "direct_candidates": [supp_direct],
    "allowed_terminal_hosts": ["sadisflix-current.example", "sadisflix-new.example"],
    "sources": [{
        "type": "hub",
        "url": supp_hub,
        "priority": 140,
        "role": "supplementary",
        "resolver": "official_outbound",
    }],
}
calls = []
original_fetch = resolver.fetch

def fake_supplementary_fetch(url: str, timeout: float = 10.0):
    calls.append(url)
    if url.rstrip("/") == supp_direct.rstrip("/"):
        return (200, supp_direct, "<html></html>", {"Content-Type": "text/html"})
    if url == supp_hub:
        return (
            200,
            supp_hub,
            f'<html><body><a href="{supp_new}/">Sadisflix current address</a></body></html>',
            {"Content-Type": "text/html"},
        )
    raise AssertionError(f"unexpected supplementary fetch: {url}")

try:
    resolver.fetch = fake_supplementary_fetch
    supp_item = refresh.resolve_authoritative_hub_domain(
        "sadisflix", supp_cfg, {}, "quick", 0.2
    )
finally:
    resolver.fetch = original_fetch

assert supp_direct.rstrip("/") in {url.rstrip("/") for url in calls}, calls
assert supp_hub in calls, calls
assert supp_item["status"] == "hub_unresolved", supp_item
assert not supp_item.get("official_site"), supp_item
assert all(
    row.get("source_role") != "supplementary"
    for row in supp_item.get("site_candidates") or []
), supp_item

# Regression: a direct-only provider whose address is actually unreachable may
# use search as a bounded discovery fallback in quick/scheduled mode. A plain
# search result cannot publish on first sighting: it must validate as the same
# provider terminal on two consecutive runs.
fallback_old = "https://demo-old.example/"
fallback_new = "https://demo-new.example"
fallback_cfg = {
    "hub": None,
    "aliases": ["demo"],
    "direct_candidates": [fallback_old],
    "allowed_terminal_hosts": ["demo-old.example", "demo-new.example"],
    "search_queries": ['"demo" official domain'],
    "search_confirmation_runs": 2,
}
fallback_history: dict = {}
search_calls: list[str] = []
original_fetch = resolver.fetch
original_search = resolver.search_candidates
original_validate = resolver.validate_terminal

def failed_direct_fetch(url: str, timeout: float = 10.0):
    if url.rstrip("/") == fallback_old.rstrip("/"):
        raise OSError("direct address unavailable")
    raise AssertionError(f"unexpected fetch: {url}")

def confirmed_search(provider_id: str, cfg: dict, query: str, timeout: float):
    search_calls.append(query)
    return (
        [{
            "url": fallback_new,
            "label": "demo official",
            "score": 22,
            "source_type": "search",
            "source": "synthetic-search",
            "query": query,
            "document_index": 0,
        }],
        [{"engine": "synthetic", "status": 200}],
    )

def validate_search(provider_id: str, cfg: dict, candidate: str, timeout: float):
    assert candidate == fallback_new
    return {
        "ok": True,
        "status": 200,
        "final_url": fallback_new,
        "brand_match": True,
        "content_type": "text/html",
        "attachment": False,
    }

try:
    resolver.fetch = failed_direct_fetch
    resolver.search_candidates = confirmed_search
    resolver.validate_terminal = validate_search

    fallback_first = refresh.resolve_authoritative_hub_domain(
        "demo", fallback_cfg, fallback_history, "quick", 0.1
    )
    assert fallback_first["status"] == "pending_confirmation", fallback_first
    assert fallback_first["reason"] == "search_fallback_requires_consecutive_confirmation", fallback_first
    assert fallback_first["confirmation"]["observed"] == 1, fallback_first
    assert fallback_first["terminal_probe_skipped"] is False, fallback_first
    assert fallback_history["pending"]["url"] == fallback_new, fallback_history

    fallback_second = refresh.resolve_authoritative_hub_domain(
        "demo", fallback_cfg, fallback_history, "quick", 0.1
    )
finally:
    resolver.fetch = original_fetch
    resolver.search_candidates = original_search
    resolver.validate_terminal = original_validate

assert len(search_calls) == 2, search_calls
assert fallback_second["status"] == "site_authoritative", fallback_second
assert fallback_second["official_site"] == fallback_new, fallback_second
assert fallback_second["selected_source_type"] == "search_confirmed", fallback_second
assert fallback_second["reason"] == "confirmed_search_fallback_after_direct_unreachable", fallback_second
assert fallback_second["terminal_probe_skipped"] is False, fallback_second
assert fallback_second["search_confirmation"]["observed"] == 2, fallback_second

print("authoritative hub domain refresh skips terminal validation for strong authority and requires two-run proof for search fallback")
