#!/usr/bin/env python3
from __future__ import annotations

import importlib
import importlib.util
import json
import subprocess
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
            "malformed_request_count":malformed,
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

# A second HTTP 200 at the *same search frontier* must not be interpreted
# as Brain success. This was the actual 4KHDHub v3 failure mode: more requests,
# still 0 details, 0 media and 0 playable streams.
old_search = result("no_streams", 100, [
    {"status": 200, "infrastructure": False, "stage": "search"},
])
repeated_search = result("no_streams", 100, [
    {"status": 200, "infrastructure": False, "stage": "search"},
    {"status": 200, "infrastructure": False, "stage": "search"},
    {"status": 200, "infrastructure": False, "stage": "search"},
])
ok, reason = runtime.compare_exploration_progress(old_search, repeated_search)
assert not ok and reason == "exploration_request_amplification_without_frontier", (ok, reason)
assert runtime._observed_provider_frontier(repeated_search) == (1, "search")

# A real transition beyond lookup is useful Learning evidence (not FULL):
# the candidate must still independently pass playable identity tests.
observed_detail = result("no_streams", 100, [
    {"status": 200, "infrastructure": False, "stage": "search"},
    {"status": 200, "infrastructure": False, "stage": "detail"},
])
ok, reason = runtime.compare_exploration_progress(old_search, observed_detail)
assert ok and "provider-frontier:detail" in reason, (ok, reason)

# An HTTP 200 TMDB/infrastructure page does not prove provider frontier gain.
infrastructure_detail = result("no_streams", 100, [
    {"status": 200, "infrastructure": False, "stage": "search"},
    {"status": 200, "infrastructure": True, "stage": "detail"},
])
ok, reason = runtime.compare_exploration_progress(old_search, infrastructure_detail)
assert not ok, (ok, reason)

# New static proposal stages without an observed provider HTTP response are
# not enough to change Learning state.
invented_detail = result("no_streams", 100, [])
invented_detail["tests"][0]["debug_progress_stage"] = "detail"
assert runtime._observed_provider_frontier(invented_detail) == (0, "")

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
    def fake(items,mode,transient_negative_memory=None):
        captured["items"]=items
        captured["mode"]=mode
        captured["transient_negative_memory"]=transient_negative_memory or []
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

# A rejected child of a proven exploration parent is in-run negative memory,
# not a reason to discard the good parent. The next bounded replan must see the
# exact executed profile as failed so it can rotate strategy without waiting for
# a later workflow to persist global memory.
transient_candidate={
    "key":"aio:demo",
    "canonical_id":"demo",
    "metadata":{"supportedTypes":["movie","tv"]},
    "brain_exploration_parent":{"round":1,"productionAccepted":False},
    "brain_exploration_rejections":[{
        "providerId":"demo",
        "failureClass":"search_gap",
        "signature":"sig-demo",
        "profile":"provider_session_bootstrap_replay_v1",
        "strategyImplementationFingerprint":"a"*64,
        "llmAdvisorExperimentFingerprint":"b"*64,
        "experimentVariant":4,
        "experimentGeneration":2,
        "failures":1,
        "consecutiveFailures":1,
        "successes":0,
        "executionObserved":True,
    }],
}
transient_rows=brain.planner_transient_negative_memory(transient_candidate)
assert len(transient_rows)==1,transient_rows
assert transient_rows[0]["profile"]=="provider_session_bootstrap_replay_v1",transient_rows
assert transient_rows[0]["strategyImplementationFingerprint"]=="a"*64,transient_rows
assert transient_rows[0]["llmAdvisorExperimentFingerprint"]=="b"*64,transient_rows
assert transient_rows[0]["executionObserved"] is True,transient_rows

captured={}
original=brain._execute_planner
try:
    def fake_transient(items,mode,transient_negative_memory=None):
        captured["transient"]=transient_negative_memory or []
        brain.PLANS["aio:demo"]={"action":"probe-targeted-repair","failureClass":"search_gap"}
        return brain.PLANS
    brain._execute_planner=fake_transient
    brain.replan_observation(transient_candidate,progress,plan_key="aio:demo",mode="deep")
    assert captured["transient"],captured
    assert captured["transient"][0]["profile"]=="provider_session_bootstrap_replay_v1",captured
finally:
    brain._execute_planner=original
    brain.PLANS.clear()

# Aggregate health is not completion when one declared semantic category is
# still unproved. Preserve that debt across the planner boundary and replan from
# the unresolved fixture instead of stopping the exploration chain.
category_progress = {
    "key": "aio:demo",
    "status": "healthy",
    "score": 100,
    "evidence": {
        "streams_returned": 5,
        "streams_playable": 5,
        "identity_contradiction_count": 0,
        "duration_identity_mismatch_count": 0,
        "required_fixture_categories": ["movie", "tv"],
        "healthy_fixture_categories": ["tv"],
    },
    "tests": [
        {
            "status": "no_streams",
            "failure_class": "content_lookup_completed_no_streams",
            "fixture": {"category": "movie", "mediaType": "movie"},
            "stream_count": 0,
            "streams_returned": 0,
            "streams_playable": 0,
            "network_observations": [
                {"status": 200, "ok": True, "infrastructure": False, "stage": "search"}
            ],
        },
        {
            "status": "healthy",
            "failure_class": "",
            "fixture": {"category": "tv", "mediaType": "tv"},
            "stream_count": 5,
            "streams_returned": 5,
            "streams_playable": 5,
            "network_observations": [
                {"status": 200, "ok": True, "infrastructure": False, "stage": "media"}
            ],
        },
    ],
}
planner_result = brain._planner_result(category_progress)
assert planner_result["evidence"]["required_fixture_categories"] == ["movie", "tv"]
assert planner_result["evidence"]["healthy_fixture_categories"] == ["tv"]

adaptive_spec = importlib.util.spec_from_file_location(
    "category_coverage_adaptive_runtime",
    SCRIPTS / "adaptive_runtime" / "runtime_repair.py",
)
assert adaptive_spec and adaptive_spec.loader
adaptive_runtime = importlib.util.module_from_spec(adaptive_spec)
adaptive_spec.loader.exec_module(adaptive_runtime)
assert adaptive_runtime._adaptive_failure(category_progress) is True

planner_payload = {
    "mode": "deep",
    "explorationChain": True,
    "policy": json.loads((ROOT / "engine_v2/config/brain-policy.json").read_text(encoding="utf-8")),
    "learnedSkills": {},
    "historicalSolutions": [],
    "llmGuidance": [],
    "negativeMemory": [],
    "items": [{
        "key": "aio:demo",
        "candidate": brain._planner_candidate({
            "key": "aio:demo",
            "canonical_id": "demo",
            "metadata": {"supportedTypes": ["movie", "tv"]},
        }),
        "result": planner_result,
        "state": {
            "mutationCount": 1,
            "generatedBytes": 100,
            "elapsedMs": 1000,
            "signatureCounts": {},
        },
    }],
}
planner_proc = subprocess.run(
    ["node", str(ROOT / "engine_v2/scripts/plan-repairs.mjs")],
    cwd=ROOT,
    input=json.dumps(planner_payload, ensure_ascii=True).encode("ascii"),
    capture_output=True,
    check=False,
)
assert planner_proc.returncode == 0, planner_proc.stderr.decode("utf-8", errors="replace")
category_plan = json.loads(planner_proc.stdout.decode("utf-8"))["plans"]["aio:demo"]
assert category_plan["failureClass"] == "search_gap", category_plan
assert category_plan["action"] == "probe-targeted-repair", category_plan
assert category_plan["targetCategories"] == ["movie"], category_plan
assert "adaptive_runtime_recovery" in category_plan["allowedProfiles"], category_plan

deep=(SCRIPTS/"deep_repair_loop.py").read_text(encoding="utf-8")
adaptive=(SCRIPTS/"run_adaptive_deep_repair.py").read_text(encoding="utf-8")
orchestrator=(SCRIPTS/"run_provider_brain_repair.py").read_text(encoding="utf-8")
assert 'NUVIO_BRAIN_EXPLORATION_CHAIN' in deep
assert '"exploration_progress": []' in deep
assert '"explorationOnly": True' in deep
assert 'exploration_is_non_publishable' in deep
assert 'brain.replan_observation(candidate, result' in adaptive
assert 'candidate.pop("brain_exploration_parent", None)' not in adaptive
assert 'retryable_exploration_rejections' in deep
assert 'brain_exploration_rejections' in deep
assert 'FIELD_PROVIDER_BRAIN_DEEP_DECISION' in deep
assert 'production_ok={str(bool(accepted)).lower()}' in deep
assert 'bool(ok)' not in deep
assert 'identity_before=' in deep and 'identity_after=' in deep
assert 'identity_contradiction_count,' in deep
assert 'malformed_before=' in deep and 'malformed_after=' in deep
decision_idx=deep.index('FIELD_PROVIDER_BRAIN_DEEP_DECISION')
rejection_idx=deep.index('rejection_reason = reason if is_selected else "inferior_to_selected_variant"')
assert rejection_idx < decision_idx,(rejection_idx,decision_idx)
assert 'bounded_rounds = "3" if exploration_chain else "1"' in adaptive
assert 'if "--max-rounds" not in sys.argv:' in adaptive
assert 'sys.argv[index + 1] = bounded_rounds' not in adaptive
assert 'FIELD_BRAIN_SINGLE_HYPOTHESIS_BOUNDS' in adaptive
assert 'env["NUVIO_BRAIN_EXPLORATION_CHAIN"] = "1"' in orchestrator
assert 'parser.add_argument("--max-rounds-per-batch", type=int, default=3' in orchestrator
assert '"--max-rounds", str(max_rounds_per_batch)' in orchestrator

print("Brain bounded causal exploration-chain contract passed")
