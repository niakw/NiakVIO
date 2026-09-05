#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_provider_v3_routes_sequential import (  # noqa: E402
    _provider_contract_hosts,
    evaluate_provider,
    should_pass,
)

common = {
    "method": "GET",
    "status": 200,
    "content_type": "text/html",
    "header_names": ["accept"],
    "body_kind": "none",
    "body_fields": [],
}

# Regression 1: request identity must survive an HTTP redirect to a current
# provider terminal. Before the fix, only final_url was checked and this 200
# response was rejected because current.example was not yet canonical DATA.
redirect_model = {
    "canonicalSupportedTypes": ["anime"],
    "knownSite": "https://old.example",
    "routeData": [{"route": "/anime/{slug}", "type": "anime"}],
}
redirect_task = {
    "semantic_type": "anime",
    "fixture_slug": "jujutsu-kaisen-s01e01",
    "fixture": {
        "tmdbId": "95479",
        "mediaType": "anime",
        "title": "Jujutsu Kaisen",
        "season": 1,
        "episode": 1,
    },
    "status": "no_streams",
    "fetches": [{
        **common,
        "url": "https://old.example/anime/jujutsu-kaisen",
        "final_url": "https://current.example/anime/jujutsu-kaisen",
    }],
}
redirect_eval = evaluate_provider("redirect-regression", redirect_model, [redirect_task], 0.75)
assert redirect_eval["validatedTypes"] == ["anime"], redirect_eval
assert redirect_eval["missingTypes"] == [], redirect_eval
assert should_pass(redirect_eval) is True, redirect_eval

# Regression 2: officialHub is first-class provider authority. If another stale
# knownSite is also present, calls initiated on the hub must not be rejected.
hub_model = {
    "canonicalSupportedTypes": ["anime"],
    "knownSite": "https://stale.example",
    "officialHub": "https://hub.example",
    "routeData": [{"route": "/anime/{slug}", "type": "anime"}],
}
hosts = _provider_contract_hosts(hub_model)
assert "hub.example" in hosts, hosts
assert "stale.example" in hosts, hosts
hub_task = {
    **redirect_task,
    "fetches": [{
        **common,
        "url": "https://hub.example/anime/jujutsu-kaisen",
        "final_url": "https://current.example/anime/jujutsu-kaisen",
    }],
}
hub_eval = evaluate_provider("hub-regression", hub_model, [hub_task], 0.75)
assert hub_eval["validatedTypes"] == ["anime"], hub_eval
assert should_pass(hub_eval) is True, hub_eval

print("PROVIDER_V3_REDIRECT_HOST_GATE_TEST_OK request_identity=true official_hub=true")
