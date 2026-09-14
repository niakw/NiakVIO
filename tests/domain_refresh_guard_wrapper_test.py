#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from domain_refresh_guard_wrapper import has_fresh_rollback_evidence
from validate_domain_refresh_transaction import selected_source_is_authoritative


def item(label: str) -> dict:
    return {
        "selected_source_type": "hub",
        "site_candidates": [{"url": "https://historical.example", "label": label}],
    }

assert has_fresh_rollback_evidence(item("Domain - 1 Active"), "https://historical.example") is True
assert has_fresh_rollback_evidence(item("Domain Online"), "https://historical.example") is True
assert has_fresh_rollback_evidence(item("Adresse disponible 31/08/2026"), "https://historical.example") is True
assert has_fresh_rollback_evidence(item("Domain Available"), "https://historical.example") is True
assert has_fresh_rollback_evidence(item("Domain - 3 Offline"), "https://historical.example") is False
assert has_fresh_rollback_evidence(item("Domain Inactive"), "https://historical.example") is False
assert has_fresh_rollback_evidence(item("Adresse indisponible"), "https://historical.example") is False
assert has_fresh_rollback_evidence(item("Domain Unavailable"), "https://historical.example") is False
assert has_fresh_rollback_evidence(item("Bloqué par les FAI — encore accessible via DNS alternatif"), "https://historical.example") is False
assert has_fresh_rollback_evidence(item("Visit"), "https://historical.example") is False

# Public Telegram is authority only when the exact current registry source is
# explicitly curated as an authoritative address/domain reference.
provider_id = "hindmoviez"
telegram_item = {
    "selected_source_type": "telegram_public",
    "selected_source": "https://t.me/s/hindmoviez/1975",
}
registry = {
    provider_id: {
        "sources": [{
            "type": "telegram_public",
            "url": "https://t.me/s/hindmoviez/1975",
            "purpose": "Authoritative address reference",
        }]
    }
}
assert selected_source_is_authoritative(provider_id, telegram_item, registry) is True
assert selected_source_is_authoritative(
    provider_id,
    telegram_item,
    {provider_id: {"sources": [{
        "type": "telegram_public",
        "url": "https://t.me/s/other/1",
        "purpose": "Authoritative address reference",
    }]}},
) is False
assert selected_source_is_authoritative(
    provider_id,
    telegram_item,
    {provider_id: {"sources": [{
        "type": "telegram_public",
        "url": "https://t.me/s/hindmoviez/1975",
        "purpose": "Community discussion",
    }]}},
) is False

print("domain refresh explicit-current-domain and registry-authority guard tests passed")
