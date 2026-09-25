#!/usr/bin/env python3
from __future__ import annotations

import copy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import domain_refresh_transaction_v2 as transaction
import refresh_authoritative_hub_domains as refresh


def run_with_candidates(cfg, candidates):
    original = refresh.hubresolver.gather_candidates
    try:
        refresh.hubresolver.gather_candidates = (
            lambda _provider, _cfg, _history, _mode, _timeout: (copy.deepcopy(candidates), [])
        )
        return refresh.resolve_authoritative_hub_domain("demo", dict(cfg), {}, "quick", 0.1)
    finally:
        refresh.hubresolver.gather_candidates = original


base = {
    "hub": "https://hub.example/",
    "direct": "https://demo.old/",
    "direct_authority": "explicit_current",
    "aliases": ["demo"],
    "allowed_terminal_host_patterns": [r"^demo\.[a-z0-9-]{2,20}$"],
    "sources": [{"type": "hub", "url": "https://hub.example/", "priority": 110}],
}

stale = run_with_candidates(base, [{
    "url": "https://demo.stale",
    "label": "ancien domaine principal bloque",
    "score": 100,
    "source_type": "hub",
    "source": "https://hub.example/",
}])
assert stale["official_site"] == "https://demo.old", stale
assert stale["reason"] == "registry_explicit_current_terminal_authority", stale
assert stale["registry_explicit_current_superseded"] is False, stale

fresh = run_with_candidates(base, [{
    "url": "https://demo.style",
    "label": "Lien principal - domaine actif - utilisez toujours ce lien",
    "score": 100,
    "source_type": "hub",
    "source": "https://hub.example/",
}])
assert fresh["official_site"] == "https://demo.style", fresh
assert fresh["reason"] == "authoritative_hub_primary_domain_observed_no_terminal_probe", fresh
assert fresh["registry_explicit_current_superseded"] is True, fresh

redirect = run_with_candidates(base, [{
    "url": "https://demo.next",
    "label": "validated redirect destination",
    "score": 92,
    "source_type": "redirect",
    "source": "https://redirect.example/",
    "source_redirect": True,
}])
assert redirect["official_site"] == "https://demo.next", redirect
assert redirect["registry_explicit_current_superseded"] is True, redirect

operator = dict(base)
operator["direct_authority"] = "operator_pin"
locked = run_with_candidates(operator, [{
    "url": "https://demo.style",
    "label": "Lien principal domaine actif",
    "score": 100,
    "source_type": "hub",
    "source": "https://hub.example/",
}])
assert locked["official_site"] == "https://demo.old", locked
assert locked["reason"] == "registry_operator_pin_terminal_authority", locked

registry = {"providers": {"demo": {
    "id": "demo",
    "direct": "https://demo.old/",
    "direct_candidates": ["https://demo.old/"],
    "allowed_terminal_hosts": ["demo.old"],
    "direct_authority": "explicit_current",
}}}
changed = transaction.sync_registry_terminal(registry, "demo", "https://demo.style")
row = registry["providers"]["demo"]
assert changed is True, registry
assert row["direct"] == "https://demo.style/", row
assert row["direct_candidates"][0] == "https://demo.style/", row
assert row["direct_authority"] == "explicit_current", row
assert row["direct_authority_source"] == "domain-refresh-authoritative-source", row
assert row["direct_authority_observed_at"], row

pinned_registry = {"providers": {"demo": {
    "id": "demo",
    "direct": "https://demo.old/",
    "direct_candidates": ["https://demo.old/"],
    "allowed_terminal_hosts": ["demo.old"],
    "direct_authority": "operator_pin",
}}}
try:
    transaction.sync_registry_terminal(pinned_registry, "demo", "https://demo.style")
except RuntimeError as exc:
    assert "operator_pin" in str(exc), exc
else:
    raise AssertionError("operator_pin rotation must fail closed")

print("Domain Refresh refreshable-current authority contract passed")
