#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts"/"build_provider_repair_batch_plan.py"
spec=importlib.util.spec_from_file_location("batch_plan_causal_precedence",SCRIPT)
assert spec and spec.loader
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

# Deepest current proof wins over stale lower-layer issue text.
assert mod.action_for("CHAIN REACHED","chain","network_http_error")[0]=="terminal-extraction"
assert mod.action_for("ROUTE PROVEN","lookup","network_exception")[0]=="route-to-terminal"
assert mod.action_for("CANDIDATE OK","lookup","network_zero_result")[0]=="candidate-replay"

# Final causal network/harness status still owns its lane.
assert mod.action_for("PROVIDER NETWORK BLOCKED","none","network_http_error")[0]=="transport"
assert mod.action_for("HARNESS MISMATCH","lookup","waf_challenge")[0]=="harness-compatibility"
assert mod.action_for("HARNESS/ENV BLOCKED","none","network_exception")[0]=="harness-compatibility"

# Only proof-less issue fallback may route an otherwise unclassified row.
assert mod.action_for("NO PROOF","none","waf_challenge")[0]=="harness-compatibility"
assert mod.action_for("NO PROOF","none","network_http_error")[0]=="transport"

source=SCRIPT.read_text(encoding="utf-8")
assert "Final causal status is stronger than an older dominantIssue" in source
print("provider repair batch causal precedence contract passed")
