#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "promote_local_force_guidance.py"
WORKFLOW = ROOT / ".github" / "workflows" / "provider-recognition-repair-v6.yml"

spec = importlib.util.spec_from_file_location("promote_local_force_guidance", SCRIPT)
assert spec is not None and spec.loader is not None
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

row = mod.validate_row({
    "providerId": "animevostfr",
    "failureClass": "candidate-replay-gap",
    "targetLayer": "provider",
    "strategy": "same-provider-candidate-program-replay",
    "profile": "retained_candidate_replay_v1",
    "confidence": 0.96,
    "priorOnly": True,
    "experiment": {
        "routePolicy": "owned_plus_peer",
        "recipePolicy": "current_only",
        "roleOrder": ["api", "source", "detail", "episode", "other", "player"],
        "terminalOnly": False,
        "aliasSearch": True,
        "responseSalvage": False,
        "documentRequestMining": False,
        "sessionBootstrap": False,
        "maxDepth": 3,
        "maxPages": 17,
        "maxEmbeds": 19,
        "maxRecipePasses": 2,
    },
    "experimentFingerprint": "a" * 64,
    "localExperimentSource": "brain-llm-guidance",
    "guidanceSourceSha": "b" * 40,
})
assert row["providerId"] == "animevostfr"
assert row["profile"] == "retained_candidate_replay_v1"
assert row["priorOnly"] is True
assert mod.canon("AnimeVOST_FR") == "animevost-fr"

assert "providers/" in mod.MATERIAL_PROVIDER_PREFIXES
assert "provider-overrides.json" in mod.MATERIAL_PROVIDER_INPUTS
assert "provider_catalog.json" in mod.MATERIAL_PROVIDER_INPUTS

workflow = WORKFLOW.read_text(encoding="utf-8")
for needle in (
    "promote_local_force_candidates:",
    "Promote persisted local FORCE candidates for current-byte revalidation",
    "scripts/promote_local_force_guidance.py",
    "promoteLocalForceCandidates",
    "local FORCE candidate promotion is valid only in force mode",
    "NIAKVIO_BRAIN_LLM_GUIDANCE=$RUNNER_TEMP/local-force-promoted-guidance.json",
):
    assert needle in workflow, needle

print("Brain local FORCE promotion bridge contract passed")
