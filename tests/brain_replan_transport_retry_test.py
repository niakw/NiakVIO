#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
ADAPTIVE = SCRIPTS / "adaptive_runtime"
sys.path.insert(0, str(ADAPTIVE))
sys.path.insert(1, str(SCRIPTS))

spec = importlib.util.spec_from_file_location(
    "adaptive_brain_transport_tested",
    ADAPTIVE / "brain_repair_runtime.py",
)
assert spec and spec.loader
brain = importlib.util.module_from_spec(spec)
spec.loader.exec_module(brain)

calls: list[dict] = []
real_run = brain.subprocess.run

def fake_run(args, **kwargs):
    calls.append(dict(kwargs))
    if len(calls) == 1:
        raise subprocess.CalledProcessError(
            2,
            args,
            stderr=b"brain_planner_input_invalid bytes=106668 reason=SyntaxError\n",
        )
    env = kwargs.get("env") or {}
    input_file = env.get("NUVIO_BRAIN_PLANNER_INPUT_FILE")
    assert input_file, kwargs
    assert kwargs.get("input") == b"", kwargs
    raw = Path(input_file).read_bytes()
    parsed = json.loads(raw.decode("ascii"))
    assert parsed["items"][0]["key"] == "published:demo"
    stdout = json.dumps({
        "plans": {
            "published:demo": {
                "providerId": "demo",
                "action": "probe-targeted-repair",
                "allowedProfiles": ["adaptive_runtime_recovery"],
                "signature": "after-file-retry",
            }
        }
    }).encode()
    return subprocess.CompletedProcess(args, 0, stdout=stdout, stderr=b"")

brain.subprocess.run = fake_run
try:
    plans = brain._run_planner_batch(
        {
            "mode": "deep",
            "policy": {},
            "learnedSkills": {},
            "negativeMemory": [],
        },
        [{
            "key": "published:demo",
            "candidate": {"canonical_id": "demo"},
            "result": {
                "status": "no_streams",
                "tests": [{
                    "failure_class": "content_lookup_completed_no_streams",
                    "network_observations": [
                        {"status": 200, "stage": "search", "infrastructure": False}
                    ],
                }],
            },
            "state": {},
        }],
    )
finally:
    brain.subprocess.run = real_run

assert len(calls) == 2, calls
assert plans["published:demo"]["signature"] == "after-file-retry", plans

# Replan must use the adaptive transport, not the base runtime's direct stdin path.
seen: list[dict] = []
original_batch = brain._run_planner_batch
def fake_batch(base_payload, items):
    seen.append({"base": base_payload, "items": items})
    return {
        "published:demo": {
            "providerId": "demo",
            "action": "probe-targeted-repair",
            "allowedProfiles": ["adaptive_runtime_recovery"],
            "signature": "adaptive-replan",
        }
    }

brain._run_planner_batch = fake_batch
brain._BASE.PLANS.clear()
try:
    plan = brain.replan_observation(
        {"key": "published:demo", "canonical_id": "demo"},
        {
            "status": "no_streams",
            "evidence": {"streams_returned": 0, "streams_playable": 0},
            "tests": [{
                "failure_class": "content_lookup_completed_no_streams",
                "network_observations": [],
            }],
        },
        plan_key="published:demo",
        mode="deep",
    )
finally:
    brain._run_planner_batch = original_batch

assert seen, "adaptive replan did not use bounded transport"
assert plan["signature"] == "adaptive-replan", plan

# The initial adaptive update_plans transport must preserve the same explicit
# production exploration-chain bit as replan_observation. FORCE representative
# Repair 37691213661 lost this field here, so Node saw explorationChain=false
# and deferred a registered post-exhaustion strategy instead of executing it.
update_seen: list[dict] = []
original_batch = brain._run_planner_batch
old_chain = os.environ.get("NUVIO_BRAIN_EXPLORATION_CHAIN")
old_mode = os.environ.get("NUVIO_BRAIN_PLANNER_MODE")
def fake_update_batch(base_payload, items):
    update_seen.append({"base": base_payload, "items": items})
    return {
        "published:demo": {
            "providerId": "demo",
            "action": "probe-targeted-repair",
            "allowedProfiles": ["route_transition_graph_v2"],
            "signature": "adaptive-initial-plan",
            "explorationChainEnabled": bool(base_payload.get("explorationChain")),
        }
    }

brain._run_planner_batch = fake_update_batch
brain._BASE.PLANS.clear()
try:
    os.environ["NUVIO_BRAIN_EXPLORATION_CHAIN"] = "1"
    os.environ.pop("NUVIO_BRAIN_PLANNER_MODE", None)
    with tempfile.TemporaryDirectory(prefix="brain-adaptive-chain-") as tmp:
        registry = Path(tmp) / "candidates.json"
        registry.write_text(json.dumps({
            "candidates": [{
                "key": "published:demo",
                "canonical_id": "demo",
                "upstream_id": "demo",
            }]
        }), encoding="utf-8")
        plans = brain.update_plans(
            registry,
            {
                "results": [{
                    "key": "published:demo",
                    "status": "no_streams",
                    "evidence": {"streams_returned": 0, "streams_playable": 0},
                    "tests": [{
                        "failure_class": "content_lookup_completed_no_streams",
                        "network_observations": [],
                    }],
                }]
            },
            "deep",
        )
finally:
    brain._run_planner_batch = original_batch
    if old_chain is None:
        os.environ.pop("NUVIO_BRAIN_EXPLORATION_CHAIN", None)
    else:
        os.environ["NUVIO_BRAIN_EXPLORATION_CHAIN"] = old_chain
    if old_mode is None:
        os.environ.pop("NUVIO_BRAIN_PLANNER_MODE", None)
    else:
        os.environ["NUVIO_BRAIN_PLANNER_MODE"] = old_mode

assert update_seen, "adaptive initial planning did not use bounded transport"
assert update_seen[0]["base"]["explorationChain"] is True, update_seen[0]
assert plans["published:demo"]["explorationChainEnabled"] is True, plans

planner_source = (ROOT / "engine_v2" / "scripts" / "plan-repairs.mjs").read_text(encoding="utf-8")
assert "NUVIO_BRAIN_PLANNER_INPUT_FILE" in planner_source
assert "brain_planner_input_invalid bytes=" in planner_source

print("Brain causal replan transport retry contract passed")
