#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

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


# Equal trust score: explicit principal/recommended must beat backup/mirror even
# when lexical URL ordering would otherwise put the backup first.
item = {
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
    "status": "site_authoritative",
    "official_site": "https://redirect.example",
    "site_candidates": [
        row("https://redirect.example", "authoritative source redirect destination", 120, 9),
        row("https://primary.example", "Principal Recommandé", 100, 1),
    ],
}
result = prioritize_authoritative_item(item)
assert result["official_site"] == "https://redirect.example", result
assert not result.get("candidate_priority_adjusted"), result

# Neutral ties preserve document order before lexical URL order.
item = {
    "status": "site_authoritative",
    "official_site": "https://z.example",
    "site_candidates": [
        row("https://a.example", "Visit", 90, 4),
        row("https://z.example", "Visit", 90, 1),
    ],
}
result = prioritize_authoritative_item(item)
assert result["official_site"] == "https://z.example", result

print("domain refresh semantic priority tests passed")
