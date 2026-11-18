#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_domain_refresh_transaction import selected_source_is_authoritative

provider_id = "hindmoviez"
item = {
    "selected_source_type": "telegram_public",
    "selected_source": "https://t.me/s/hindmoviez/1975",
}
registry = {
    provider_id: {
        "sources": [
            {
                "type": "telegram_public",
                "url": "https://t.me/s/hindmoviez/1975",
                "priority": 100,
                "purpose": "Authoritative address reference",
            }
        ]
    }
}

assert selected_source_is_authoritative(provider_id, item, registry) is True

# The same configured source is deliberately non-authoritative when its role is
# supplementary/reference-only. This is the fail-closed boundary for community
# indexes imported as fallback discovery.
supplementary_registry = {
    provider_id: {
        "sources": [{
            "type": "telegram_public",
            "url": "https://t.me/s/hindmoviez/1975",
            "priority": 100,
            "role": "supplementary",
            "purpose": "Authoritative address reference",
        }]
    }
}
assert selected_source_is_authoritative(provider_id, item, supplementary_registry) is False
supplementary_hub_item = {
    "selected_source_type": "hub",
    "selected_source": "https://community-index.example/hindmoviez",
}
supplementary_hub_registry = {
    provider_id: {
        "sources": [{
            "type": "hub",
            "url": "https://community-index.example/hindmoviez",
            "role": "supplementary",
            "purpose": "Community address discovery reference",
        }]
    }
}
assert selected_source_is_authoritative(
    provider_id, supplementary_hub_item, supplementary_hub_registry
) is False

# Same source type is not enough: arbitrary/community feeds stay fail-closed.
unconfigured = {
    provider_id: {
        "sources": [
            {
                "type": "telegram_public",
                "url": "https://t.me/s/other-channel/1",
                "purpose": "Authoritative address reference",
            }
        ]
    }
}
assert selected_source_is_authoritative(provider_id, item, unconfigured) is False

wrong_purpose = {
    provider_id: {
        "sources": [
            {
                "type": "telegram_public",
                "url": "https://t.me/s/hindmoviez/1975",
                "purpose": "Community discussion",
            }
        ]
    }
}
assert selected_source_is_authoritative(provider_id, item, wrong_purpose) is False

assert selected_source_is_authoritative(
    provider_id,
    {"selected_source_type": "telegram_public", "selected_source": ""},
    registry,
) is False

# Existing globally trusted authority types remain accepted independently.
assert selected_source_is_authoritative(
    provider_id,
    {"selected_source_type": "hub", "selected_source": "https://hub.example"},
    {},
) is True

print("domain refresh registry-scoped authority tests passed")
