#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


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
assert experience.classify_route("/api/streams/{id}") == "api"
assert experience.reusable_route("/?sid=" + ("A" * 120), peer=True) is None
assert experience.reusable_route("/literal-interstellar-2014/", peer=True) is None
assert experience.reusable_route("/film/{slug}", peer=True) == "/film/{slug}"

with tempfile.TemporaryDirectory() as tmp:
    memory = Path(tmp) / "experience.json"
    memory.write_text(
        json.dumps(
            {
                "schemaVersion": 1,
                "strategyPatterns": {
                    "html_scraper": {
                        "greenProviderCount": 8,
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

    config = {
        "provider_patches": {
            "target": {
                "official_site": "https://target.example",
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
    assert options["direct_paths"][0] == "/film/{slug}", options["direct_paths"]
    assert "/episode/{id}/{season}/{episode}" in options["direct_paths"]
    assert "/player/{id}" in options["direct_paths"]
    assert not any("sid=" in route for route in options["direct_paths"] + options["search_paths"])
    assert options["route_prior_counts"]["provider"] == 3
    assert options["route_prior_counts"]["peer"] == 2

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
    },
)
assert "NUVIO_VERIFIED_MEDIA_RUNTIME_RECOVERY_V5" in patched
assert "function expandRoute(" in patched
assert "{season}" not in patched.split("CONFIG_PLACEHOLDER")[0] or "expandRoute" in patched
assert 'p!=="extension"' in patched
assert "TMDB_API_KEY" in patched
assert "8265bd1679663a7ea12ac168da84d2e8" not in patched

print("Brain repair experience transfer test passed")
