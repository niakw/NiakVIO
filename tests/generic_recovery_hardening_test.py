#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# Historical peer domains are fallback-only. An explicit direct route is
# authoritative and must suppress old peer/LKG candidates; history participates
# only when NiakVIO has no current hub/direct route.
hubs = load("hubs", ROOT / "scripts" / "resolve_provider_hubs.py")
direct_candidates, _ = hubs.gather_candidates(
    "demo",
    {
        "direct_candidates": ["https://demo.current"],
        "historical_terminal_candidates": ["https://demo.backup"],
        "sources": [],
        "manifest_status": "Actif",
    },
    {},
    "quick",
    0.1,
)
assert [row.get("source_type") for row in direct_candidates] == ["curated_direct"]
assert all(row.get("url") != "https://demo.backup" for row in direct_candidates)

history_candidates, _ = hubs.gather_candidates(
    "demo",
    {
        "direct_candidates": [],
        "historical_terminal_candidates": ["https://demo.backup"],
        "sources": [],
        "manifest_status": "Actif",
    },
    {},
    "quick",
    0.1,
)
assert any(
    row.get("url") == "https://demo.backup" and row.get("source_type") == "historical_peer"
    for row in history_candidates
)

# Provider-v3 no longer owns generic source-shape runtime failover patches here.
# Keep that retirement explicit so a stale test cannot silently recreate the old
# adaptive-domain/runtime mutation layer after the DATA/Core reconstruction split.
for retired in (
    ROOT / "scripts" / "provider_patches" / "adaptive_domain_recovery.py",
    ROOT / "scripts" / "provider_patches" / "adaptive_runtime_recovery_v4.py",
):
    assert not retired.exists(), retired

print("generic recovery hardening test passed: hub_history_fallback=true retired_adaptive_runtime_patches=true")
