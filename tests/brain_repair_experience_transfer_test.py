#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


experience = load_module(
    "brain_repair_experience",
    ROOT / "scripts" / "build_brain_repair_experience.py",
)
runtime = load_module(
    "adaptive_runtime_repair",
    ROOT / "scripts" / "adaptive_runtime" / "runtime_repair.py",
)
v5 = load_module(
    "adaptive_runtime_recovery_v5_test",
    ROOT / "scripts" / "provider_patches" / "adaptive_runtime_recovery_v5.py",
)

assert experience.classify_route("/search?q={query}") == "search"
assert experience.classify_route("/film/{slug}") == "detail"
assert experience.classify_route("/episode/{id}/{season}/{episode}") == "episode"
assert experience.classify_route("/player/{id}") == "player"
assert experience.classify_route("/file/{binding:id}") == "source"
assert experience.classify_route("/drive/{binding:slug}") == "source"
assert experience.reusable_route("/file/{binding:id}", peer=True) == "/file/{binding:id}"
assert experience.classify_route("/api/streams/{id}") == "api"
assert experience.reusable_route("/?sid=" + ("A" * 120), peer=True) is None
assert experience.reusable_route("/literal-interstellar-2014/", peer=True) is None
assert experience.reusable_route("/film/{slug}", peer=True) == "/film/{slug}"
assert runtime._ROUTE_PLACEHOLDER.search("/film/{slug}") is not None
assert runtime._REQUEST_PLACEHOLDER.search("{query}") is not None

with tempfile.TemporaryDirectory() as tmp:
    memory = Path(tmp) / "experience.json"
    memory.write_text(
        json.dumps(
            {
                "schemaVersion": 2,
                "providers": {
                    "target": {
                        "requestRecipes": [
                            {
                                "route": "/engine/ajax/search.php",
                                "origin": "https://target.example",
                                "role": "search",
                                "method": "POST",
                                "bodyKind": "form",
                                "body": {"query": "{query}", "page": "1"},
                                "headerNames": ["accept", "content-type", "referer", "user-agent"],
                                "response": "json",
                                "semanticType": "movie",
                                "streamProof": True,
                                "executable": True
                            }
                        ]
                    }
                },
                "strategyPatterns": {
                    "html_scraper": {
                        "greenProviderCount": 8,
                        "commonRequestRecipes": [
                            {
                                "route": "/template-php/defaut/fetch.php",
                                "role": "search",
                                "method": "POST",
                                "bodyKind": "form",
                                "body": {"query": "{query}"},
                                "headerNames": ["accept", "content-type"],
                                "response": "html-or-text",
                                "semanticType": "",
                                "streamProof": True,
                                "executable": True,
                                "providerSupport": 3
                            }
                        ],
                        "commonRouteTemplates": [
                            {
                                "route": "/?s={query}",
                                "role": "search",
                                "providerSupport": 5,
                            },
                            {
                                "route": "/player/{id}",
                                "role": "player",
                                "providerSupport": 3,
                            },
                            {
                                "route": "/single-fixture-path/",
                                "role": "other",
                                "providerSupport": 1,
                            },
                        ],
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    runtime.EXPERIENCE_PATH = memory
    census = Path(tmp) / "census.json"
    census.write_text(
        json.dumps(
            {
                "providers": [
                    {
                        "provider": "target",
                        "status": "CHAIN REACHED",
                        "dominantIssue": "provider_network_zero_result",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    runtime.CENSUS_STATUS_PATH = census

    config = {
        "provider_patches": {
            "target": {
                "official_site": "https://target.example",
                "provider_lego_options": {
                    "scripts/provider_patches/synthetic_runtime.py": {
                        "base": "https://api.target.example",
                        "fallbackBases": ["https://mirror.target.example"],
                        "user_agent": "NiakVIO-Brain-Test/1.0",
                    }
                },
                "core_options": {
                    "stream_sanitizer": {
                        "blocked_hosts": ["bad-player.example"],
                        "blocked_path_patterns": ["/ads/"],
                    }
                },
                "candidate_learned_routes": [
                    "/search?q={query}",
                    "/film/{slug}",
                    "/episode/{id}/{season}/{episode}",
                    "/?sid=" + ("A" * 120),
                ],
            }
        },
        "provider_capabilities": {
            "target": {
                "strategy": "html_scraper",
                "catalogue_types": ["movie", "tv"],
            }
        },
    }
    candidate = {
        "canonical_id": "target",
        "metadata": {
            "name": "Target",
            "supportedTypes": ["movie", "tv"],
        },
    }
    options = runtime._adaptive_runtime_options(candidate, config)
    assert options is not None
    assert options["base_url"] == "https://target.example"
    assert options["search_paths"][0] == "/search?q={query}", options["search_paths"]
    assert "/?s={query}" in options["search_paths"]
    assert "/film/{slug}" in options["direct_paths"]
    assert "/episode/{id}/{season}/{episode}" in options["direct_paths"]
    assert not any("sid=" in route for route in options["direct_paths"] + options["search_paths"])
    assert options["route_prior_counts"]["provider"] == 3
    assert options["route_prior_counts"]["peer"] == 0
    assert options["route_prior_counts"]["requestRecipes"] == 1, options
    assert options["route_prior_counts"]["providerRequestRecipes"] == 1, options
    assert options["route_prior_counts"]["peerRequestRecipes"] == 1, options
    assert options["request_recipes"][0]["method"] == "POST"
    assert options["request_recipes"][0]["body"] == {"query": "{query}", "page": "1"}
    # Variant 0 consumes provider-local request evidence only. Peer request
    # recipes are reserved for later exploratory variants.
    assert len(options["request_recipes"]) == 1
    assert options["user_agent"] == "NiakVIO-Brain-Test/1.0"
    endpoint_hosts = {
        (urlparse(value).hostname or "").casefold()
        for value in options["endpoint_origins"]
    }
    assert "api.target.example" in endpoint_hosts
    assert "mirror.target.example" in endpoint_hosts
    assert "bad-player.example" in options["blocked_hosts"]
    assert "/ads/" in options["blocked_path_patterns"]
    assert options["repair_focus"] == "terminal-chain"
    assert options["census_status"] == "CHAIN REACHED"
    assert options["max_depth"] == 4
    assert options["max_embeds"] == 20
    # Variant 0 is deliberately provider-owned evidence only. Strategy-peer
    # route shapes and request recipes are introduced by later variants.
    assert options["experiment_strategy"] == "owned-evidence"
    assert options["direct_paths"][0] == "/episode/{id}/{season}/{episode}", options["direct_paths"]
    assert "/player/{id}" not in options["direct_paths"]

    variant1 = dict(candidate)
    variant1["brain_repair_plan"] = {
        "failureClass": "chain_terminal_gap",
        "experimentVariant": 1,
        "negativeMemoryMatches": 1,
    }
    options1 = runtime._adaptive_runtime_options(variant1, config)
    assert options1 is not None
    assert options1["experiment_strategy"] == "route-shape-transfer"
    assert options1["route_prior_counts"]["peer"] == 2
    assert options1["route_prior_counts"]["requestRecipes"] == 1
    assert options1["direct_paths"][0] == "/player/{id}", options1["direct_paths"]

    variant2 = dict(candidate)
    variant2["brain_repair_plan"] = {
        "failureClass": "chain_terminal_gap",
        "experimentVariant": 2,
        "negativeMemoryMatches": 2,
    }
    options2 = runtime._adaptive_runtime_options(variant2, config)
    assert options2 is not None
    assert options2["experiment_strategy"] == "request-recipe-transfer"
    assert options2["route_prior_counts"]["peer"] == 2
    assert options2["route_prior_counts"]["requestRecipes"] == 2
    assert {row["source"] for row in options2["request_recipes"]} == {
        "provider-experience", "peer-experience"
    }

    transport1 = dict(candidate)
    transport1["brain_repair_plan"] = {
        "failureClass": "provider_transport_gap",
        "experimentVariant": 1,
        "negativeMemoryMatches": 1,
    }
    transport_options = runtime._adaptive_runtime_options(transport1, config)
    assert transport_options is not None
    assert transport_options["route_prior_counts"]["peer"] == 0
    assert runtime._route_role(transport_options["direct_paths"][0]) == "detail", transport_options["direct_paths"]
    assert "/player/{id}" not in transport_options["direct_paths"]

    candidate2 = dict(candidate)
    candidate2["brain_repair_plan"] = {
        "failureClass": "candidate_replay_gap",
        "experimentVariant": 2,
        "negativeMemoryMatches": 2,
    }
    candidate_options2 = runtime._adaptive_runtime_options(candidate2, config)
    assert candidate_options2 is not None
    assert candidate_options2["peer_route_min_variant"] == 3
    assert candidate_options2["peer_recipe_min_variant"] == 3
    assert candidate_options2["route_prior_counts"]["peer"] == 0
    assert candidate_options2["route_prior_counts"]["requestRecipes"] == 1

    candidate3 = dict(candidate)
    candidate3["brain_repair_plan"] = {
        "failureClass": "candidate_replay_gap",
        "experimentVariant": 3,
        "negativeMemoryMatches": 3,
    }
    candidate_options3 = runtime._adaptive_runtime_options(candidate3, config)
    assert candidate_options3 is not None
    assert candidate_options3["experiment_strategy"] == "expanded-discovery"
    assert candidate_options3["route_prior_counts"]["peer"] == 2
    assert candidate_options3["route_prior_counts"]["requestRecipes"] == 2
    assert "/api/stream/{id}" in candidate_options3["direct_paths"]

    chain4 = dict(candidate)
    chain4["brain_repair_plan"] = {
        "failureClass": "chain_terminal_gap",
        "experimentVariant": 4,
        "negativeMemoryMatches": 4,
    }
    chain_options4 = runtime._adaptive_runtime_options(chain4, config)
    assert chain_options4 is not None
    assert chain_options4["experiment_strategy"] == "learned-family-new-strategy"
    assert chain_options4["new_strategy_id"] == "chain_terminal_extractor_v1"
    assert chain_options4["max_pages"] == 24
    assert "/player/{id}" in chain_options4["direct_paths"]
    assert "/api/stream/{id}" in chain_options4["direct_paths"]

    route4 = dict(candidate)
    route4["brain_repair_plan"] = {
        "failureClass": "route_proven_gap",
        "experimentVariant": 4,
        "negativeMemoryMatches": 4,
    }
    route_options4 = runtime._adaptive_runtime_options(route4, config)
    assert route_options4 is not None
    assert route_options4["new_strategy_id"] == "proven_route_terminal_traversal_v1"
    assert "/?s={query}" not in route_options4["search_paths"], route_options4["search_paths"]
    assert "/player/{id}" in route_options4["direct_paths"]

    transport4 = dict(candidate)
    transport4["brain_repair_plan"] = {
        "failureClass": "provider_transport_gap",
        "experimentVariant": 4,
        "negativeMemoryMatches": 4,
    }
    transport_options4 = runtime._adaptive_runtime_options(transport4, config)
    assert transport_options4 is not None
    assert transport_options4["new_strategy_id"] == "provider_origin_failover_v1"
    assert transport_options4["base_url"] == "https://api.target.example", transport_options4
    transport_endpoint_hosts = {
        (urlparse(value).hostname or "").casefold()
        for value in transport_options4["endpoint_origins"]
    }
    assert "target.example" in transport_endpoint_hosts
    assert transport_options4["max_pages"] == 24

    replay4 = dict(candidate)
    replay4["brain_repair_plan"] = {
        "failureClass": "candidate_replay_gap",
        "experimentVariant": 4,
        "negativeMemoryMatches": 4,
    }
    replay_options4 = runtime._adaptive_runtime_options(replay4, config)
    assert replay_options4 is not None
    assert replay_options4["new_strategy_id"] == "retained_candidate_replay_v1"
    assert replay_options4["route_prior_counts"]["requestRecipes"] == 1
    assert {row["source"] for row in replay_options4["request_recipes"]} == {"provider-experience"}
    assert "/player/{id}" not in replay_options4["direct_paths"], replay_options4["direct_paths"]
    assert "/api/stream/{id}" not in replay_options4["direct_paths"], replay_options4["direct_paths"]

# Restored V5 must still generate the verified-media runtime and inherit the
# new contextual route expansion from V4. This proves the executable Brain path
# is no longer pointing at a deleted script.
patched = v5.apply(
    "var module={exports:{getStreams:async function(){return []}}};",
    options={
        "provider_name": "Synthetic",
        "base_url": "https://synthetic.example",
        "types": ["movie", "tv"],
        "search_paths": ["/search?q={query}"],
        "direct_paths": ["/episode/{id}/{season}/{episode}"],
        "user_agent": "NiakVIO-Brain-Test/1.0",
        "repair_focus": "terminal-chain",
        "census_status": "CHAIN REACHED",
        "experiment_variant": 4,
        "new_strategy_id": "chain_terminal_extractor_v1",
        "request_recipes": [
            {
                "route": "/engine/ajax/search.php",
                "origin": "https://synthetic.example",
                "role": "search",
                "method": "POST",
                "bodyKind": "form",
                "body": {"query": "{query}"},
                "headerNames": ["accept", "content-type", "referer"],
                "response": "html-or-text",
                "semanticType": "movie",
                "streamProof": True,
                "executable": True,
            }
        ],
    },
)
assert "NUVIO_VERIFIED_MEDIA_RUNTIME_RECOVERY_V5" in patched
assert "function expandRoute(" in patched
assert "{season}" not in patched.split("CONFIG_PLACEHOLDER")[0] or "expandRoute" in patched
assert 'p!=="extension"' in patched
assert "TMDB_API_KEY" in patched
assert '"userAgent":"NiakVIO-Brain-Test/1.0"' in patched
assert '"repairFocus":"terminal-chain"' in patched
assert '"censusStatus":"CHAIN REACHED"' in patched
assert '"experimentVariant":4' in patched
assert '"newStrategyId":"chain_terminal_extractor_v1"' in patched
assert '"requestRecipes":[{"route":"/engine/ajax/search.php"' in patched
assert "function requestRecipe(" in patched
assert "function recipeBody(" in patched
assert "function jsonUrls(" in patched
assert 'h["User-Agent"]=c.userAgent' in patched
assert "8265bd1679663a7ea12ac168da84d2e8" not in patched

print("Brain repair experience transfer test passed")
