#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/adaptive_runtime/runtime_repair.py"
spec=importlib.util.spec_from_file_location("brain_archetype_matching",SCRIPT)
assert spec and spec.loader
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

experience={
    "providers":{
        "api-peer":{
            "operational":True,
            "strategy":"api_stream_resolver",
            "mediaTypes":["movie","tv"],
            "routeFamilies":["search","api"],
            "recipeRoles":["search","api"],
            "recipeMethods":["GET"],
            "recipeResponses":["json"],
            "peerRouteTemplates":["/api/search?q={query}","/api/movie/{tmdbId}"],
            "peerRequestRecipes":[{
                "route":"/api/search?q={query}",
                "role":"search","method":"GET","bodyKind":"none","body":{},
                "headerNames":["accept"],"response":"json","semanticType":"movie",
                "streamProof":False,"requiredBindings":[],"executable":True,
            }],
        },
        "html-peer":{
            "operational":True,
            "strategy":"html_scraper",
            "mediaTypes":["movie"],
            "routeFamilies":["search","detail"],
            "recipeRoles":["search","detail"],
            "recipeMethods":["GET"],
            "recipeResponses":["html-or-text"],
            "peerRouteTemplates":["/?s={query}","/film/{slug}"],
            "peerRequestRecipes":[{
                "route":"/?s={query}",
                "role":"search","method":"GET","bodyKind":"none","body":{},
                "headerNames":["accept"],"response":"html-or-text","semanticType":"movie",
                "streamProof":False,"requiredBindings":[],"executable":True,
            }],
        },
        "api-post-peer":{
            "operational":True,
            "strategy":"api_stream_resolver",
            "mediaTypes":["anime"],
            "routeFamilies":["search","api"],
            "recipeRoles":["search","api"],
            "recipeMethods":["POST"],
            "recipeResponses":["json"],
            "peerRouteTemplates":["/api/search","/api/source/{id}"],
            "peerRequestRecipes":[{
                "route":"/api/search",
                "role":"search","method":"POST","bodyKind":"form","body":{"q":"{query}"},
                "headerNames":["accept","content-type"],"response":"json","semanticType":"anime",
                "streamProof":False,"requiredBindings":[],"executable":True,
            }],
        },
    },
    "strategyPatterns":{},
    "historicalCases":[],
}
with tempfile.TemporaryDirectory() as directory:
    path=Path(directory)/"experience.json"
    path.write_text(json.dumps(experience),encoding="utf-8")
    old=mod.EXPERIENCE_PATH
    mod.EXPERIENCE_PATH=path
    try:
        peers=mod._nearest_archetype_peers(
            "new-provider",
            "api_stream_resolver",
            ["movie"],
            ["/api/search?q={query}","/api/movie/{tmdbId}"],
            [{
                "route":"/api/search?q={query}",
                "role":"search","method":"GET","response":"json",
            }],
            limit=3,
        )
        assert peers, peers
        assert peers[0]["providerId"]=="api-peer",peers
        assert all(row["strategy"]=="api_stream_resolver" for row in peers),peers
        assert "html-peer" not in [row["providerId"] for row in peers]
        assert peers[0]["score"] > peers[-1]["score"],peers
        assert "/api/movie/{tmdbId}" in peers[0]["routes"]
        assert peers[0]["requestRecipes"][0]["response"]=="json"

        # With almost no provider-local structure, strategy is still a bounded
        # fallback rather than provider-name matching.
        sparse=mod._nearest_archetype_peers(
            "brand-new",
            "html_scraper",
            ["movie"],
            [],
            [],
            limit=3,
        )
        assert sparse and sparse[0]["providerId"]=="html-peer",sparse
    finally:
        mod.EXPERIENCE_PATH=old

source=SCRIPT.read_text(encoding="utf-8")
assert "nearest_archetype_peers" in source
assert "nearestArchetypePeers" in source
assert "providerId" in source and "score" in source

print("Brain nearest green provider archetype matching contract passed")
