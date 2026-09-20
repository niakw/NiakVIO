#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
text=(ROOT/"scripts/provider_base_store.py").read_text(encoding="utf-8")

required=[
    "NIAKVIO_PROVIDER_ADAPTIVE_PLAYER_FANOUT_V25",
    "const seedCap = Math.min(16, Math.max(8, rankedSeeds.length));",
    "const requestBudget = Math.min(18, Math.max(10, queue.length + 4));",
    "while (queue.length && requests < requestBudget && streams.length < 12)",
]
for needle in required:
    assert needle in text, needle

assert "slice(0, 8).map(url => ({ url, depth: 0, referer }))" not in text
assert "while (queue.length && requests < 10 && streams.length < 12)" not in text
print("Provider shared adaptive player fanout contract passed")
