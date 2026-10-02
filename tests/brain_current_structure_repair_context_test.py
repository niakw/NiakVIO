#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


brain = load(ROOT / "scripts" / "brain_repair_runtime.py", "brain_current_structure")
runtime = load(ROOT / "scripts" / "adaptive_runtime" / "runtime_repair.py", "runtime_current_structure")

payload = {
    "schemaVersion": 1,
    "role": "provider-current-structure-evidence",
    "proofAuthority": False,
    "executionAuthority": False,
    "providers": {
        "demo": {
            "sourceKind": "current-page",
            "observedAt": "2026-10-02",
            "originHost": "demo.example",
            "routes": [
                {"path": "/wp-json/demo/v1/resolve", "method": "UNKNOWN", "role": "player-resolver"},
                {"path": "https://unsafe.example/no", "method": "GET"},
            ],
            "requestKeys": ["tmdb", "type", "year", "pid", "bad key"],
            "fanout": {
                "groupCount": 2,
                "groupVariantCounts": [10, 9],
                "indexedVariantCount": 19,
                "languageLabels": ["VF", "VOSTFR", "bad label"],
            },
        }
    },
}
observed = brain._current_structure_evidence("demo", payload)
assert observed["proofAuthority"] is False
assert observed["executionAuthority"] is False
assert observed["originHost"] == "demo.example"
assert observed["routes"] == [{
    "path": "/wp-json/demo/v1/resolve",
    "method": "UNKNOWN",
    "role": "player-resolver",
}]
assert observed["requestKeys"] == ["tmdb", "type", "year", "pid"]
assert observed["fanout"]["groupVariantCounts"] == [10, 9]
assert observed["fanout"]["indexedVariantCount"] == 19
assert observed["fanout"]["languageLabels"] == ["VF", "VOSTFR"]

candidate = {
    "canonical_id": "demo",
    "metadata": {"name": "Demo", "supportedTypes": ["movie"]},
    "brain_repair_plan": {
        "failureClass": "variant_coverage_gap",
        "experimentVariant": 4,
        "experimentGeneration": 2,
    },
    "brain_current_structure_evidence": observed,
}
config = {
    "provider_patches": {
        "demo": {
            "official_site": "https://old-demo.example",
            "published_types": ["movie"],
            "learned_routes": ["/old/{slug}"],
        }
    },
    "provider_capabilities": {
        "demo": {
            "strategy": "html_scraper",
            "catalogue_types": ["movie"],
            "observed_origins": ["https://old-demo.example"],
        }
    },
}
options = runtime._adaptive_runtime_options(candidate, config)
assert isinstance(options, dict), options
assert options["base_url"] == "https://demo.example", options
assert "/wp-json/demo/v1/resolve" in options["direct_paths"], options
assert options["route_prior_counts"]["currentStructureRoutes"] == 1, options
assert options["route_prior_counts"]["currentStructureVariantCount"] == 19, options
assert options["max_embeds"] >= 19, options
assert options["repair_focus"] == "variant-coverage", options

# The current structure is hypothesis input only. UNKNOWN must remain unknown:
# no executable request recipe is synthesized from request-key names.
assert observed["routes"][0]["method"] == "UNKNOWN"
assert not options["request_recipes"], options
assert options["route_prior_counts"]["currentContractProbes"] == 1, options
assert options["contract_probes"] == [{
    "origin": "https://demo.example",
    "route": "/wp-json/demo/v1/resolve",
    "role": "player-resolver",
    "requestKeys": ["tmdb", "type", "year", "pid"],
    "methodCandidates": ["POST", "GET"],
    "bodyKindCandidates": ["form", "json"],
    "proofAuthority": False,
    "executionAuthority": False,
    "executable": False,
    "source": "current-structure-observation",
}], options["contract_probes"]
assert "987" not in repr(options["contract_probes"])

print("canonical Brain current-structure Repair context contract passed")
