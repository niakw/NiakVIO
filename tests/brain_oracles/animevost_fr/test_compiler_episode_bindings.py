#!/usr/bin/env python3
"""Reverse Brain pipeline: retain exact season/episode through acceptance compiler.

A manual reference repair proves the missing behavior in isolation; this test
proves the Brain's accepted program can encode the same episode-aware route.
It does NOT claim a Brain-generated accepted program or terminal stream.
"""
from __future__ import annotations
import copy
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
source = ROOT / "scripts" / "compile_brain_accepted_program_v3.py"
spec = importlib.util.spec_from_file_location("brain_oracle_compiler",source)
assert spec and spec.loader
compiler = importlib.util.module_from_spec(spec)
spec.loader.exec_module(compiler)

program = {
  "profile":"adaptive_runtime_recovery", "revision":5, "schemaVersion":1,
  "options":{
    "base_url":"https://animevost.fr","user_agent":"Nuvio-Oracular-Test/1.0",
    "types":["anime"],"experiment_failure_class":"media_extraction_gap",
    "request_recipes":[
      {"origin":"https://animevost.fr","route":"/api/animes/search?q={query}",
       "role":"search","semanticType":"anime","method":"GET",
       "response":"json","requiredBindings":[],"headerNames":["accept"],
       "executable":True},
      {"origin":"https://animevost.fr",
       "route":"/api/animes/{binding:slug}/seasons/{binding:season}/episodes/{binding:episode}/sources",
       "role":"episode","semanticType":"anime","method":"GET",
       "response":"json","requiredBindings":["slug","season","episode"],
       "headerNames":["accept"],"executable":True,"streamProof":True}
    ]
  }
}
compiled = compiler.compile_program(program,"animevost-fr")
assert compiled["provider"] == "animevost-fr"
assert compiled["providerValuePlan"], compiled
step = compiled["providerValuePlan"][0]["steps"][0]
assert step["route"] == "/api/animes/{slug}/seasons/{season}/episodes/{episode}/sources", step
assert step["streamProof"] is True
assert step["semanticTypes"] == ["anime"]
assert compiled["terminalRequestPlan"][0]["requiredBindings"] == ["slug","season","episode"]

saved=compiler.apply_compiled({"provider_patches":{"animevost-fr":{}}},compiled)
assert saved["provider_patches"]["animevost-fr"]["provider_value_plan"][0]["steps"][0] == step

# Only exact provider ID and episodic coordinates can be interpolated.
movie=copy.deepcopy(program)
movie["options"]["types"]=["movie"]
for r in movie["options"]["request_recipes"]:r["semanticType"]="movie"
try: compiler.compile_program(movie,"animevost-fr")
except ValueError as error: assert "episodic coordinate binding on movie lane" in str(error),error
else: raise AssertionError("movie lane accepted episodic provider path")

unbound=copy.deepcopy(program)
unbound["options"]["request_recipes"][1]["route"]="/api/animes/{binding:season}/episodes/{binding:episode}"
unbound["options"]["request_recipes"][1]["requiredBindings"]=["season","episode"]
try: compiler.compile_program(unbound,"animevost-fr")
except ValueError as error: assert "dependent recipe not representable" in str(error),error
else: raise AssertionError("episode-only path lost provider correlated identity")

unsafe=copy.deepcopy(program)
unsafe["options"]["request_recipes"][1]["route"]="/api/animes/{binding:token}/episodes/{binding:episode}"
unsafe["options"]["request_recipes"][1]["requiredBindings"]=["token","episode"]
try: compiler.compile_program(unsafe,"animevost-fr")
except ValueError as error: assert "unsupported" in str(error),error
else: raise AssertionError("untrusted provider token binding accepted")

# The actual generated ProviderBase must consume these exact fields and keep 0.
runtime=(ROOT/"scripts"/"provider_base_store.py").read_text(encoding="utf-8")
assert "season: values.season" in runtime
assert "episode: values.episode" in runtime
assert "const stepUrl = _recipeUrl(stepRoute, values, stepBase);" in runtime
assert "season == null ? \"\" : season" in runtime
print("FIELD_BRAIN_EPISODE_BINDING_ORACLE compiled=true persisted=true "
      "season_zero_preserved=true movie_lanes_rejected=true unsafe_binding_rejected=true")
