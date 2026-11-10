#!/usr/bin/env python3
"""Brain accepted programme -> compiler -> persisted prior -> replay, including S00.

This is a structural, isolated compiler/memory test; never a live playback proof.
"""
from __future__ import annotations
import importlib.util
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def load(name: str, filename: str):
    spec=importlib.util.spec_from_file_location(name,ROOT/"scripts"/filename)
    assert spec and spec.loader
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

compiler=load("brain_episode_replay_compiler","compile_brain_accepted_program_v3.py")
memory=load("brain_episode_replay_memory","brain_positive_program_memory.py")

program={
  "schemaVersion":1,"profile":"adaptive_runtime_recovery","revision":5,
  "options":{
    "base_url":"https://provider.example","types":["anime"],
    "experiment_failure_class":"chain_terminal_gap",
    "request_recipes":[
      {"origin":"https://provider.example","route":"/search?q={query}",
       "role":"search","method":"GET","response":"json","semanticType":"anime",
       "requiredBindings":[],"streamProof":False,"executable":True},
      {"origin":"https://provider.example",
       "route":"/series/{binding:id}/season/{binding:season}/episode/{binding:episode}/source",
       "role":"source","method":"GET","response":"json","semanticType":"anime",
       "requiredBindings":["id","season","episode"],
       "streamProof":True,"executable":True},
    ],
  },
}
compiled=compiler.compile_program(program,"synthetic-episode")
assert compiled["providerValuePlan"]
assert compiled["terminalRequestPlan"]
accepted={
  "provider":"synthetic-episode",
  "reason":"strict_playable_stream_improvement",
  "statusBefore":"no_streams","statusAfter":"healthy",
  "playableBefore":0,"playableAfter":1,
  "profile":"adaptive_runtime_recovery",
  "acceptedProgram":program,
  "brainPlan":{"failureClass":"chain_terminal_gap","signature":"offline-contract-only"},
}
with tempfile.TemporaryDirectory(prefix="brain-episode-memory-") as tmp:
    path=Path(tmp)/"positive.json"
    memory.merge_records([(accepted,compiled)],path=path)
    fetched=memory.provider_entries("synthetic-episode",path=path)
    assert len(fetched)==1
    assert not memory.load_memory(path)["rejectedEntries"]
    replay=memory.provider_request_recipes("synthetic-episode",path=path)
    sources=[x for x in replay if x.get("streamProof") is True]
    assert sources, replay
    wanted="/series/{binding:id}/season/{binding:season}/episode/{binding:episode}/source"
    assert any(x["route"]==wanted for x in sources),sources
    for source in sources:
        if source["route"]==wanted:
            assert set(source["requiredBindings"])=={"id","season","episode"},source
            assert source["semanticType"]=="anime",source
    assert memory.provider_program_fingerprint("synthetic-episode",path=path)
    # A newly replayed programme must be representable by the same compiler.
    replay_program={"schemaVersion":1,"profile":"adaptive_runtime_recovery","revision":5,
                    "options":{"base_url":"https://provider.example","types":["anime"],
                               "experiment_failure_class":"chain_terminal_gap",
                               "request_recipes":replay}}
    next_compiled=compiler.compile_program(replay_program,"synthetic-episode")
    assert next_compiled["providerValuePlan"],next_compiled
    route=next_compiled["providerValuePlan"][0]["steps"][0]["route"]
    assert route=="/series/{id}/season/{season}/episode/{episode}/source",route
    assert "{season}" in route and "{episode}" in route

print("FIELD_BRAIN_EPISODE_POSITIVE_MEMORY_REPLAY compilation=true persistence=true "
      "season_zero_coordinate_capability=true episode_binding_preserved=true "
      "provider_identity_bound=true decoded_playback_proven=false")
