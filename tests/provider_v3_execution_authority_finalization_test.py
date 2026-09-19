#!/usr/bin/env python3
from __future__ import annotations

import copy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from upgrade_provider_execution_authority_finalization_v1 import patch as patch_execution_authority  # noqa: E402

patch_execution_authority()

from validate_provider_v3_routes_sequential import evaluate_provider, finalize_provider  # noqa: E402
from reconstruct_provider_v3_sequential_live import credit_verified_playable_chains  # noqa: E402


def fetch(url: str, status: int = 200) -> dict[str, object]:
    return {
        "url": url,
        "final_url": url,
        "status": status,
        "method": "GET",
        "content_type": "text/html",
        "header_names": ["accept"],
        "body_kind": "none",
        "body_fields": [],
    }


provider_id = "animekai-shaped"
verified_route = "/filter?keyword={query}"
internal_routes = [
    "/links/list",
    "/ajax/links/list",
    "/ajax/episodes/list",
    "/episodes/list",
    "/ajax/anime/search",
]

candidate_rows = [
    {
        "route": route,
        "role": "api",
        "source": "live-capture",
        "validationState": "candidate-not-executed",
    }
    for route in internal_routes
] + [{
    "route": verified_route,
    "role": "search",
    "source": "provider-verified",
    "validationState": "candidate-not-executed",
}]

model = {
    "canonicalSupportedTypes": ["anime"],
    "knownSite": "https://animekai.test",
    "officialSite": "https://animekai.test",
    "origins": ["https://animekai.test"],
    "observedUrls": ["https://animekai.test/"],
    "routes": internal_routes + [verified_route],
    "routeData": copy.deepcopy(candidate_rows),
    "candidateRoutes": internal_routes + [verified_route],
    "candidateRouteData": copy.deepcopy(candidate_rows),
}

task = {
    "semantic_type": "anime",
    "fixture_slug": "jujutsu-kaisen-s01e01",
    "fixture": {
        "tmdbId": "95479",
        "mediaType": "anime",
        "title": "Jujutsu Kaisen",
        "season": 1,
        "episode": 1,
    },
    "status": "playable_verified",
    "fetches": [
        fetch("https://animekai.test/filter?keyword=Jujutsu%20Kaisen"),
        fetch("https://animekai.test/ajax/anime/search"),
        fetch("https://animekai.test/ajax/episodes/list"),
        fetch("https://animekai.test/episodes/list"),
        fetch("https://animekai.test/ajax/links/list"),
        fetch("https://animekai.test/links/list"),
    ],
}

evaluation = evaluate_provider(provider_id, copy.deepcopy(model), [task], 0.75)
evaluation = credit_verified_playable_chains(evaluation, [task])
assert evaluation["validatedTypes"] == ["anime"], evaluation
assert any(
    row.get("route") == verified_route and row.get("validationState") == "live-validated"
    for row in evaluation["candidateRouteData"]
), evaluation["candidateRouteData"]
assert any(
    row.get("route") in internal_routes and not row.get("liveDerived")
    for row in evaluation["candidateRouteData"]
), evaluation["candidateRouteData"]

knowledge = {
    "providers": {
        provider_id: {
            "model": copy.deepcopy(model),
            "knowledge": {"recognizedContract": {}},
        }
    }
}
overrides = {
    "provider_patches": {
        provider_id: {
            "route_proof_version": 5,
            "learned_routes": [verified_route],
        }
    }
}

finalize_provider(
    provider_id,
    {"provider_id": provider_id},
    knowledge,
    overrides,
    evaluation,
    "declared-types-qualified",
    [],
)

final_model = knowledge["providers"][provider_id]["model"]
patch = overrides["provider_patches"][provider_id]
assert final_model["routes"] == [verified_route], final_model["routes"]
assert [row.get("route") for row in final_model["routeData"]] == [verified_route], final_model["routeData"]
assert patch["learned_routes"] == [verified_route], patch
recognized = knowledge["providers"][provider_id]["knowledge"]["recognizedContract"]
assert any(
    row.get("route") in internal_routes
    for row in recognized["candidateRequests"]
), recognized["candidateRequests"]

print(
    "PROVIDER_V3_EXECUTION_AUTHORITY_FINALIZATION_TEST_OK "
    "candidate_proof_v5_route_preserved=1 stale_internal_candidate_rows=evidence-only"
)
