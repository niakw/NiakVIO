#!/usr/bin/env python3
from __future__ import annotations
import importlib.util, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
spec=importlib.util.spec_from_file_location("adaptive_runtime_contract",ROOT/"scripts/adaptive_runtime/runtime_repair.py")
assert spec and spec.loader
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)

config={
 "provider_patches":{"demo":{"official_site":"https://demo.test","published_types":["movie"]}},
 "provider_capabilities":{"demo":{"strategy":"html_scraper"}},
}
base={
 "canonical_id":"demo",
 "metadata":{"name":"Demo","supportedTypes":["movie"]},
 "canonical":{},
 "brain_observed_request_recipes":[],
}
experiment={
 "routePolicy":"owned_plus_peer_generic",
 "recipePolicy":"current_only",
 "roleOrder":["api","player","detail","search","other"],
 "terminalOnly":False,
 "aliasSearch":True,
 "responseSalvage":True,
 "documentRequestMining":True,
 "sessionBootstrap":True,
 "maxDepth":5,
 "maxPages":17,
 "maxEmbeds":19,
 "maxRecipePasses":3,
}
candidate={**base,"brain_repair_plan":{"failureClass":"route_proven_gap","experimentVariant":0,"experimentGeneration":1,"llmAdvisorExperiment":experiment,"llmAdvisorExperimentFingerprint":"a"*64}}
options=mod._adaptive_runtime_options(candidate,config)
assert options,options
assert options["llm_experiment_applied"] is True,options
assert options["llm_experiment_fingerprint"]=="a"*64,options
assert options["max_depth"]==5 and options["max_pages"]==17 and options["max_embeds"]==19 and options["max_recipe_passes"]==3,options
assert options["alias_search"] is True and options["runtime_response_salvage"] is True,options
assert options["document_request_mining"] is True and options["session_bootstrap"] is True,options
assert "/search?q={query}" in options["search_paths"],options["search_paths"]
blocked_hosts=set(options["blocked_hosts"])
assert {"gstatic.com","www.gstatic.com","api.themoviedb.org"}.issubset(blocked_hosts),blocked_hosts

owned={**experiment,"routePolicy":"owned_only","terminalOnly":True,"aliasSearch":False,"maxDepth":2}
candidate2={**base,"brain_repair_plan":{"failureClass":"route_proven_gap","experimentVariant":0,"experimentGeneration":1,"llmAdvisorExperiment":owned,"llmAdvisorExperimentFingerprint":"b"*64}}
options2=mod._adaptive_runtime_options(candidate2,config)
assert options2,options2
assert "/search?q={query}" not in options2["search_paths"],options2["search_paths"]
assert options2["max_depth"]==2,options2
assert options2["llm_experiment_fingerprint"]=="b"*64,options2
assert options2!=options
print("Brain LLM experiment runtime contract passed")
