#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/run_provider_brain_repair.py"
spec=importlib.util.spec_from_file_location("provider_brain_repair",SCRIPT)
assert spec and spec.loader
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

# Deterministic horizontal partitioning must cover each provider exactly once.
providers=[f"provider-{i}" for i in range(257)]
for count in (1,2,4,8,16):
    buckets=[set() for _ in range(count)]
    for provider in providers:
        idx=mod.shard_for(provider,count)
        assert 0<=idx<count
        buckets[idx].add(provider)
        assert idx==mod.shard_for(provider,count)
    union=set().union(*buckets)
    assert union==set(providers)
    assert sum(len(x) for x in buckets)==len(providers)

assert mod.chunks(["a","b","c","d","e"],2)==[["a","b"],["c","d"],["e"]]


assert mod.experiment_rotation_decision(
    accepted_count=0, remaining_count=3, wave=1, max_waves=5, memory_advanced=True
)=="rotate"
assert mod.experiment_rotation_decision(
    accepted_count=0, remaining_count=3, wave=5, max_waves=5, memory_advanced=True
)=="exhausted"
assert mod.experiment_rotation_decision(
    accepted_count=0, remaining_count=3, wave=1, max_waves=5, memory_advanced=False
)=="stalled"
assert mod.experiment_rotation_decision(
    accepted_count=1, remaining_count=3, wave=1, max_waves=5, memory_advanced=True
)=="materialize"

with tempfile.TemporaryDirectory() as tmp:
    old_status,old_plan=mod.STATUS,mod.BATCH_PLAN
    try:
        mod.STATUS=Path(tmp)/"status.json"
        mod.BATCH_PLAN=Path(tmp)/"plan.json"
        mod.STATUS.write_text(json.dumps({
            "runId":"r1",
            "providers":[
                {"provider":"a","status":"ROUTE PROVEN"},
                {"provider":"b","status":"ROUTE PROVEN"},
                {"provider":"c","status":"CHAIN REACHED"},
                {"provider":"d","status":"PROVIDER NETWORK BLOCKED"},
            ],
            "repairQueue":["a","b","c","d"],
        }),encoding="utf-8")
        mod.BATCH_PLAN.write_text(json.dumps({
            "sourceRunId":"r1",
            "groups":[
                {
                    "groupId":"route-to-terminal|html_scraper",
                    "repairScope":"route-to-terminal",
                    "capabilityStrategy":"html_scraper",
                    "providers":["b","a"],
                },
                {
                    "groupId":"terminal-extraction|direct_media",
                    "repairScope":"terminal-extraction",
                    "capabilityStrategy":"direct_media",
                    "providers":["c"],
                },
            ],
        }),encoding="utf-8")
        batches=mod.repair_batches(["a","b","c","d"],48)
        assert [row["providers"] for row in batches]==[["b","a"],["c"],["d"]],batches
        assert batches[0]["groupId"]=="route-to-terminal|html_scraper"
        assert batches[1]["repairScope"]=="terminal-extraction"
        assert batches[2]["groupId"]=="unplanned"

        mod.BATCH_PLAN.write_text(json.dumps({"sourceRunId":"old","groups":[]}),encoding="utf-8")
        stale=mod.repair_batches(["d","b","a","c"],2)
        assert [row["providers"] for row in stale]==[["a","b"],["c","d"]],stale
        assert all(row["groupId"]=="fallback" for row in stale)
    finally:
        mod.STATUS,mod.BATCH_PLAN=old_status,old_plan

payload={
    "providers":[
        {"provider":"a","status":"PROVIDER JS BROKEN"},
        {"provider":"b","status":"HARNESS MISMATCH"},
        {"provider":"c","status":"FULL OK"},
    ],
    "brainQueue":["a","b"],
    "repairQueue":["a"],
    "symptomaticProviders":["a","b"],
}
assert mod.census_queue(payload, include_environment=False)=={"a"}
assert mod.census_queue(payload, include_environment=True)=={"a","b"}

health={
    "results":[
        {
            "key":"published:a",
            "status":"healthy",
            "evidence":{
                "streams_playable":2,
                "identity_verified_streams":2,
                "identity_unverified_streams":0,
            },
            "tests":[{
                "fixture":{"label":"A"},
                "streams_playable":2,
                "identity_verified_streams":2,
                "identity_unverified_streams":0,
            }],
        },
        {
            "key":"published:b",
            "status":"healthy",
            "evidence":{
                "streams_playable":1,
                "identity_verified_streams":1,
                "identity_contradiction_count":1,
            },
            "tests":[{
                "fixture":{"label":"B"},
                "streams_playable":1,
                "identity_verified_streams":1,
                "identity_contradiction_count":1,
            }],
        },
        {
            "key":"published:c",
            "status":"healthy",
            "evidence":{"streams_playable":1,"identity_verified_streams":0},
            "tests":[{
                "fixture":{"label":"C"},
                "streams_playable":1,
                "identity_verified_streams":0,
                "identity_unverified_streams":1,
            }],
        },
    ]
}
assert mod.fixed_providers(health)=={"a"}

repair={
    "rounds":[
        {"accepted":[
            {
                "parent_key":"published:a",
                "profile":"adaptive_runtime_recovery",
                "reason":"strict_playable_stream_improvement",
                "status_before":"no_streams",
                "status_after":"healthy",
                "streams_playable_before":0,
                "streams_playable_after":2,
            }
        ]}
    ]
}
accepted=mod.accepted_rows(repair)
assert accepted[0]["provider"]=="a"
assert accepted[0]["playableAfter"]==2

brain_summary=mod.sanitized_brain({
    "brain":{
        "plans":{
            "published:a":{
                "providerId":"a",
                "failureClass":"route_proven_gap",
                "signature":"sig",
                "action":"deferred_retry",
                "exitReason":"experiment_variants_exhausted",
                "repairScope":"deferred",
                "repairType":"experiment_strategy_exhausted",
                "learningDisposition":"queue_new_strategy_after_variant_exhaustion",
                "experimentVariant":4,
                "experimentVariantCount":5,
                "experimentExhausted":True,
                "negativeMemoryMatches":4,
                "allowedProfiles":[],
                "hypotheses":[],
            }
        }
    }
})
plan=brain_summary["plans"]["published:a"]
assert plan["experimentExhausted"] is True,plan
assert plan["repairScope"]=="deferred",plan
assert plan["exitReason"]=="experiment_variants_exhausted",plan

with tempfile.TemporaryDirectory() as tmp:
    old_memory,old_policy=mod.REPAIR_MEMORY,mod.BRAIN_POLICY
    try:
        mod.REPAIR_MEMORY=Path(tmp)/"memory.json"
        mod.BRAIN_POLICY=Path(tmp)/"policy.json"
        mod.BRAIN_POLICY.write_text(json.dumps({
            "production":{
                "negativeExperimentMemory":{
                    "rotateExperimentAfterFailures":1,
                    "maxVariantsPerSignature":5,
                }
            }
        }),encoding="utf-8")
        mod.REPAIR_MEMORY.write_text(json.dumps({
            "entries":[
                {
                    "providerId":"a",
                    "failureClass":"route_proven_gap",
                    "signature":"sig",
                    "profile":"adaptive_runtime_recovery",
                    "experimentVariant":variant,
                    "failures":1,
                    "consecutiveFailures":1,
                    "successes":0,
                }
                for variant in range(5)
            ]
        }),encoding="utf-8")
        just_exhausted={
            "plans":{
                "published:a":{
                    "providerId":"a",
                    "failureClass":"route_proven_gap",
                    "signature":"sig",
                    "experimentVariantCount":5,
                    "experimentExhausted":False,
                    "allowedProfiles":["adaptive_runtime_recovery"],
                }
            }
        }
        assert mod.exhausted_from_negative_memory(just_exhausted)=={"a"}
    finally:
        mod.REPAIR_MEMORY,mod.BRAIN_POLICY=old_memory,old_policy

source=SCRIPT.read_text(encoding="utf-8")
for required in (
    "run_adaptive_deep_repair.py",
    "build_brain_repair_experience.py",
    "brain-repair-experience.json",
    "stage_published.py",
    "materialize_provider_base_v3_store.py",
    "materialize_provider_v3_all.py",
    "validatedRepairLearningExecuted",
    "family-batched-multi-wave-brain-repair",
    "rotating_rejected_experiment",
    "experimentMemoryAdvanced",
    "providerSpecificRules",
    "wafEnvironmentExcludedByDefault",
    "selectionSource",
    "deferredLearningProviders",
    "deferredToLearning",
    "experimentExhausted",
    "learningDisposition",
    "repairQueue",
):
    assert required in source, required

# The orchestrator is portfolio-generic: current provider names must never become
# executable repair branches.
for forbidden in (
    "4khdhub",
    "showbox",
    "allanime",
    "mallumv",
    "wookafr",
    "moviebox",
):
    assert forbidden not in source.casefold(), forbidden

print("Provider Brain repair orchestrator contract passed")
