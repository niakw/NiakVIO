#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "automation" / "provider-current-structure-evidence.json"
data = json.loads(path.read_text(encoding="utf-8"))

assert data["schemaVersion"] == 1
assert data["role"] == "provider-current-structure-evidence"
assert data["proofAuthority"] is False
assert data["executionAuthority"] is False

row = data["providers"]["coflix"]
assert row["sourceKind"] == "user-current-page"
assert row["originHost"] == "coflix.ac"
assert row["routes"] == [{
    "path": "/wp-json/coflix/v1/resolve",
    "method": "UNKNOWN",
    "role": "player-resolver",
}]
assert row["requestKeys"] == ["tmdb", "type", "year", "pid"]
assert row["fanout"]["groupCount"] == 2
assert row["fanout"]["groupVariantCounts"] == [10, 9]
assert row["fanout"]["indexedVariantCount"] == 19
assert row["fanout"]["languageLabels"] == ["VF", "VFF", "VOSTFR"]

blob = json.dumps(data, ensure_ascii=False)
for forbidden in ("<div", "data-cfp", "157336", "20467", "1fichier.com", "megaup.net", "veev.to"):
    assert forbidden not in blob, forbidden

print("current provider structure evidence contract passed")
