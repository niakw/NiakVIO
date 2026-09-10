#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from reconcile_provider_domain_metadata import reconcile_patch

patch = {
    "official_site": "https://flemmix.cloud",
    "manifest_overrides": {
        "logo": "https://flemmix.kim/favicon.ico",
        "icon": "https://cdn.example/flemmix.png",
    },
    "domain_substitutions": {
        "flemmix.men": "flemmix.kim",
        "api.flemmix.men": "api.flemmix.kim",
    },
    "runtime_domain_replacements": {
        "flemmix.kim": "flemmix.cloud",
    },
}
registry = {
    "direct": "https://flemmix.cloud/",
    "direct_candidates": [
        "https://flemmix.cloud/",
        "https://flemmix.kim/",
        "https://flemmix.men/",
    ],
    "allowed_terminal_hosts": ["flemmix.cloud", "flemmix.kim", "flemmix.men"],
}
history = {
    "current": {"url": "https://flemmix.cloud"},
    "previous": [{"url": "https://flemmix.kim"}],
}

changed = reconcile_patch("flemmix", patch, registry, history)
assert "manifest_overrides.logo" in changed
assert patch["manifest_overrides"]["logo"] == "https://flemmix.cloud/favicon.ico"
# External/CDN assets are not provider-domain metadata and must stay untouched.
assert patch["manifest_overrides"]["icon"] == "https://cdn.example/flemmix.png"
assert patch["domain_substitutions"]["flemmix.men"] == "flemmix.cloud"
# API hosts retain independent API authority.
assert patch["domain_substitutions"]["api.flemmix.men"] == "api.flemmix.kim"
assert "flemmix.cloud" not in patch["runtime_domain_replacements"]

print("provider domain metadata reconciliation tests passed")
