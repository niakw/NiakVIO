#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/adaptive_runtime/runtime_repair.py"
spec=importlib.util.spec_from_file_location("adaptive_runtime_positive_priority",SCRIPT)
assert spec and spec.loader
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

positive_recipe={
    "route":"/search.php?q={query}",
    "origin":"https://demo.example",
    "role":"search",
    "method":"GET",
    "bodyKind":"none",
    "body":{},
    "headerNames":["accept","referer","user-agent"],
    "response":"html-or-text",
    "semanticType":"movie",
    "streamProof":False,
    "requiredBindings":[],
    "executable":True,
    "source":"positive-program-memory",
}
legacy_recipe={
    "route":"/legacy-search?q={query}",
    "origin":"https://demo.example",
    "role":"search",
    "method":"GET",
    "bodyKind":"none",
    "body":{},
    "headerNames":["accept"],
    "response":"html-or-text",
    "semanticType":"movie",
    "streamProof":False,
    "requiredBindings":[],
    "executable":True,
    "source":"provider-experience",
}
current_recipe={
    "route":"/fresh-search?q={query}",
    "origin":"https://demo.example",
    "role":"search",
    "method":"GET",
    "bodyKind":"none",
    "body":{},
    "headerNames":["accept"],
    "response":"html-or-text",
    "semanticType":"movie",
    "streamProof":False,
    "requiredBindings":[],
    "executable":True,
    "source":"current-observation",
}

old_routes=mod.positive_program_routes
old_recipes=mod.positive_program_request_recipes
old_ua=mod.positive_program_user_agent
old_patch_routes=mod._patch_routes
old_provider_recipes=mod._provider_request_recipes
old_peer_routes=mod._peer_routes
old_peer_recipes=mod._peer_request_recipes
old_focus=mod._census_runtime_focus
old_network=mod._runtime_network_hints
try:
    mod.positive_program_routes=lambda provider_id:["/search.php?q={query}","/api/file/{id}"] if provider_id=="demo" else []
    mod.positive_program_request_recipes=lambda provider_id:[positive_recipe] if provider_id=="demo" else []
    mod.positive_program_user_agent=lambda provider_id:"Validated-UA/1.0" if provider_id=="demo" else ""
    mod._patch_routes=lambda patch:["/legacy-search?q={query}","/legacy-player/{id}"]
    mod._provider_request_recipes=lambda provider_id:[legacy_recipe]
    mod._peer_routes=lambda strategy:["/peer-search?q={query}","/peer-player/{id}"]
    mod._peer_request_recipes=lambda strategy:[{
        **legacy_recipe,
        "route":"/peer-search?q={query}",
        "source":"peer-experience",
    }]
    mod._census_runtime_focus=lambda provider_id:{"status":"ROUTE PROVEN","focus":"route-traversal","max_pages":10,"max_embeds":10,"max_depth":3}
    mod._runtime_network_hints=lambda patch:{"bases":[],"user_agent":"Fallback-UA/1.0","blocked_hosts":[],"blocked_paths":[]}

    config={
        "provider_patches":{
            "demo":{
                "official_site":"https://demo.example",
                "published_types":["movie"],
            }
        },
        "provider_capabilities":{
            "demo":{
                "strategy":"html_search",
                "catalogue_types":["movie"],
                "observed_origins":[],
            }
        },
    }
    candidate={
        "canonical_id":"demo",
        "metadata":{"name":"Demo","baseUrl":"https://demo.example"},
        "brain_observed_request_recipes":[current_recipe],
        "brain_repair_plan":{
            "failureClass":"route_proven_gap",
            "experimentVariant":2,
            "experimentGeneration":1,
        },
    }
    options=mod._adaptive_runtime_options(candidate,config)
    assert isinstance(options,dict), options
    assert options["user_agent"]=="Validated-UA/1.0"
    assert options["search_paths"].index("/search.php?q={query}") < options["search_paths"].index("/legacy-search?q={query}")
    assert options["direct_paths"].index("/api/file/{id}") < options["direct_paths"].index("/legacy-player/{id}")

    recipes=options["request_recipes"]
    routes=[row["route"] for row in recipes]
    # Fresh current observation remains strongest, then validated provider-local
    # positive memory, then older provider experience, then peer transfer.
    assert routes.index("/fresh-search?q={query}") < routes.index("/search.php?q={query}")
    assert routes.index("/search.php?q={query}") < routes.index("/legacy-search?q={query}")
    assert routes.index("/legacy-search?q={query}") < routes.index("/peer-search?q={query}")
    counts=options["route_prior_counts"]
    assert counts["positiveProgramRoutes"]==2
    assert counts["positiveProgramRequestRecipes"]==1
    assert counts["positiveProgramUserAgent"] is True

    # A provider-scoped executable recipe is itself sufficient runtime origin
    # evidence. This covers providers such as Yflix whose durable experience
    # identifies an API origin even when no branded official_site is known.
    mod.positive_program_routes=lambda provider_id:[]
    mod.positive_program_request_recipes=lambda provider_id:[]
    mod.positive_program_user_agent=lambda provider_id:""
    mod._patch_routes=lambda patch:[]
    mod._provider_request_recipes=lambda provider_id:[{
        **legacy_recipe,
        "origin":"https://enc-dec.app",
        "route":"/db/flix/find?tmdb_id={tmdbId}&type=movie",
        "response":"json",
    }] if provider_id=="yflix" else []
    mod._peer_routes=lambda strategy:[]
    mod._peer_request_recipes=lambda strategy:[]
    yflix_config={
        "provider_patches":{"yflix":{"published_types":["movie","tv"]}},
        "provider_capabilities":{"yflix":{"strategy":"mixed_embed_resolver","catalogue_types":["movie","tv"],"observed_origins":[]}},
    }
    yflix_candidate={
        "canonical_id":"yflix",
        "metadata":{"name":"Yflix"},
        "brain_observed_request_recipes":[],
        "brain_repair_plan":{
            "failureClass":"route_proven_gap",
            "experimentVariant":0,
            "experimentGeneration":1,
        },
    }
    yflix_options=mod._adaptive_runtime_options(yflix_candidate,yflix_config)
    assert isinstance(yflix_options,dict), yflix_options
    assert yflix_options["base_url"]=="https://enc-dec.app"
    assert yflix_options["request_recipes"][0]["origin"]=="https://enc-dec.app"

    # Runtime sanitation happens before exploration, not only when accepted
    # programs are compiled for durable memory.
    google_noise={
        **legacy_recipe,
        "origin":"https://www.google.co.in",
        "route":"/search?q={query}",
    }
    assert mod._safe_request_recipe(google_noise,peer=False) is None
    assert mod._safe_route("/favicon.ico") is None
finally:
    mod.positive_program_routes=old_routes
    mod.positive_program_request_recipes=old_recipes
    mod.positive_program_user_agent=old_ua
    mod._patch_routes=old_patch_routes
    mod._provider_request_recipes=old_provider_recipes
    mod._peer_routes=old_peer_routes
    mod._peer_request_recipes=old_peer_recipes
    mod._census_runtime_focus=old_focus
    mod._runtime_network_hints=old_network

print("Brain positive-program runtime priority contract passed")
