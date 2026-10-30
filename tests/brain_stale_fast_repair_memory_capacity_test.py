#!/usr/bin/env python3
"""Stale Fast memory bridge must honor live policy and retain rare providers."""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "merge_stale_fast_repair_memory.py"
spec = importlib.util.spec_from_file_location("stale_fast_capacity", SCRIPT)
assert spec and spec.loader
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)


def row(provider: str, signature: str, failures: int = 1, outcome: str = "rejected"):
    return {
        "providerId": provider,
        "signature": signature,
        "profile": "route_transition_graph_v2",
        "experimentVariant": 4,
        "experimentGeneration": 2,
        "executionObserved": True,
        "lastOutcome": outcome,
        "lastReason": "no-terminal",
        "failures": failures,
        "consecutiveFailures": failures,
        "successes": 0,
    }


capacity = bridge.configured_memory_capacity()
assert capacity == 16000, capacity  # live production policy, not historical 1000
baseline = {
    "schemaVersion": 1,
    "entries": [row("4khdhub", f"hot-{i}", 90) for i in range(1250)]
}
incoming = {"schemaVersion": 1, "entries": [row("uhdmovies", "rare", 1)]}
merged, stats = bridge.merge_memory(baseline, incoming, {"4khdhub", "uhdmovies"})
assert len(merged["entries"]) == 1251
assert stats == {"inspected": 1, "accepted": 1, "inserted": 1}
assert any(x["providerId"] == "uhdmovies" for x in merged["entries"])

# When over a *smaller* configured cap, canonical fair retention must protect
# rare-provider evidence despite much larger counters on the hot provider.
small = {
    "schemaVersion": 1,
    "entries": [row("4khdhub", f"hot-{i}", 100) for i in range(19)]
    + [row("uhdmovies", "rare", 1)]
}
extra = {"schemaVersion": 1, "entries": [row("4khdhub", "hot-extra", 200)]}
bounded, _ = bridge.merge_memory(small, extra, {"4khdhub"}, max_rows=20)
assert len(bounded["entries"]) == 20
assert any(x["providerId"] == "uhdmovies" for x in bounded["entries"])

# A stale rejection must never replace a current positive result.
positive = {"schemaVersion": 1, "entries": [row("4khdhub", "same", 1, "accepted")]}
negative = {"schemaVersion": 1, "entries": [row("4khdhub", "same", 200)]}
safe, _ = bridge.merge_memory(positive, negative, {"4khdhub"})
assert safe["entries"][0]["lastOutcome"] == "accepted"

# Exercise the real CLI, not just the Python helper.
with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    current = root / "current.json"
    prior = root / "prior.json"
    census = root / "census.json"
    current.write_text(json.dumps(baseline), encoding="utf-8")
    prior.write_text(json.dumps(incoming), encoding="utf-8")
    census.write_text(json.dumps({"repairQueue": ["4khdhub", "uhdmovies"]}), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--current", str(current),
         "--prior", str(prior), "--census", str(census)],
        check=True, text=True, capture_output=True,
    )
    assert "publicationAuthority=false" in result.stdout
    assert len(json.loads(current.read_text(encoding="utf-8"))["entries"]) == 1251

print("Stale Fast memory live-capacity, fairness and CLI regression passed")
