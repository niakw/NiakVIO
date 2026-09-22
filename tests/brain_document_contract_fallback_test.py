#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLANNER = ROOT / "engine_v2/scripts/plan-repairs.mjs"
RUNTIME = ROOT / "scripts/adaptive_runtime/runtime_repair.py"

source = PLANNER.read_text(encoding="utf-8")

def profiles_for(failure: str) -> list[str]:
    match = re.search(
        rf"\n  {re.escape(failure)}: \[(.*?)\n  \],",
        source,
        flags=re.S,
    )
    assert match, failure
    return re.findall(r'profile: "([^"]+)"', match.group(1))

for failure in ("route_proven_gap", "candidate_replay_gap", "search_gap"):
    profiles = profiles_for(failure)
    assert profiles[-1] == "document_request_contract_mining_v1", (failure, profiles)
    assert profiles.count("document_request_contract_mining_v1") == 1, (failure, profiles)
    assert profiles.index("runtime_response_salvage_v1") < profiles.index("document_request_contract_mining_v1"), (failure, profiles)

spec = importlib.util.spec_from_file_location("runtime_document_fallback", RUNTIME)
assert spec and spec.loader
runtime = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runtime)

config = {
    "provider_patches": {
        "synthetic-doc": {
            "official_site": "https://provider.example",
            "documented_routes": ["/?s={query}", "/detail/{slug}", "/player/{id}"],
        }
    },
    "provider_capabilities": {
        "synthetic-doc": {
            "strategy": "html_scraper",
            "catalogue_types": ["movie"],
        }
    },
}

for failure, status in (
    ("route_proven_gap", "ROUTE PROVEN"),
    ("candidate_replay_gap", "CANDIDATE OK"),
    ("search_gap", "NO PROOF"),
):
    candidate = {
        "canonical_id": "synthetic-doc",
        "metadata": {
            "name": "Synthetic",
            "supportedTypes": ["movie"],
            "baseUrl": "https://provider.example",
        },
        "censusPrior": {"status": status},
        "brain_repair_plan": {
            "failureClass": failure,
            "experimentVariant": 4,
            "experimentGeneration": 5,
            "postExhaustionStrategyProfile": "document_request_contract_mining_v1",
            "postExhaustionStrategyMethod": "provider-document-request-contract-mining",
        },
    }
    options = runtime._adaptive_runtime_options(candidate, config)
    assert options is not None, failure
    assert options["new_strategy_id"] == "document_request_contract_mining_v1", (failure, options)
    assert options["document_request_mining"] is True, (failure, options)

print("Brain document-contract fallback test passed")
