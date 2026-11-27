#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/adaptive_runtime/runtime_repair.py"
spec=importlib.util.spec_from_file_location("causal_profile_runtime",SCRIPT)
assert spec and spec.loader
runtime=importlib.util.module_from_spec(spec)
spec.loader.exec_module(runtime)

config={
    "provider_patches":{
        "demo":{
            "official_site":"https://demo.example",
            "published_types":["movie"],
            "learned_routes":["/detail/{slug}","/player/{id}"],
        }
    },
    "provider_capabilities":{
        "demo":{
            "strategy":"html_scraper",
            "catalogue_types":["movie"],
            "observed_origins":["https://demo.example"],
        }
    },
}
candidate={
    "key":"published:demo",
    "canonical_id":"demo",
    "source":"synthetic",
    "metadata":{
        "name":"Demo",
        "baseUrl":"https://demo.example",
        "supportedTypes":["movie"],
    },
    "brain_repair_plan":{
        "failureClass":"chain_terminal_gap",
        "experimentVariant":4,
        "experimentGeneration":2,
    },
}
result={
    "status":"no_streams",
    "evidence":{"streams_playable":0},
    "tests":[],
}
profiles=runtime.matching_profiles(candidate,result,"module.exports={};\n",config)
assert "chain_terminal_extractor_v1" in profiles,profiles
assert "adaptive_runtime_recovery" in profiles,profiles
assert runtime._is_causal_strategy_profile("chain_terminal_extractor_v1")
assert runtime._is_causal_strategy_profile("chain_terminal_extractor_v1_g3")
assert runtime.CAUSAL_STRATEGY_BASES["unknown_failure"] == "adaptive_runtime_recovery"
assert runtime.CAUSAL_STRATEGY_BASES["variant_coverage_gap"] == "player_media_extractor_v1"
assert runtime.CAUSAL_STRATEGY_BASES["content_identity_gap"] == "identity_alias_search_traversal_v1"
assert runtime._is_causal_strategy_profile("identity_alias_search_traversal_v1")
assert runtime._is_causal_strategy_profile("adaptive_runtime_recovery")
assert runtime._is_causal_strategy_profile("player_media_extractor_v1")
assert not runtime._is_causal_strategy_profile("expanded_family_strategy_v1")

with tempfile.TemporaryDirectory() as directory:
    stage=Path(directory)
    provider_dir=stage/"providers"
    provider_dir.mkdir(parents=True)
    source=provider_dir/"demo.js"
    raw=b"module.exports={getStreams:async function(){return []}};\n"
    source.write_bytes(raw)
    working={
        **candidate,
        "local_path":"providers/demo.js",
        "bytes":len(raw),
        "sha256":"synthetic",
        "local_patches":[],
    }
    original=runtime.load_overrides
    runtime.load_overrides=lambda: config
    try:
        repaired,error=runtime.create_repair_candidate(
            stage,working,"chain_terminal_extractor_v1",1
        )
        assert error is None,(repaired,error)
        assert isinstance(repaired,dict),repaired
        assert repaired["runtime_repair"]["profile"]=="chain_terminal_extractor_v1",repaired
        assert repaired["runtime_repair"]["strategy"]=="chain_terminal_extractor_v1",repaired
        records=repaired.get("local_patches") or []
        assert records[-1]["profile"]=="chain_terminal_extractor_v1",records
        assert records[-1]["strategy"]=="chain_terminal_extractor_v1",records

        player_working={
            **working,
            "brain_repair_plan":{
                "failureClass":"media_extraction_gap",
                "experimentVariant":1,
                "experimentGeneration":1,
            },
        }
        player_repaired,player_error=runtime.create_repair_candidate(
            stage,player_working,"player_media_extractor_v1",1
        )
        assert player_error is None,(player_repaired,player_error)
        assert isinstance(player_repaired,dict),player_repaired
        assert player_repaired["runtime_repair"]["profile"]=="player_media_extractor_v1",player_repaired
        assert player_repaired["runtime_repair"]["strategy"]=="player_media_extractor_v1",player_repaired
        player_records=player_repaired.get("local_patches") or []
        assert player_records and player_records[-1]["profile"]=="player_media_extractor_v1",player_records
        assert int(player_repaired.get("bytes") or 0)>len(raw),player_repaired

        mismatch,error=runtime.create_repair_candidate(
            stage,working,"chain_terminal_extractor_v1_g3",2
        )
        assert mismatch is None,mismatch
        assert str(error).startswith("patch_exception:ValueError:"),error
    finally:
        runtime.load_overrides=original

print("Brain causal strategy executable profile contract passed")
