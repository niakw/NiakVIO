#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "scripts" / "merge_waf_latest_evidence.py"
spec = importlib.util.spec_from_file_location("merge_waf_latest_evidence", path)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)

previous = {
    "schemaVersion": 1,
    "rows": [
        {
            "provider": "demo",
            "lane": "movie",
            "publicUrl": "https://demo.invalid/",
            "outcome": "browser_challenge_persisted",
            "residentialExitNodeProfile": {
                "profile": "tailscale-residential-exit",
                "outcome": "browser_content_reached",
            },
        },
        {
            "provider": "untouched",
            "lane": "movie",
            "publicUrl": "https://untouched.invalid/",
            "outcome": "browser_content_reached",
        },
    ],
    "residentialExitNodeEvidence": {
        "available": True,
        "profile": "tailscale-residential-exit",
        "matchedProviderLanes": 1,
    },
    "residentialProviderReplay": {
        "available": True,
        "rows": [
            {
                "provider": "demo",
                "lane": "movie",
                "raw": 1,
                "playable": 1,
                "verified": 1,
                "contradictions": 0,
            }
        ],
    },
}

current_without_tailscale = {
    "schemaVersion": 1,
    "rows": [
        {
            "provider": "demo",
            "lane": "movie",
            "publicUrl": "https://demo.invalid/",
            "outcome": "browser_content_reached",
        }
    ],
    "residentialExitNodeEvidence": {
        "available": False,
        "reason": "tailscale-unavailable",
    },
}

merged = module.merge(previous, current_without_tailscale)
demo = next(row for row in merged["rows"] if row["provider"] == "demo")
assert demo["outcome"] == "browser_content_reached"
assert demo["residentialExitNodeProfile"]["outcome"] == "browser_content_reached"
assert any(row["provider"] == "untouched" for row in merged["rows"])
assert merged["residentialExitNodeEvidence"]["available"] is True
assert merged["residentialExitNodeLastAttempt"]["available"] is False
assert merged["residentialProviderReplay"]["verifiedProviders"] == ["demo"]
assert merged["residentialProviderReplay"]["lastAttempt"]["available"] is False

current_with_tailscale = {
    "schemaVersion": 1,
    "rows": [
        {
            "provider": "demo",
            "lane": "movie",
            "publicUrl": "https://demo.invalid/",
            "outcome": "browser_content_reached",
            "residentialExitNodeProfile": {
                "profile": "tailscale-residential-exit",
                "outcome": "browser_challenge_persisted",
            },
        }
    ],
    "residentialExitNodeEvidence": {
        "available": True,
        "profile": "tailscale-residential-exit",
        "matchedProviderLanes": 1,
    },
    "residentialProviderReplay": {
        "available": True,
        "rows": [
            {
                "provider": "demo",
                "lane": "movie",
                "raw": 0,
                "playable": 0,
                "verified": 0,
                "contradictions": 0,
            }
        ],
    },
}
merged2 = module.merge(merged, current_with_tailscale)
demo2 = next(row for row in merged2["rows"] if row["provider"] == "demo")
assert demo2["residentialExitNodeProfile"]["outcome"] == "browser_challenge_persisted"
assert merged2["residentialProviderReplay"]["verifiedProviders"] == []
assert merged2["residentialProviderReplay"]["lastAttempt"]["available"] is True

print("WAF latest evidence merge contract passed")
