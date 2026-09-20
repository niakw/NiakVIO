#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "adaptive_runtime" / "runtime_repair.py"
spec = importlib.util.spec_from_file_location("terminal_source_runtime", SCRIPT)
assert spec and spec.loader
runtime = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runtime)

assert runtime._route_role("/file/{binding:id}") == "source"
assert runtime._route_role("/drive/{binding:slug}") == "source"
assert runtime._route_role("/download/{binding:id}") == "source"
assert runtime._route_role("/download-{slug}-movie-2026/") == "detail"
assert runtime._route_role("/player/{binding:id}") == "player"
assert runtime._route_role("/api/sources/{binding:id}") == "api"

config = {
    "provider_patches": {
        "demo": {
            "official_site": "https://demo.example",
            "candidate_learned_routes": [
                "/?s={query}",
                "/file/{binding:id}",
                "/drive/{binding:slug}",
                "/download-{slug}-movie-2026/",
                "/movie/{id}",
            ],
        }
    },
    "provider_capabilities": {
        "demo": {
            "strategy": "html_scraper",
            "catalogue_types": ["movie"],
        }
    },
}

for variant in (0, 4):
    candidate = {
        "canonical_id": "demo",
        "metadata": {
            "name": "Demo",
            "baseUrl": "https://demo.example",
            "supportedTypes": ["movie"],
        },
        "brain_repair_plan": {
            "failureClass": "media_extraction_gap",
            "experimentVariant": variant,
            "experimentGeneration": 2 if variant == 4 else 1,
        },
        "brain_observed_request_recipes": [],
    }
    options = runtime._adaptive_runtime_options(candidate, config)
    assert options is not None
    direct = options["direct_paths"]
    assert "/file/{binding:id}" in direct, (variant, direct)
    assert "/drive/{binding:slug}" in direct, (variant, direct)
    assert "/download-{slug}-movie-2026/" not in direct, (variant, direct)
    assert "/movie/{id}" not in direct, (variant, direct)
    assert options["search_paths"] == ["/?s={query}"], (variant, options["search_paths"])

prefs0 = runtime._experiment_role_preferences({}, "media_extraction_gap", 0)
assert prefs0.index("source") < prefs0.index("api"), prefs0

source = SCRIPT.read_text(encoding="utf-8")
assert 'TERMINAL_MEDIA_ROLES = {"player", "source", "api"}' in source
assert 'if _route_role(route) in TERMINAL_MEDIA_ROLES' in source

print("Brain terminal source-route preservation contract passed")
