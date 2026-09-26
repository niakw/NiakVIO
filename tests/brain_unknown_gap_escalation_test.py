#!/usr/bin/env python3
from __future__ import annotations
import json
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PLANNER=ROOT/"engine_v2/scripts/plan-repairs.mjs"
policy={
  "production":{
    "negativeExperimentMemory":{
      "rotateExperimentAfterFailures":1,
      "maxVariantsPerSignature":5,
      "finalVariantGeneration":2,
      "maxLearningGenerationsPerSignature":5,
    },
    "maxHypotheses":3,
    "maxMutationsPerProvider":2,
    "maxRepeatedSignature":2,
    "maxGeneratedBytesPerProvider":180000,
    "maxElapsedMsPerProvider":45000,
  },
  "skillMaturity":{},
}
guidance=[{
  "providerId":"synthetic-unknown-gap",
  "failureClass":"provider_transport_gap",
  "targetLayer":"provider",
  "strategy":"meta-gap-provider-transport-composition",
  "profile":"provider_origin_failover_v1",
  "confidence":0.86,
  "priorOnly":True,
  "experiment":{
    "routePolicy":"owned_plus_peer",
    "recipePolicy":"current_plus_provider",
    "roleOrder":["api","search","detail","player","source","episode","other"],
    "terminalOnly":False,
    "aliasSearch":True,
    "responseSalvage":True,
    "documentRequestMining":True,
    "sessionBootstrap":True,
    "maxDepth":5,
    "maxPages":24,
    "maxEmbeds":24,
    "maxRecipePasses":5,
  },
  "experimentFingerprint":"e"*64,
  "guidanceKind":"meta-gap-synthesis",
}]
payload={
  "mode":"deep",
  "explorationChain":True,
  "policy":policy,
  "learnedSkills":{},
  "historicalSolutions":[],
  "llmGuidance":guidance,
  "negativeMemory":[],
  "items":[{
    "key":"published:synthetic-unknown-gap",
    "candidate":{
      "canonical_id":"synthetic-unknown-gap",
      "metadata":{"supportedTypes":["anime"]},
    },
    "result":{
      "status":"runtime_error",
      "evidence":{"streams_playable":0,"streams_returned":0},
      "tests":[{
        "fixture":{"mediaType":"anime","category":"anime","title":"Synthetic"},
        "failure_class":"synthetic_novel_gap",
        "status":"runtime_error",
        "runtime_errors":["synthetic"],
        "network_observations":[],
        "streams_playable":0,
        "stream_count":0,
      }],
    },
    "state":{},
  }],
}
completed=subprocess.run(
  ["node",str(PLANNER)],cwd=ROOT,input=json.dumps(payload),
  capture_output=True,text=True,check=True,timeout=20,
)
plan=next(iter((json.loads(completed.stdout).get("plans") or {}).values()))
assert plan["failureClass"]=="unknown_failure",plan
assert plan["architectureGapEscalation"] is True,plan
assert plan["metaGapEscalated"] is True,plan
assert plan["repairType"]=="synthesized_strategy",plan
assert plan["llmAdvisorProfile"]=="adaptive_runtime_recovery",plan
assert plan["llmAdvisorGuidanceKind"]=="meta-gap-synthesis",plan
assert plan["action"]=="probe-targeted-repair",plan
print("Brain unknown architecture-gap escalation test passed")
