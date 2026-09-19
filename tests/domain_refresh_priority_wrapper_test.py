#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import domain_refresh_priority_wrapper as wrapper
from domain_refresh_priority_wrapper import prioritize_authoritative_item


def row(url: str, label: str, score: int, index: int) -> dict:
    return {
        "url": url,
        "label": label,
        "score": score,
        "document_index": index,
        "source_type": "hub",
        "source": "https://hub.example/",
    }


# Current scope regression: embedded legacy address rows must not create refresh
# work. The wrapper must call merge_hub_registry without official_domain_hubs so
# provider-hubs.json remains the only current provider membership authority.
seen_config: dict = {}
original_merge = wrapper.transaction.resolver.merge_hub_registry


def fake_merge(config: dict) -> dict:
    seen_config.clear()
    seen_config.update(config)
    return {"anime-sama": {"sources": [{"type": "hub", "url": "https://hub.example"}]}}

try:
    wrapper.transaction.resolver.merge_hub_registry = fake_merge
    current = wrapper.current_registry_hub_configs({
        "official_domain_hubs": {
            "frenchstream": {"hub": "https://fstream.org/"},
        },
        "provider_patches": {"anime-sama": {}, "frenchstream": {}},
    })
finally:
    wrapper.transaction.resolver.merge_hub_registry = original_merge

assert "official_domain_hubs" not in seen_config, seen_config
assert set(current) == {"anime-sama"}, current

# Equal trust score: explicit principal/recommended must beat backup/mirror even
# when lexical URL ordering would otherwise put the backup first.
item = {
    "provider_id": "anime-sama",
    "status": "site_authoritative",
    "official_site": "https://backup.example",
    "site_candidates": [
        row("https://backup.example", "Backup Miroir Alpha Secours", 100, 3),
        row("https://primary.example", "Principal Recommandé Accès prioritaire", 100, 2),
    ],
}
result = prioritize_authoritative_item(item)
assert result["official_site"] == "https://primary.example", result
assert result["candidate_priority_adjusted"] is True, result

# A strictly stronger authority score always wins, regardless of semantic label.
item = {
    "provider_id": "provider",
    "status": "site_authoritative",
    "official_site": "https://redirect.example",
    "site_candidates": [
        row("https://redirect.example", "authoritative source redirect destination", 120, 9),
        row("https://primary.example", "Principal Recommandé Provider", 100, 1),
    ],
}
result = prioritize_authoritative_item(item)
assert result["official_site"] == "https://redirect.example", result
assert not result.get("candidate_priority_adjusted"), result

# A concise provider-branded link beats an anonymous equal-score link even when
# the anonymous link appears much earlier in the authoritative hub document.
item = {
    "provider_id": "voiranime",
    "status": "site_authoritative",
    "official_site": "https://voiranime.homes",
    "site_candidates": [
        row("https://voiranime.homes", "", 67, 2),
        row("https://voiranime.diy", "VoirAnime", 67, 41),
        row("https://voiranime.icu", "Voiranime.icu", 67, 42),
    ],
}
result = prioritize_authoritative_item(item)
assert result["official_site"] == "https://voiranime.diy", result
assert result["candidate_priority_adjusted"] is True, result

# Neutral ties with no provider-brand signal preserve document order before
# lexical URL order.
item = {
    "provider_id": "neutral-provider",
    "status": "site_authoritative",
    "official_site": "https://z.example",
    "site_candidates": [
        row("https://a.example", "Visit", 90, 4),
        row("https://z.example", "Visit", 90, 1),
    ],
}
result = prioritize_authoritative_item(item)
assert result["official_site"] == "https://z.example", result

# Real registry-chain regression: Kehflix explicit current terminal must survive
# provider-hubs.json -> merge_hub_registry -> authoritative resolver.
real_config = wrapper.transaction.resolver.load_json(ROOT / "provider-overrides.json", {})
real_hubs = wrapper.current_registry_hub_configs(real_config)
kehflix = real_hubs["kehflix"]
assert kehflix["hub"].rstrip("/") == "https://kehflix.wiki", kehflix
assert kehflix["direct"].rstrip("/") == "https://kehflix.com", kehflix
assert kehflix["direct_authority"] == "explicit_current", kehflix
explicit = wrapper.refresh._explicit_current_direct_candidate(kehflix)
assert explicit is not None, kehflix
assert explicit["url"] == "https://kehflix.com", explicit
assert explicit["registry_explicit_current"] is True, explicit

original_gather = wrapper.refresh.hubresolver.gather_candidates
try:
    def mutating_gather(_provider_id, cfg, _history_row, _mode, _timeout):
        cfg["direct"] = "https://kehflix.lol/"
        cfg["allowed_terminal_hosts"] = ["kehflix.com", "kehflix.lol"]
        return ([{
            "url": "https://kehflix.lol",
            "label": "stale hub card",
            "score": 100,
            "source_type": "hub",
            "source": "https://kehflix.wiki/",
        }], [])

    wrapper.refresh.hubresolver.gather_candidates = mutating_gather
    protected = wrapper.refresh.resolve_authoritative_hub_domain(
        "kehflix", dict(kehflix), {}, "quick", 1.0
    )
finally:
    wrapper.refresh.hubresolver.gather_candidates = original_gather

assert protected["official_site"] == "https://kehflix.com", protected
assert protected["reason"] == "registry_explicit_current_terminal_authority", protected
assert protected["site_candidates"][0]["url"] == "https://kehflix.com", protected

# Real registry-chain regression: 4KHDHub must not be conflated with the
# separate HDHub4u catalogue. The current 4KHDHub terminal is explicitly
# pinned and every stale HDHub4u terminal is excluded from provider authority.
fourk = real_hubs["4khdhub"]
assert fourk["direct"].rstrip("/") == "https://4khdhub.one", fourk
assert fourk["direct_authority"] == "explicit_current", fourk
assert fourk["aliases"] == ["4khdhub"], fourk
assert fourk["terminal_aliases"] == ["4khdhub"], fourk
assert "hdhub4u.ms" in fourk["blocked_hosts"], fourk
assert "hdhub4u.bi" in fourk["blocked_hosts"], fourk
assert fourk["allowed_terminal_hosts"] == ["4khdhub.one"], fourk
fourk_explicit = wrapper.refresh._explicit_current_direct_candidate(fourk)
assert fourk_explicit is not None, fourk
assert fourk_explicit["url"] == "https://4khdhub.one", fourk_explicit
assert fourk_explicit["registry_explicit_current"] is True, fourk_explicit

print("domain refresh current-registry scope and semantic priority tests passed")
