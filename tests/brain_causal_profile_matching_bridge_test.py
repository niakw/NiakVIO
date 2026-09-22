#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def load(name: str, path: Path):
    spec=importlib.util.spec_from_file_location(name,path)
    assert spec and spec.loader
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

brain=load("causal_matching_brain",ROOT/"scripts/brain_repair_runtime.py")
runtime=load("causal_matching_runtime",ROOT/"scripts/adaptive_runtime/runtime_repair.py")

candidate={
    "key":"published:demo",
    "canonical_id":"demo",
    "metadata":{
        "name":"Demo",
        "baseUrl":"https://demo.example",
        "supportedTypes":["movie"],
    },
}
result={"status":"no_streams","evidence":{"streams_playable":0},"tests":[]}
config={
    "provider_patches":{
        "demo":{
            "official_site":"https://demo.example",
            "published_types":["movie"],
            "learned_routes":["/detail/{slug}","/player/{id}"],
        }
    },
    "provider_capabilities":{
        "demo":{"strategy":"html_scraper","catalogue_types":["movie"]},
    },
}
plan={
    "providerId":"demo",
    "failureClass":"chain_terminal_gap",
    "signature":"demo-signature",
    "action":"probe-targeted-repair",
    "allowedProfiles":["chain_terminal_extractor_v1"],
    "experimentVariant":4,
    "experimentGeneration":2,
}
brain.PLANS.clear()
brain.PLANS["published:demo"]=plan

wrapped=brain.wrap_matching_profiles(runtime.matching_profiles)
profiles=wrapped(candidate,result,"module.exports={};\n",config)
assert profiles==["chain_terminal_extractor_v1"],profiles
snapshot=candidate.get("brain_repair_plan") or {}
assert snapshot.get("failureClass")=="chain_terminal_gap",snapshot
assert snapshot.get("experimentVariant")==4,snapshot
assert snapshot.get("experimentGeneration")==2,snapshot

deep=(ROOT/"scripts/run_adaptive_deep_repair.py").read_text(encoding="utf-8")
quick=(ROOT/"scripts/run_adaptive_quick_repair.py").read_text(encoding="utf-8")
assert 'candidate["brain_repair_plan"] = brain._plan_snapshot(plan)' in deep
assert deep.index('candidate["brain_repair_plan"] = brain._plan_snapshot(plan)') < deep.index('profiles = list(_base_matching(candidate, result, source_text, config))')
assert 'candidate["brain_repair_plan"] = brain._plan_snapshot(plan)' in quick
assert quick.index('candidate["brain_repair_plan"] = brain._plan_snapshot(plan)') < quick.index('base = _base_matching_profiles(candidate, result, source_text, config)')

print("Brain causal profile matching bridge contract passed")
