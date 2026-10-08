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

# A non-publishable Deep exploration parent may cross wave boundaries only
# inside the same Brain sandbox. Exact bytes + SHA are preserved, publication
# authority stays false, and the fresh wave will retest it as baseline.
with tempfile.TemporaryDirectory() as tmp:
    root=Path(tmp)
    stage1=root/"wave-1"/"stage"
    stage2=root/"wave-2"/"stage"
    rel=Path("providers/runtime-repairs/demo.js")
    payload=b"// safe exploration parent\n"
    digest=mod.hashlib.sha256(payload).hexdigest()
    (stage1/rel).parent.mkdir(parents=True,exist_ok=True)
    (stage1/rel).write_bytes(payload)
    reg1=stage1/"candidates.json"
    reg1.write_text(json.dumps({
        "candidates":[{
            "key":"published:demo",
            "canonical_id":"demo",
            "local_path":str(rel),
            "sha256":digest,
            "brain_exploration_parent":{
                "round":2,
                "reason":"sandbox_diagnostic_progress:returned",
                "productionAccepted":False,
            },
        }]
    }),encoding="utf-8")
    carry=mod.capture_cross_wave_exploration_parents(
        stage1,reg1,{"demo"},source_wave=1
    )
    assert set(carry)=={"demo"},carry
    assert carry["demo"]["candidate"]["brain_cross_wave_exploration_parent"]=={
        "sourceWave":1,
        "sandboxOnly":True,
        "publicationAuthority":False,
        "requiresBaselineRetest":True,
    },carry

    fresh=b"// published baseline\n"
    fresh_rel=Path("providers/demo.js")
    (stage2/fresh_rel).parent.mkdir(parents=True,exist_ok=True)
    (stage2/fresh_rel).write_bytes(fresh)
    reg2=stage2/"candidates.json"
    reg2.write_text(json.dumps({
        "candidates":[{
            "key":"published:demo",
            "canonical_id":"demo",
            "local_path":str(fresh_rel),
            "sha256":mod.hashlib.sha256(fresh).hexdigest(),
        }]
    }),encoding="utf-8")
    applied=mod.apply_cross_wave_exploration_parents(
        stage2,reg2,carry,["demo"],target_wave=2
    )
    assert applied==["demo"],applied
    merged=json.loads(reg2.read_text(encoding="utf-8"))["candidates"][0]
    assert merged["key"]=="published:demo",merged
    assert merged["local_path"]==str(rel),merged
    assert (stage2/rel).read_bytes()==payload
    cross=merged["brain_cross_wave_exploration_parent"]
    assert cross["sourceWave"]==1 and cross["targetWave"]==2,cross
    assert cross["sandboxOnly"] is True and cross["publicationAuthority"] is False,cross
    assert cross["requiresBaselineRetest"] is True,cross
    assert "provider_base_change_authorized" not in merged

    # Path escape can never become a cross-wave sandbox parent.
    escaped=stage1/"escaped.json"
    escaped.write_text(json.dumps({"candidates":[{
        "key":"published:bad",
        "canonical_id":"bad",
        "local_path":"../outside.js",
        "sha256":"0"*64,
        "brain_exploration_parent":{"productionAccepted":False},
    }]}),encoding="utf-8")
    assert mod.capture_cross_wave_exploration_parents(
        stage1,escaped,{"bad"},source_wave=1
    )=={}

assert mod.health_concurrency_for_batch(0,1)==1
assert mod.health_concurrency_for_batch(0,3)==3
assert mod.health_concurrency_for_batch(0,4)==4
assert mod.health_concurrency_for_batch(0,6)==6
assert mod.health_concurrency_for_batch(0,8)==8
assert mod.health_concurrency_for_batch(0,48)==8
assert mod.health_concurrency_for_batch(5,48)==5
assert mod.health_concurrency_for_batch(99,48)==8

# Reporting must preserve the configured concurrency mode without referring to
# the pre-batch global variable that was removed by packed-batch scaling.


assert mod.experiment_rotation_decision(
    accepted_count=0, remaining_count=3, wave=1, max_waves=5, memory_advanced=True
)=="rotate"
assert mod.experiment_rotation_decision(
    accepted_count=0, remaining_count=3, wave=5, max_waves=5, memory_advanced=True
)=="exhausted"
assert mod.experiment_rotation_decision(
    accepted_count=0, remaining_count=3, wave=1, max_waves=5, memory_advanced=False
)=="stalled"

# UHDMovies Repair 37705963499: an advisor-planned but non-executable
# hypothesis yielded no accepted candidate, no memory advancement, and
# previously *zero* Learning debt despite reachable detail pages. The Brain
# must escalate remaining providers instead of silently dropping them.
assert mod.stalled_experiment_learning_handoff(
    ["uhdmovies", "moviebox", "blocked"],
    {"blocked"},
) == {"uhdmovies", "moviebox"}
assert mod.stalled_experiment_learning_handoff(["blocked"], {"blocked"}) == set()
source_contract = SCRIPT.read_text(encoding="utf-8")
assert "all_deferred.update(learning_handoff)" in source_contract
assert "FIELD_PROVIDER_BRAIN_STALLED_LEARNING_HANDOFF" in source_contract

assert mod.experiment_rotation_decision(
    accepted_count=1, remaining_count=3, wave=1, max_waves=5, memory_advanced=True
)=="materialize"

generic_summary={
    "plans":{
        "published:y":{
            "providerId":"y",
            "action":"probe-targeted-repair",
            "allowedProfiles":["adaptive_runtime_recovery"],
            "llmAdvisorApplied":False,
            "llmAdvisorRescue":False,
        },
        "published:advisor":{
            "providerId":"advisor",
            "action":"probe-targeted-repair",
            "allowedProfiles":["player_media_extractor_v1"],
            "llmAdvisorApplied":True,
            "llmAdvisorRescue":False,
        },
        "published:named":{
            "providerId":"named",
            "action":"probe-targeted-repair",
            "allowedProfiles":["chain_terminal_extractor_v1"],
            "llmAdvisorApplied":False,
            "llmAdvisorRescue":False,
        },
    }
}
assert mod.generic_unadvised_learning_handoff(generic_summary,[],set())=={"y"}
assert mod.generic_unadvised_learning_handoff(
    generic_summary,[{"provider":"y"}],set()
)==set()
assert mod.generic_unadvised_learning_handoff(
    generic_summary,[],{"y"}
)==set()

advisor_summary={
    "plans":{
        "published:advisor":{
            "providerId":"advisor",
            "action":"probe-targeted-repair",
            "llmAdvisorApplied":True,
            "llmAdvisorProfile":"proven_route_terminal_traversal_v1",
            "llmAdvisorExperimentFingerprint":"a"*64,
        },
        "published:future":{
            "providerId":"future",
            "action":"probe-targeted-repair",
            "llmAdvisorApplied":True,
            "llmAdvisorProfile":"proven_route_terminal_traversal_v1",
            "llmAdvisorExperimentFingerprint":"b"*64,
        },
    }
}
advisor_memory={
    "entries":[
        {
            "providerId":"advisor",
            "profile":"proven_route_terminal_traversal_v1",
            "llmAdvisorExperimentFingerprint":"a"*64,
            "executionObserved":False,
            "lastOutcome":"profile_unavailable",
            "lastReason":"planned_profile_not_applicable_to_current_bytes",
        },
        {
            "providerId":"future",
            "profile":"proven_route_terminal_traversal_v1",
            "llmAdvisorExperimentFingerprint":"c"*64,
            "executionObserved":False,
            "lastOutcome":"profile_unavailable",
            "lastReason":"planned_profile_not_applicable_to_current_bytes",
        },
    ]
}
assert mod.unexecutable_llm_advisor_handoff(
    advisor_summary,memory_payload=advisor_memory
)=={"advisor"}
executed_memory=json.loads(json.dumps(advisor_memory))
executed_memory["entries"][0]["executionObserved"]=True
assert mod.unexecutable_llm_advisor_handoff(
    advisor_summary,memory_payload=executed_memory
)==set()
raw_accept=[
    {
        "provider":"mallu",
        "acceptedProgram":{"profile":"x"},
        "v3ProgramPersistence":{"status":"rejected","reason":"no provider-owned stream-proof recipe"},
    },
    {
        "provider":"good",
        "acceptedProgram":{"profile":"y"},
        "v3ProgramPersistence":{"status":"compiled"},
    },
    {
        "provider":"good",
        "acceptedProgram":{"profile":"y2"},
        "v3ProgramPersistence":{"status":"compiled"},
    },
]
durable=mod.durable_accepted_rows(raw_accept,{"good"})
assert [row["provider"] for row in durable]==["good"],durable
assert durable[0]["acceptedProgram"]["profile"]=="y2",durable
assert mod.durable_accepted_rows(raw_accept,set())==[]

source_text=SCRIPT.read_text(encoding="utf-8")
for required in (
    "capture_cross_wave_exploration_parents",
    "apply_cross_wave_exploration_parents",
    "FIELD_PROVIDER_BRAIN_CROSS_WAVE_EXPLORATION_APPLIED",
    "crossWaveExplorationCarryoverApplied",
    "crossWaveExplorationCarryoverCaptured",
    "same-run-sandbox-only-retested-no-publication-authority",
):
    assert required in source_text,required

with tempfile.TemporaryDirectory() as tmp:
    old_status,old_plan,old_memory=mod.STATUS,mod.BATCH_PLAN,mod.REPAIR_MEMORY
    try:
        mod.STATUS=Path(tmp)/"status.json"
        mod.BATCH_PLAN=Path(tmp)/"plan.json"
        mod.REPAIR_MEMORY=Path(tmp)/"memory.json"
        mod.REPAIR_MEMORY.write_text(json.dumps({
            "entries":[
                {"providerId":"a","failures":5,"successes":0},
                {"providerId":"c","failures":2,"successes":0},
                {"providerId":"d","failures":3,"successes":0},
            ]
        }),encoding="utf-8")
        mod.STATUS.write_text(json.dumps({
            "runId":"r1",
            "providers":[
                {"provider":"a","status":"ROUTE PROVEN"},
                {"provider":"b","status":"ROUTE PROVEN"},
                {"provider":"c","status":"CHAIN REACHED"},
                {"provider":"d","status":"PROVIDER NETWORK BLOCKED"},
                {"provider":"e","status":"FULL OK"},
            ],
            "repairQueue":["a","b","c","d"],
        }),encoding="utf-8")
        mod.BATCH_PLAN.write_text(json.dumps({
            "sourceRunId":"r1",
            "dynamicVariantProviders":["e"],
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
        assert [row["providers"] for row in batches]==[["b","a","c","d"]],batches
        assert batches[0]["groupId"]=="packed"
        assert batches[0]["repairScope"]=="mixed"
        assert [row["groupId"] for row in batches[0]["familyGroups"]]==[
            "route-to-terminal|html_scraper",
            "terminal-extraction|direct_media",
            "unplanned",
        ],batches
        bounded=mod.repair_batches(["a","b","c","d"],2)
        assert [row["providers"] for row in bounded]==[["b","a"],["c","d"]],bounded
        assert bounded[0]["groupId"]=="route-to-terminal|html_scraper"
        assert bounded[1]["groupId"]=="packed"

        regular,_,_=mod.select_targets(["e"],include_environment=False,shard_count=1,shard_index=0)
        forced,_,_=mod.select_targets(
            ["e"],include_environment=False,shard_count=1,shard_index=0,architecture_force=True
        )
        assert regular==[],regular
        assert forced==["e"],forced

        mod.BATCH_PLAN.write_text(json.dumps({
            "sourceRunId":"old",
            "dynamicVariantProviders":["e"],
            "groups":[],
        }),encoding="utf-8")
        stale=mod.repair_batches(["d","b","a","c"],2)
        assert [row["providers"] for row in stale]==[["b","c"],["d","a"]],stale
        assert all(row["groupId"]=="fallback" for row in stale)
        stale_forced,_,_=mod.select_targets(
            ["e"],include_environment=False,shard_count=1,shard_index=0,architecture_force=True
        )
        assert stale_forced==[],stale_forced
        pressure=mod.provider_attempt_pressure_map()
        assert pressure["a"]==5 and pressure["c"]==2 and pressure["d"]==3,pressure
    finally:
        mod.STATUS,mod.BATCH_PLAN,mod.REPAIR_MEMORY=old_status,old_plan,old_memory

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
assert accepted[0]["acceptedProgram"]=={}, accepted
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
                "llmAdvisorApplied":True,
                "llmAdvisorProfile":"proven_route_terminal_traversal_v1",
                "llmAdvisorSourceFailureClass":"route_proven_gap",
                "llmAdvisorFailureCompatibility":"exact",
                "llmAdvisorExperimentFingerprint":"d"*64,
                "llmAdvisorExperiment":{"maxDepth":5},
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
assert plan["llmAdvisorExperimentFingerprint"]=="d"*64,plan
assert plan["llmAdvisorExperiment"]["maxDepth"]==5,plan
assert plan["llmAdvisorFailureCompatibility"]=="exact",plan

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
assert '"healthConcurrency": health_concurrency_setting' in source
assert '"healthConcurrencyMode": "fixed" if health_concurrency_setting else "auto-per-batch"' in source
assert '"healthConcurrency": batch_concurrency' in source
assert '"healthConcurrency": concurrency' not in source
for required in (
    "run_adaptive_deep_repair.py",
    "build_brain_repair_experience.py",
    "brain-repair-experience.json",
    "stage_published.py",
    "materialize_provider_v3_one.py",
    "PROVIDER_BRAIN_INCREMENTAL_MATERIALIZATION_V1",
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
    "time_budget_exhausted",
    "resumeRecommended",
    "unvisitedProviders",
    "provider_attempt_pressure_map",
    "PROVIDER_BRAIN_PACKED_FAMILY_BATCHES_V1",
    "PROVIDER_BRAIN_BATCH_CONCURRENCY_V1",
    "PROVIDER_BRAIN_GENERIC_MISS_TO_LEARNING_V1",
    "PROVIDER_BRAIN_UNEXECUTABLE_LLM_TO_LEARNING_V1",
    "PROVIDER_BRAIN_DURABLE_ACCEPTANCE_V1",
    "rawLabAcceptedCount",
    "compileRejectedToLearning",
    "current_dynamic_completeness_queue",
    "--architecture-force",
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

source=(ROOT/"scripts/run_provider_brain_repair.py").read_text(encoding="utf-8")
assert 'def materialize(provider_ids:' in source
assert '"--provider",\n            provider_id' in source
assert '(sys.executable, "scripts/reconcile_provider_domain_metadata.py", "--rebuild")' not in source
materialize_source = source.split("def materialize(provider_ids:", 1)[1].split("\ndef main()", 1)[0]
assert "PROVIDER_BRAIN_INCREMENTAL_MATERIALIZATION_V1" in materialize_source
assert '"scripts/materialize_provider_v3_one.py"' in materialize_source
assert '"scripts/materialize_provider_v3_all.py"' not in materialize_source
assert '"scripts/materialize_provider_base_v3_store.py"' not in materialize_source
assert materialize_source.count('"scripts/validate_published_provider_config.py"') == 1
