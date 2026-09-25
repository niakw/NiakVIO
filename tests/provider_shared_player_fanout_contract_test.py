#!/usr/bin/env python3
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
base=(ROOT/"scripts/provider_base_store.py").read_text(encoding="utf-8")

# Global ProviderBase contract: every provider that delegates player resolution
# to the shared crawler receives the same bounded multi-player fanout.
required=[
    "NIAKVIO_PROVIDER_ADAPTIVE_PLAYER_FANOUT_V25",
    "const seedCap = Math.min(16, Math.max(8, rankedSeeds.length));",
    "const requestBudget = Math.min(18, Math.max(10, queue.length + 4));",
    "while (queue.length && requests < requestBudget && streams.length < 12)",
    "return streams.slice(0, 40);",
]
for needle in required:
    assert needle in base, needle

assert "slice(0, 8).map(url => ({ url, depth: 0, referer }))" not in base
assert "while (queue.length && requests < 10 && streams.length < 12)" not in base

# Provider-local runtimes may adapt site-specific player discovery, but they
# must not silently truncate a shared-crawler result below the common 12-stream
# fanout. This scans the actual provider-local Blocs materialized for the
# current provider set instead of naming one or two providers.
materialization=json.loads((ROOT/"provider-v3-materialization.json").read_text(encoding="utf-8"))
local_paths=set()
for row in materialization.get("providers") or []:
    for applied in row.get("applied") or []:
        if applied.get("type")=="provider_lego" and str(applied.get("path") or "").startswith("scripts/provider_patches/"):
            local_paths.add(str(applied["path"]))

for relative in sorted(local_paths):
    source=(ROOT/relative).read_text(encoding="utf-8")
    if "_crawlDirectMedia" in source and ("out.length<c.maxStreams" in source or "out.length < c.maxStreams" in source):
        forbidden=(
            'maxStreams": int(cfg.get("max_streams") or 4)',
            'maxStreams": int(cfg.get("max_streams") or 5)',
            'maxStreams": max(1, min(6,',
            'maxStreams": max(1, min(8,',
        )
        for pattern in forbidden:
            assert pattern not in source, f"{relative}: local multi-player cap regressed via {pattern}"

# Current server-enumeration runtimes must also not stop before the shared
# fanout budget merely because a historical default used five servers.
vidrock=(ROOT/"scripts/provider_patches/vidrock_runtime_v1.py").read_text(encoding="utf-8")
assert 'maxStreams": max(1, min(12, int(cfg.get("max_streams") or 12)))' in vidrock

print(f"Provider global multiflux preservation contract passed: provider_local_blobs={len(local_paths)}")
