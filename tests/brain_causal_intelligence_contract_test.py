#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))

def load_module(name: str, path: Path):
    spec=importlib.util.spec_from_file_location(name,path)
    assert spec is not None and spec.loader is not None
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

runtime=load_module("causal_runtime_contract",ROOT/"scripts/adaptive_runtime/runtime_repair.py")

expected={
    "provider_transport_gap":"provider_origin_failover_v1",
    "route_proven_gap":"proven_route_terminal_traversal_v1",
    "chain_terminal_gap":"chain_terminal_extractor_v1",
    "candidate_replay_gap":"retained_candidate_replay_v1",
    "media_extraction_gap":"player_media_extractor_v1",
}
for failure,strategy in expected.items():
    assert runtime._new_strategy_id(failure,4)==strategy,(failure,runtime._new_strategy_id(failure,4))

raw={
    "executable":True,
    "route":"/api/search?q={query}",
    "role":"api",
    "method":"GET",
    "bodyKind":"none",
    "body":{},
    "headerNames":["accept","referer"],
    "origin":"https://provider-a.example",
}
local=runtime._safe_request_recipe(raw,peer=False)
peer=runtime._safe_request_recipe(raw,peer=True)
assert local and local.get("origin")=="https://provider-a.example",local
assert peer and "origin" not in peer,peer
runtime_src=(ROOT/"scripts/adaptive_runtime/runtime_repair.py").read_text(encoding="utf-8")
assert 'int(raw.get("providerSupport") or 0) < 2' in runtime_src
assert 'experiment_failure in {"candidate_replay_gap", "media_extraction_gap"}' in runtime_src
assert 'elif experiment_failure == "media_extraction_gap":' in runtime_src

planner=(ROOT/"engine_v2/scripts/plan-repairs.mjs").read_text(encoding="utf-8")
for status,failure in [
    ("CHAIN REACHED","chain_terminal_gap"),
    ("ROUTE PROVEN","route_proven_gap"),
    ("CANDIDATE OK","candidate_replay_gap"),
    ("PROVIDER NETWORK BLOCKED","provider_transport_gap"),
]:
    pos=planner.index(f'if (status === "{status}")')
    assert failure in planner[pos:pos+650],(status,failure)
assert "census_chain_reached_forbids_regression_to_search_or_detail" in planner
assert "census_route_proof_forbids_rediscovering_search" in planner

policy=json.loads((ROOT/"engine_v2/config/brain-policy.json").read_text(encoding="utf-8"))
negative=policy["production"]["negativeExperimentMemory"]
assert int(negative["maxVariantsPerSignature"])>=5,negative
assert int(negative["rotateExperimentAfterFailures"])>=1,negative

runner=(ROOT/"scripts/run_provider_brain_repair.py").read_text(encoding="utf-8")
assert '"directSkillApplication": False' in runner
assert '"experienceMemoryRole": "prior-only-no-acceptance-authority"' in runner
assert "deferredLearningProviders" in runner

workflow=(ROOT/".github/workflows/provider-recognition-repair-v6.yml").read_text(encoding="utf-8")
assert "FIELD_PROVIDER_BRAIN_ESCALATE" in workflow
assert "gh workflow run brain-learning-lab.yml" in workflow
assert "-f publish_proposal=true" in workflow

print("causal Brain intelligence contract passed")
