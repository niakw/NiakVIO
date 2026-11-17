#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import resolve_provider_hubs as resolver
import refresh_authoritative_hub_domains as authoritative
import domain_refresh_transaction_v2 as transaction
import sanitize_provider_hub_registry as sanitizer
import validate_domain_refresh_transaction as domain_guard

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

assert [row["url"].rstrip("/") for row in candidates[:2]] == [
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

assert [row["url"].rstrip("/") for row in candidates] == [SECONDARY_TERMINAL.rstrip("/")], candidates
assert candidates[0]["source_fallback"] is True, candidates
assert any(row.get("url") == PRIMARY and "error" in row for row in observations), observations
assert any(row.get("url") == SECONDARY and row.get("resolver") == "alias_outbound" for row in observations), observations

# The fast authoritative Domain Refresh path must preserve the same source tier.
# A high-scoring fallback cannot override a usable primary source; it becomes
# authoritative only when no primary candidate exists.
original_gather = resolver.gather_candidates

def gather_both(provider_id: str, cfg: dict, history_row: dict, mode: str, timeout: float):
    return (
        [
            {
                "url": PRIMARY_TERMINAL,
                "label": "primary current",
                "score": 20,
                "source_type": "hub",
                "source": PRIMARY,
                "source_role": "primary",
                "source_priority": 40,
                "source_fallback": False,
            },
            {
                "url": SECONDARY_TERMINAL,
                "label": "fallback current",
                "score": 100,
                "source_type": "hub",
                "source": SECONDARY,
                "source_role": "fallback",
                "source_priority": 120,
                "source_fallback": True,
            },
        ],
        [],
    )

try:
    resolver.gather_candidates = gather_both
    resolved = authoritative.resolve_authoritative_hub_domain("demo", cfg, {}, "quick", 0.1)
finally:
    resolver.gather_candidates = original_gather

assert resolved["official_site"] == PRIMARY_TERMINAL.rstrip("/"), resolved
assert resolved["selected_source"] == PRIMARY, resolved

def gather_fallback_only(provider_id: str, cfg: dict, history_row: dict, mode: str, timeout: float):
    return (
        [{
            "url": SECONDARY_TERMINAL,
            "label": "fallback current",
            "score": 100,
            "source_type": "hub",
            "source": SECONDARY,
            "source_role": "fallback",
            "source_priority": 120,
            "source_fallback": True,
        }],
        [],
    )

try:
    resolver.gather_candidates = gather_fallback_only
    resolved = authoritative.resolve_authoritative_hub_domain("demo", cfg, {}, "quick", 0.1)
finally:
    resolver.gather_candidates = original_gather

assert resolved["official_site"] == SECONDARY_TERMINAL.rstrip("/"), resolved
assert resolved["selected_source"] == SECONDARY, resolved

redirect_rows = authoritative._redirect_candidates_from_source_observations(
    cfg,
    [{
        "source_type": "redirect",
        "source_role": "fallback",
        "source_priority": 90,
        "url": "https://go.demo.example/",
        "final_url": "https://demo-redirect.example/",
    }],
)
assert redirect_rows and redirect_rows[0]["source_fallback"] is True, redirect_rows
assert redirect_rows[0]["source_priority"] == 90, redirect_rows

# A trusted HTML hub may publish its official Telegram address feed inside a
# normal link/card. Discover it as fallback registry knowledge, never as same-run
# terminal publication authority.
linked = resolver._linked_telegram_address_sources(
    "demo",
    {"aliases": ["demo"]},
    '<div>Official Telegram address channel <a href="https://t.me/s/demoofficial">Telegram officiel demo</a></div>',
    PRIMARY,
)
assert linked and linked[0]["url"] == "https://t.me/s/demoofficial", linked
assert linked[0]["role"] == "fallback", linked
assert linked[0]["resolver"] == "latest_telegram_domain", linked

registry = {
    "providers": {
        "demo": {
            "id": "demo",
            "sources": [
                {"type": "hub", "url": PRIMARY, "priority": 100, "role": "primary"},
            ],
        }
    }
}
observations = [{
    "source_type": "telegram_public",
    "source_role": "fallback",
    "source_priority": 90,
    "resolver": "latest_telegram_domain",
    "url": "https://t.me/s/demoofficial",
    "status": 0,
    "final_url": "https://t.me/s/demoofficial",
    "discovered_address_source": True,
    "discovered_from": PRIMARY,
    "purpose": "Official address fallback discovered from authoritative hub link",
}]
assert transaction.sync_registry_discovered_sources(registry, "demo", observations) is True, registry
persisted = registry["providers"]["demo"]["sources"][-1]
assert persisted["type"] == "telegram_public" and persisted["role"] == "fallback", persisted
assert persisted["discovery"] == "authoritative_hub_link", persisted
assert transaction.sync_registry_discovered_sources(registry, "demo", observations) is False, registry


# Generic HTML hubs cover the common workbook shapes without provider-specific
# parsers: anchor-in-div, raw URL text, JS assignment/window.location and
# meta-refresh all remain address candidates. This also covers Linktree/bio-link
# style pages when their outbound URL is rendered in ordinary HTML.
html_shapes = """
<div class="address-card"><a href="https://demo-anchor.example/">Entrer</a></div>
<div class="plain-address">Adresse actuelle: https://demo-text.example/</div>
<script>
const currentUrl = "https://demo-js.example/";
window.location = "https://demo-location.example/";
</script>
<meta http-equiv="refresh" content="0; url=https://demo-meta.example/">
"""
shape_urls = {row[0].rstrip("/") for row in resolver.links(html_shapes, PRIMARY)}
for expected in {
    "https://demo-anchor.example",
    "https://demo-text.example",
    "https://demo-js.example",
    "https://demo-location.example",
    "https://demo-meta.example",
}:
    assert expected in shape_urls, (expected, sorted(shape_urls))

# Telegram bots/private landing pages are interactive surfaces, not public
# address feeds. Never silently treat them like /s/<channel> preview pages.
bot_fetch_called = False

def bot_fetch(url: str, timeout: float = 10.0):
    global bot_fetch_called
    bot_fetch_called = True
    raise AssertionError("interactive Telegram source must not be fetched")

try:
    resolver.fetch = bot_fetch
    bot_candidates, bot_observations = resolver.gather_candidates(
        "demo",
        {
            "aliases": ["demo"],
            "sources": [{
                "type": "telegram_public",
                "url": "https://t.me/demo_mirror_bot",
                "role": "fallback",
                "resolver": "latest_telegram_domain",
            }],
        },
        {},
        "quick",
        0.1,
    )
finally:
    resolver.fetch = original_fetch

assert bot_fetch_called is False
assert not bot_candidates
assert bot_observations and bot_observations[0]["reason"] == "interactive_or_nonpublic_telegram_source"
assert bot_observations[0]["publication_authority"] is False

architecture = json.loads((ROOT / "automation/provider-v3-architecture.json").read_text(encoding="utf-8"))
validation = json.loads((ROOT / "VALIDATION.json").read_text(encoding="utf-8"))
registry_policy = json.loads((ROOT / "provider-hubs.json").read_text(encoding="utf-8"))["resolution_policy"]
arch_md = (ROOT / "ARCHITECTURE.md").read_text(encoding="utf-8")

domain_arch = architecture["domain_refresh"]
assert domain_arch["per_source_resolver_allowed"] is True, domain_arch
assert domain_arch["primary_precedes_fallback"] is True, domain_arch
assert domain_arch["discovery_sources_never_runtime_origins"] is True, domain_arch
assert "meta_refresh" in domain_arch["html_extraction_modes"], domain_arch
assert "/s/<channel>" in domain_arch["public_telegram_contract"], domain_arch
assert "manual evidence only" in domain_arch["interactive_telegram_bot_contract"], domain_arch
assert validation["domain_refresh"]["multi_source_address_authority"] is True, validation["domain_refresh"]
assert validation["domain_refresh"]["learned_hub_linked_telegram_requires_later_run_before_publication"] is True
assert validation["domain_refresh"]["public_telegram_requires_web_preview"] is True
assert validation["domain_refresh"]["interactive_telegram_bot_is_automatic_authority"] is False
assert validation["domain_refresh"]["link_aggregators_use_generic_html_hub_parser"] is True
assert "window_location" in validation["domain_refresh"]["html_hub_extraction_modes"]
assert "multi_source_policy" in registry_policy and "linked_source_learning" in registry_policy, registry_policy
assert "meta_refresh" in registry_policy["html_extraction_modes"], registry_policy
assert "manual evidence only" in registry_policy["interactive_telegram_bot_policy"], registry_policy
assert "plusieurs sources d’adresse ordonnées" in arch_md, "Domain Refresh multi-source documentation missing"
assert "Sources d'adresse hétérogènes et fallbacks" in arch_md
assert "preuve manuelle uniquement" in arch_md

# The Domain preflight sanitizer must accept the exact current Global+France
# visible union; using root manifest.json alone previously rejected France-only
# providers before any network resolution.
root_manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
vf_manifest = json.loads((ROOT / "vf/manifest.json").read_text(encoding="utf-8"))
global_ids = {str(row["id"]).strip().casefold() for row in root_manifest["scrapers"]}
vf_ids = {str(row["id"]).strip().casefold() for row in vf_manifest["scrapers"]}
strict_fr = vf_ids - global_ids
sanitized_scope = set(sanitizer.current_provider_rows(ROOT / "manifest.json"))
assert strict_fr, "fixture requires at least one strict France-only provider"
assert strict_fr <= sanitized_scope, (sorted(strict_fr - sanitized_scope), len(sanitized_scope))

# The publication guard must use the active Global+France union too; otherwise
# the sanitizer can pass France-only rows only for the next guard to reject them.
guard_scope = {str(value).strip().casefold() for value in domain_guard.validation_provider_ids(ROOT / "manifest.json")}
from current_provider_scope import projection_active_provider_ids
expected_guard_scope = {str(value).strip().casefold() for value in projection_active_provider_ids(ROOT)}
assert guard_scope == expected_guard_scope, (
    len(guard_scope),
    len(expected_guard_scope),
)
assert strict_fr & guard_scope, "active France-only scope must reach Domain publication guard"

missing = authoritative._no_address_authority_items(
    {"demo", "castle", "missing-row"},
    {
        "demo": cfg,
        "castle": {"sources": [{"type": "search", "query": '"Castle" official domain'}]},
    },
    {"demo"},
)
assert missing["castle"]["status"] == "no_address_authority", missing
assert missing["castle"]["reason"] == "no_configured_authoritative_address_source", missing
assert missing["missing-row"]["reason"] == "provider_missing_from_current_hub_registry", missing
assert missing["castle"]["publication_authority"] is False, missing

print("provider hub heterogeneous multi-source fallback contract passed")
