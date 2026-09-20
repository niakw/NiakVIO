#!/usr/bin/env python3
from __future__ import annotations

import importlib
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPTS=ROOT/"scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0,str(SCRIPTS))

import runtime_repair as runtime
import brain_repair_runtime as brain

def result(status, score, observations=None, contradictions=0, malformed=0):
    return {
        "key":"aio:demo",
        "status":status,
        "score":score,
        "evidence":{
            "streams_returned":0,
            "streams_playable":0,
            "identity_contradiction_count":contradictions,
            "duration_identity_mismatch_count":0,
        },
        "tests":[{
            "stream_count":0,
            "streams_returned":0,
            "streams_playable":0,
            "runtime_errors":0,
            "malformed_requests":malformed,
            "network_observations":observations or [],
        }],
    }

parent=result("provider_unreachable",0,[])
progress=result("no_streams",100,[{
    "url":"https://provider.example/search?q=test",
    "status":200,
    "infrastructure":False,
}])
ok,reason=runtime.compare_exploration_progress(parent,progress)
assert ok,reason
assert "provider-" in reason,reason

score_only=result("no_streams",100,[])
ok,reason=runtime.compare_exploration_progress(parent,score_only)
assert not ok and reason=="exploration_no_causal_evidence_gain",(ok,reason)

bad_identity=result("no_streams",100,[{
    "url":"https://provider.example/search?q=test",
    "status":200,
    "infrastructure":False,
}],contradictions=1)
ok,reason=runtime.compare_exploration_progress(parent,bad_identity)
assert not ok and "identity" in reason,(ok,reason)

bad_request=result("no_streams",100,[{
    "url":"https://provider.example/search?q=test",
    "status":200,
    "infrastructure":False,
}],malformed=1)
ok,reason=runtime.compare_exploration_progress(parent,bad_request)
assert not ok and "malformed" in reason,(ok,reason)

captured={}
original=brain._execute_planner
try:
    def fake(items,mode):
        captured["items"]=items
        captured["mode"]=mode
        brain.PLANS["aio:demo"]={"action":"probe-targeted-repair","failureClass":"route_proven_gap"}
        return brain.PLANS
    brain._execute_planner=fake
    plan=brain.replan_observation(
        {"key":"aio:demo","canonical_id":"demo","metadata":{"supportedTypes":["movie"]}},
        progress,
        plan_key="aio:demo",
        mode="deep",
    )
    assert plan["action"]=="probe-targeted-repair",plan
    assert captured["mode"]=="deep",captured
    assert captured["items"][0]["key"]=="aio:demo",captured
finally:
    brain._execute_planner=original
    brain.PLANS.clear()

deep=(SCRIPTS/"deep_repair_loop.py").read_text(encoding="utf-8")
adaptive=(SCRIPTS/"run_adaptive_deep_repair.py").read_text(encoding="utf-8")
orchestrator=(SCRIPTS/"run_provider_brain_repair.py").read_text(encoding="utf-8")
assert 'NUVIO_BRAIN_EXPLORATION_CHAIN' in deep
assert '"exploration_progress": []' in deep
assert '"explorationOnly": True' in deep
assert 'exploration_is_non_publishable' in deep
assert 'brain.replan_observation(candidate, result' in adaptive
assert 'bounded_rounds = "3" if exploration_chain else "1"' in adaptive
assert 'env["NUVIO_BRAIN_EXPLORATION_CHAIN"] = "1"' in orchestrator
assert '"--max-rounds", "3"' in orchestrator

print("Brain bounded causal exploration-chain contract passed")
