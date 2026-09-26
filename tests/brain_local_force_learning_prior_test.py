#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import os
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "brain_repair_runtime.py"
spec = importlib.util.spec_from_file_location("brain_repair_runtime_local_force", SCRIPT)
assert spec is not None and spec.loader is not None
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

row = {
    "providerId": "mallumv",
    "failureClass": "chain-terminal-gap",
    "targetLayer": "provider",
    "strategy": "terminal-media-extractor-with-playback-validation",
    "profile": "chain_terminal_extractor_v1",
    "confidence": 0.96,
    "priorOnly": True,
    "experiment": {
        "routePolicy": "owned_only",
        "recipePolicy": "current_plus_provider",
        "roleOrder": ["episode", "detail", "player", "source", "api", "other"],
        "terminalOnly": True,
        "aliasSearch": True,
        "responseSalvage": True,
        "documentRequestMining": False,
        "sessionBootstrap": False,
        "maxDepth": 5,
        "maxPages": 27,
        "maxEmbeds": 33,
        "maxRecipePasses": 4,
    },
    "experimentFingerprint": "a" * 64,
}
payload = {
    "schemaVersion": 2,
    "sourceSha": "b" * 40,
    "publicationAuthority": False,
    "directMutationAuthority": False,
    "proofAuthority": False,
    "rawMutationContentRetained": False,
    "privateContentRetained": False,
    "providerCount": 1,
    "rows": [row],
}

old_mode = os.environ.get("NUVIO_BRAIN_PLANNER_MODE")
try:
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        (root / "2026-09-26-test-winning-guidance.json").write_text(
            json.dumps(payload), encoding="utf-8"
        )
        mod.LOCAL_FORCE_RESULTS_DIR = root
        mod.LLM_GUIDANCE_PATH = None

        os.environ.pop("NUVIO_BRAIN_PLANNER_MODE", None)
        assert mod.planner_llm_guidance() == []

        os.environ["NUVIO_BRAIN_PLANNER_MODE"] = "learning"
        rows = mod.planner_llm_guidance()
        assert len(rows) == 1, rows
        loaded = rows[0]
        assert loaded["providerId"] == "mallumv"
        assert loaded["confidence"] == 0.84
        assert loaded["localForceAmbiguous"] is True
        assert loaded["guidanceKind"] == "local-force-baseline-coincident"
        assert loaded["sourceSha"] == "b" * 40
finally:
    if old_mode is None:
        os.environ.pop("NUVIO_BRAIN_PLANNER_MODE", None)
    else:
        os.environ["NUVIO_BRAIN_PLANNER_MODE"] = old_mode

planner = (ROOT / "engine_v2" / "scripts" / "plan-repairs.mjs").read_text(encoding="utf-8")
assert "!row.localForceAmbiguous || row.failureCompatibility === \"exact\"" in planner
assert "llmAdvisorLocalForceAmbiguous" in planner
assert "llmAdvisorGuidanceKind" in planner

print("Brain local FORCE Learning prior contract passed")
