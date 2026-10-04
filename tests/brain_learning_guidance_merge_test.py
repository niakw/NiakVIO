#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "merge_brain_llm_guidance_memory.py"
spec = importlib.util.spec_from_file_location("merge_learning_guidance", SCRIPT)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

BRAIN = "b" * 40
PREV = "1" * 40
CURR = "2" * 40


def row(provider: str, profile: str, fp: str, confidence: float = 0.96) -> dict:
    return {
        "providerId": provider,
        "failureClass": "route-proven-gap",
        "targetLayer": "provider",
        "strategy": "search-detail-player-terminal-traversal",
        "profile": profile,
        "confidence": confidence,
        "priorOnly": True,
        "experiment": {
            "routePolicy": "owned_plus_peer",
            "recipePolicy": "current_plus_provider_peer",
            "roleOrder": ["search", "detail", "player", "source", "api"],
            "terminalOnly": False,
            "aliasSearch": False,
            "responseSalvage": True,
            "documentRequestMining": False,
            "sessionBootstrap": False,
            "maxDepth": 5,
            "maxPages": 24,
            "maxEmbeds": 24,
            "maxRecipePasses": 4,
        },
        "experimentFingerprint": fp,
    }


def payload(source: str, rows: list[dict], brain: str = BRAIN) -> dict:
    return {
        "schemaVersion": 2,
        "sourceSha": source,
        "brainLlmSha": brain,
        "publicationAuthority": False,
        "directMutationAuthority": False,
        "proofAuthority": False,
        "rawMutationContentRetained": False,
        "minConfidence": 0.8,
        "providerCount": len({r["providerId"] for r in rows}),
        "rows": rows,
    }


previous = payload(
    PREV,
    [
        row("moviebox", "player_media_extractor_v1", "a" * 64),
        row("mallumv", "chain_terminal_extractor_v1", "b" * 64),
        row("vidfast", "proven_route_terminal_traversal_v1", "c" * 64),
    ],
)
current = payload(
    CURR,
    [
        row("coflix", "player_media_extractor_v1", "d" * 64),
        # Exact duplicate must remain single and newest/current wins.
        row("moviebox", "player_media_extractor_v1", "a" * 64, confidence=0.99),
    ],
)

original = mod.source_drift
try:
    mod.source_drift = lambda _root, _previous, _current: (["MEMORY.md"], {"vidfast"})
    merged, stats = mod.merge(previous, current, repo_root=ROOT)
finally:
    mod.source_drift = original

keys = {
    (r["providerId"], r["profile"], r["experimentFingerprint"])
    for r in merged["rows"]
}
assert ("coflix", "player_media_extractor_v1", "d" * 64) in keys
assert ("moviebox", "player_media_extractor_v1", "a" * 64) in keys
assert ("mallumv", "chain_terminal_extractor_v1", "b" * 64) in keys
assert not any(key[0] == "vidfast" for key in keys)
movie = next(r for r in merged["rows"] if r["providerId"] == "moviebox")
assert movie["confidence"] == 0.99, movie
assert merged["sourceSha"] == CURR
assert merged["providerCount"] == 3
assert stats["carriedRows"] == 1, stats
assert stats["droppedProviderDriftRows"] == 1, stats

# A different Brain revision cannot be falsely attributed to the new model.
other_brain = payload(PREV, [row("allanime", "chain_terminal_extractor_v1", "e" * 64)], brain="c" * 40)
same, stats = mod.merge(other_brain, current, repo_root=ROOT)
assert not any(r["providerId"] == "allanime" for r in same["rows"])
assert stats["droppedBrainRevisionRows"] == 1

unsafe = payload(PREV, [])
unsafe["publicationAuthority"] = True
try:
    mod.merge(unsafe, current, repo_root=ROOT)
except ValueError:
    pass
else:
    raise AssertionError("unsafe guidance authority must be rejected")

print("Brain concurrent Learning guidance merge contract passed")
