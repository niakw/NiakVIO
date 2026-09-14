#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from domain_refresh_guard_wrapper import has_fresh_rollback_evidence


def item(label: str) -> dict:
    return {
        "selected_source_type": "hub",
        "site_candidates": [{"url": "https://historical.example", "label": label}],
    }

assert has_fresh_rollback_evidence(item("Domain - 1 Active"), "https://historical.example") is True
assert has_fresh_rollback_evidence(item("Domain Online"), "https://historical.example") is True
assert has_fresh_rollback_evidence(item("Domain - 3 Offline"), "https://historical.example") is False
assert has_fresh_rollback_evidence(item("Domain Inactive"), "https://historical.example") is False
assert has_fresh_rollback_evidence(item("Visit"), "https://historical.example") is False

print("domain refresh active-domain reuse guard tests passed")
