#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "adaptive_runtime"))
sys.path.insert(1, str(ROOT / "scripts"))

import runtime_repair  # noqa: E402


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


config = {
    "provider_patches": {
        "demo": {
            "official_site": "https://primary.example",
            "published_types": ["movie"],
            "learned_routes": [
                "/search?q={query}",
                "/detail/{slug}",
                "/player/{id}",
            ],
        }
    },
    "provider_capabilities": {
        "demo": {
            "strategy": "html_scraper",
            "observed_origins": [
                "https://alt-one.example",
                "https://alt-two.example",
            ],
            "catalogue_types": ["movie"],
        }
    },
}

experience = {
    "providers": {
        "demo": {
            "requestRecipes": [
                {
                    "route": "/api/owned?q={query}",
                    "role": "search",
                    "method": "GET",
                    "bodyKind": "none",
                    "headerNames": ["accept"],
                    "response": "json",
                    "executable": True,
                }
            ]
        }
    },
    "strategyPatterns": {
        "html_scraper": {
            "commonRouteTemplates": [
                {"route": "/peer-search?q={query}", "providerSupport": 2},
                {"route": "/player/{id}", "providerSupport": 2},
            ],
            "commonRequestRecipes": [
                {
                    "route": "/api/peer?q={query}",
                    "role": "search",
                    "method": "GET",
                    "bodyKind": "none",
                    "headerNames": ["accept"],
                    "response": "json",
                    "executable": True,
                    "providerSupport": 2,
                }
            ],
        }
    },
}


def candidate(failure: str, generation: int) -> dict:
    return {
        "canonical_id": "demo",
        "metadata": {
            "name": "Demo",
            "baseUrl": "https://primary.example",
            "supportedTypes": ["movie"],
        },
        "brain_repair_plan": {
            "failureClass": failure,
            "experimentVariant": 4,
            "experimentGeneration": generation,
            "negativeMemoryMatches": generation,
        },
        "brain_observed_request_recipes": [],
    }


with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    census = td / "census.json"
    memory = td / "experience.json"
    census.write_text(json.dumps({"providers": []}), encoding="utf-8")
    memory.write_text(json.dumps(experience), encoding="utf-8")
    old_census, old_experience = runtime_repair.CENSUS_STATUS_PATH, runtime_repair.EXPERIENCE_PATH
    runtime_repair.CENSUS_STATUS_PATH, runtime_repair.EXPERIENCE_PATH = census, memory
    try:
        g2 = runtime_repair._adaptive_runtime_options(candidate("candidate_replay_gap", 2), config)
        g3 = runtime_repair._adaptive_runtime_options(candidate("candidate_replay_gap", 3), config)
        g4 = runtime_repair._adaptive_runtime_options(candidate("candidate_replay_gap", 4), config)
        g5 = runtime_repair._adaptive_runtime_options(candidate("candidate_replay_gap", 5), config)
        assert g2 and g3 and g4 and g5

        assert g2["experiment_generation"] == 2
        assert g2["new_strategy_id"] == "retained_candidate_replay_v1"
        assert g2["max_recipe_passes"] == 3
        assert not any(row.get("source") == "peer-experience" for row in g2["request_recipes"])

        assert g3["experiment_generation"] == 3
        assert g3["new_strategy_id"] == "retained_candidate_replay_v1_g3"
        assert g3["max_recipe_passes"] == 4
        assert g3["max_depth"] >= 5 and g3["max_pages"] >= 28 and g3["max_embeds"] >= 28
        assert any(row.get("source") == "peer-experience" for row in g3["request_recipes"])
        assert "/peer-search?q={query}" in g3["search_paths"]

        assert g4["new_strategy_id"] == "retained_candidate_replay_v1_g4"
        assert g4["max_recipe_passes"] == 5
        assert "/api/sources/{id}" in g4["direct_paths"]

        assert g5["new_strategy_id"] == "retained_candidate_replay_v1_g5"
        assert g5["max_recipe_passes"] == 6
        assert g5["max_depth"] >= 6 and g5["max_pages"] >= 36 and g5["max_embeds"] >= 36
        assert "/api/search?q={query}" in g5["search_paths"]
        assert "/movie/{id}" in g5["direct_paths"]

        transport2 = runtime_repair._adaptive_runtime_options(candidate("provider_transport_gap", 2), config)
        transport3 = runtime_repair._adaptive_runtime_options(candidate("provider_transport_gap", 3), config)
        assert transport2 and transport3
        assert transport2["base_url"] == "https://alt-one.example"
        assert transport3["base_url"] == "https://alt-two.example"
    finally:
        runtime_repair.CENSUS_STATUS_PATH, runtime_repair.EXPERIENCE_PATH = old_census, old_experience


generator = load(
    "brain_generation_runtime_generator",
    ROOT / "scripts" / "adaptive_runtime" / "runtime_recovery_generator.py",
)
generated = generator.apply(
    "module.exports={getStreams:async function(){return []}};\n",
    options={
        "provider_name": "Demo",
        "base_url": "https://primary.example",
        "types": ["movie"],
        "experiment_variant": 4,
        "experiment_generation": 3,
        "new_strategy_id": "retained_candidate_replay_v1_g3",
        "max_recipe_passes": 4,
        "max_pages": 28,
        "max_embeds": 28,
        "max_depth": 5,
    },
)
assert '"experimentVariant":4' in generated
assert '"experimentGeneration":3' in generated
assert '"newStrategyId":"retained_candidate_replay_v1_g3"' in generated
assert '"maxRecipePasses":4' in generated
assert '"maxPages":28' in generated
assert '"maxEmbeds":28' in generated
assert '"maxDepth":5' in generated
assert "pass<c.maxRecipePasses" in generated

print("Brain Learning generation-aware adaptive runtime contract passed")
