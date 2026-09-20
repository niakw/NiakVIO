#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
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

health={
    "results":[
        {"key":"published:a","status":"healthy","evidence":{"streams_playable":2}},
        {"key":"published:b","status":"healthy","evidence":{"streams_playable":1,"identity_contradiction_count":1}},
        {"key":"published:c","status":"no_streams","evidence":{"streams_playable":0}},
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

source=SCRIPT.read_text(encoding="utf-8")
for required in (
    "run_adaptive_deep_repair.py",
    "stage_published.py",
    "materialize_provider_base_v3_store.py",
    "materialize_provider_v3_all.py",
    "validatedRepairLearningExecuted",
    "multi-wave-brain-repair",
    "providerSpecificRules",
    "wafEnvironmentExcludedByDefault",
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
