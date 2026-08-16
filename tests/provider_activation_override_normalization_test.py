#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from normalize_provider_activation_overrides import (  # noqa: E402
    is_configured_safety_quarantine,
    normalize,
)

config = {
    "provider_patches": {
        "recoverable": {
            "capability": "direct_media",
            "manifest_overrides": {"enabled": False, "disabledPlatforms": []},
        },
        "configured-quarantine": {
            "capability": "quarantined",
            "manifest_overrides": {"enabled": False},
        },
        "patched-quarantine": {
            "capability": "html_scraper",
            "patch_scripts": ["scripts/provider_patches/quarantine_provider_v1.py"],
            "manifest_overrides": {"enabled": False},
        },
        "explicit-quarantine": {
            "capability": "direct_media",
            "safety_quarantine": True,
            "manifest_overrides": {"enabled": False},
        },
    }
}

normalized, released = normalize(config)
assert released == ["recoverable"], released
assert "enabled" not in normalized["provider_patches"]["recoverable"]["manifest_overrides"]
assert normalized["provider_patches"]["recoverable"]["manifest_overrides"]["disabledPlatforms"] == []
assert normalized["provider_patches"]["configured-quarantine"]["manifest_overrides"]["enabled"] is False
assert normalized["provider_patches"]["patched-quarantine"]["manifest_overrides"]["enabled"] is False
assert normalized["provider_patches"]["explicit-quarantine"]["manifest_overrides"]["enabled"] is False
assert is_configured_safety_quarantine(config["provider_patches"]["configured-quarantine"])
assert is_configured_safety_quarantine(config["provider_patches"]["patched-quarantine"])
assert is_configured_safety_quarantine(config["provider_patches"]["explicit-quarantine"])
assert not is_configured_safety_quarantine(config["provider_patches"]["recoverable"])

print("provider activation override normalization test passed")
