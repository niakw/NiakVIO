#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import os
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
SANDBOX = SCRIPTS / "run_brain_learning_sandbox.py"
BRAIN = SCRIPTS / "brain_repair_runtime.py"
DEEP = SCRIPTS / "deep_repair_loop.py"

spec = importlib.util.spec_from_file_location("brain_learning_sandbox_chain", SANDBOX)
assert spec and spec.loader
sandbox = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sandbox)

brain_spec = importlib.util.spec_from_file_location("brain_runtime_learning_chain", BRAIN)
assert brain_spec and brain_spec.loader
brain = importlib.util.module_from_spec(brain_spec)
brain_spec.loader.exec_module(brain)

assert sandbox._learning_quick_argv(["sandbox.py", "--stage", "x"]) == [
    "sandbox.py", "--stage", "x", "--max-rounds", "3"
]
assert sandbox._learning_quick_argv(
    ["sandbox.py", "--stage", "x", "--max-rounds", "5"]
) == ["sandbox.py", "--stage", "x", "--max-rounds", "5"]

with patch.dict(os.environ, {
    "NUVIO_BRAIN_PLANNER_MODE": "learning",
    "NUVIO_BRAIN_EXPLORATION_CHAIN": "1",
}, clear=False):
    # Learning may retain non-publishable intermediate progress, but the
    # production Brain planner must never inherit exploration/FORCE authority.
    assert brain._exploration_chain_enabled() is False

deep = DEEP.read_text(encoding="utf-8")
assert 'exploration_chain_enabled = str(os.environ.get("NUVIO_BRAIN_EXPLORATION_CHAIN")' in deep
proposal = (SCRIPTS / "build_brain_repair_proposal.py").read_text(encoding="utf-8")
assert 'accepted.get("durable_promotion_eligible") is not True' in proposal
assert 'positive_content_identity_proof' in proposal
assert 'streams_playable_after' in proposal

print("Brain Learning non-publishable multi-step exploration contract passed")
