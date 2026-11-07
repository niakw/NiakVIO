#!/usr/bin/env python3
"""Enforce exact CLI-to-Deep-to-planner FORCE preference contract."""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "brain_force_preferred_context",
    ROOT / "scripts/brain_force_preferred_context.py",
)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
base = {"NUVIO_BRAIN_EXPLORATION_CHAIN": "1"}
argv = ["deep_repair.py", "--stage", "/tmp/sandbox", "--force-preferred-profile", "terminal_transition_graph_v11", "--max-rounds", "1"]
env = dict(base)
stripped, preferred = mod.consume(argv, env)
assert preferred == "terminal_transition_graph_v11"
assert env["NUVIO_BRAIN_FORCE_PREFERRED_PROFILE"] == preferred
assert stripped == ["deep_repair.py", "--stage", "/tmp/sandbox", "--max-rounds", "1"]
assert mod.consume(["deep_repair.py", "--max-rounds", "1"], dict(base)) == (["deep_repair.py", "--max-rounds", "1"], "")
for bad_argv, bad_env in (
    (argv + ["--force-preferred-profile", "terminal_transition_graph_v11"], base),
    (argv[:-3] + ["--force-preferred-profile"], base),
    (["deep", "--force-preferred-profile", "unknown/evil_v1"], base),
    (argv, {"NUVIO_BRAIN_EXPLORATION_CHAIN": "0"}),
    (argv, {**base, "NUVIO_BRAIN_PLANNER_MODE": "learning"}),
    (argv, {**base, "NUVIO_BRAIN_FORCE_PREFERRED_PROFILE": "terminal_transition_graph_v10"}),
):
    try:
        mod.consume(list(bad_argv), dict(bad_env))
    except ValueError:
        pass
    else:
        raise AssertionError("Unsafe or incompatible Deep FORCE context accepted")
portfolio = (ROOT / "scripts/run_provider_brain_repair.py").read_text(encoding="utf-8")
deep = (ROOT / "scripts/run_adaptive_deep_repair.py").read_text(encoding="utf-8")
planner = (ROOT / "scripts/brain_repair_runtime.py").read_text(encoding="utf-8")
workflow = (ROOT / ".github/workflows/github-actions-gate.yml").read_text(encoding="utf-8")
assert 'deep_cmd.extend(["--force-preferred-profile", preferred])' in portfolio
assert "consume_force_preferred(sys.argv, os.environ)" in deep
assert 'payload["forcePreferredStrategy"]' in planner
assert "FIELD_BRAIN_FORCE_PLANNER_INTENT_MISMATCH" in planner
assert "tests/brain_force_preferred_context_contract_test.py" in workflow
print("Brain explicit FORCE Deep context contract passed; playable media still unverified")
