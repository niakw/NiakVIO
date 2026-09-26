#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "local" / "run_force_experiment_farm.py"

spec = importlib.util.spec_from_file_location("local_force_experiment_farm", SCRIPT)
assert spec is not None and spec.loader is not None
farm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(farm)

row = {
    "provider": "demo",
    "status": "CHAIN REACHED",
    "dominantIssue": "terminal chain reached without playable media",
}
variants = farm.generated_experiments("demo", row, 24)
assert len(variants) == 24, len(variants)
fingerprints = [item["experimentFingerprint"] for item in variants]
assert len(set(fingerprints)) == len(fingerprints)
assert all(len(value) == 64 for value in fingerprints)
assert all(item["providerId"] == "demo" for item in variants)
assert all(item["profile"] == "chain_terminal_extractor_v1" for item in variants)
assert all(item["strategy"] == "terminal-media-extractor-with-playback-validation" for item in variants)

payload = farm.guidance_payload("a" * 40, variants[0])
assert payload["sourceSha"] == "a" * 40
assert payload["publicationAuthority"] is False
assert payload["directMutationAuthority"] is False
assert payload["proofAuthority"] is False
assert payload["providerCount"] == 1

source = SCRIPT.read_text(encoding="utf-8")
for forbidden in (
    "git push",
    "gh workflow run",
    "brain-learning-lab.yml",
    "publicationAuthority\": True",
    "directMutationAuthority\": True",
):
    assert forbidden not in source, forbidden
for required in (
    "run_adaptive_quick_repair.py",
    "run_adaptive_deep_repair.py",
    "WINNING_GUIDANCE.json",
    "STATE.json",
    "git\", \"worktree\", \"add",
    "quick_then_deep=true",
):
    assert required in source, required

print("local FORCE experiment farm contract passed")
