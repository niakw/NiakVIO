#!/usr/bin/env python3
"""Restore Purstream's proof-backed terminal API without using its hub at runtime.

Live proof 2026-09-11:
- GET https://api.purstream.ad/api/v1/search-bar/search/Interstellar -> provider id 2466
- GET https://api.purstream.ad/api/v1/stream/2466 -> direct HLS
- GET https://api.purstream.ad/api/v1/search-bar/search/Breaking%20Bad -> provider id 3852
- GET https://api.purstream.ad/api/v1/stream/3852/episode?season=1&episode=1 -> direct HLS

The hub remains discovery authority only. It is not an executable runtime backend.
Route proof v5 is persisted alongside recipe proof v5: materialization deliberately
filters recipes/routes whose top-level route proof authority is below v5.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OVERRIDES = ROOT / "provider-overrides.json"
KNOWLEDGE = ROOT / "automation" / "provider-v3-static-knowledge.json"

SITE = "https://purstream.ad"
API = "https://api.purstream.ad/api/v1"
HUB = "https://purstream.wiki"
PROOF_VERSION = 5
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36"

RECIPE = {
    "proofModelVersion": PROOF_VERSION,
    "allowGenericFallback": False,
    "base": API,
    "referer": SITE + "/",
    "searchRoute": "/search-bar/search/{query}",
    "movieRoute": "/stream/{id}",
    "episodeRoute": "/stream/{id}/episode?season={season}&episode={episode}",
    "idFields": ["id"],
    "titleFields": ["title"],
    "yearFields": ["release_date"],
    "sourceFields": ["stream_url", "url"],
    "strictIdentity": True,
    "directSourcesOnly": True,
    "requestTimeoutMs": 5000,
    "requestHeaders": {
        "User-Agent": UA,
        "Accept": "application/json,text/plain,*/*",
        "Origin": SITE,
        "Referer": SITE + "/",
    },
}


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"{path}: object required")
    return value


def write(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    overrides = load(OVERRIDES)
    patches = overrides.setdefault("provider_patches", {})
    patch = patches.setdefault("purstream", {})
    patch["official_hub"] = HUB
    patch["official_site"] = SITE
    patch["official_api"] = API
    patch["fixed_endpoint"] = {
        "resolver_function": "detectPurstreamDomain",
        "api": API,
        "referer": SITE + "/",
    }
    patch["manifest_overrides"] = dict(patch.get("manifest_overrides") or {}, enabled=True)

    site_aliases = ["purstream.art", "purstream.club", "purstream.id", "purstream.wiki"]
    api_aliases = ["api.purstream.art", "api.purstream.club", "api.purstream.id", "api.purstream.wiki"]
    patch["domain_substitutions"] = {
        **{host: "purstream.ad" for host in site_aliases},
        **{host: "api.purstream.ad" for host in api_aliases},
    }
    patch["replacements"] = copy.deepcopy(patch["domain_substitutions"])
    patch["runtime_domain_replacements"] = copy.deepcopy(patch["domain_substitutions"])

    # Route authority and recipe authority are a pair. provider_model() will not
    # publish either learned routes or apiRecipe unless routeProofVersion >= 5,
    # even when the recipe itself carries proofModelVersion=5.
    patch["route_proof_version"] = max(int(patch.get("route_proof_version") or 0), PROOF_VERSION)
    patch["api_recipe"] = copy.deepcopy(RECIPE)
    patch["candidate_api_recipe"] = copy.deepcopy(RECIPE)
    patch["learned_routes"] = [
        "/search-bar/search/{query}",
        "/stream/{id}",
        "/stream/{id}/episode?season={season}&episode={episode}",
    ]
    patch["candidate_learned_routes"] = list(patch["learned_routes"])
    patch["proof_search_bases"] = [API]
    patch["proof_detail_bases"] = [API]
    patch["proof_protected_hosts"] = ["api.purstream.ad"]
    patch["identity_input"] = {
        "mode": "catalog_search",
        "requires_tmdb_before_run": True,
        "required_fields": ["title", "mediaType"],
    }
    patches["purstream"] = patch
    overrides["provider_patches"] = patches
    write(OVERRIDES, overrides)

    knowledge = load(KNOWLEDGE)
    providers = knowledge.setdefault("providers", {})
    row = providers.setdefault("purstream", {})
    model = row.get("model") if isinstance(row.get("model"), dict) else {}
    model["knownSite"] = SITE
    model["officialSite"] = SITE
    model["officialHub"] = HUB
    model["officialApi"] = API
    model["fixedApi"] = API
    model["routeProofVersion"] = max(int(model.get("routeProofVersion") or 0), PROOF_VERSION)
    model["apiRecipe"] = copy.deepcopy(RECIPE)
    model["candidateApiRecipe"] = copy.deepcopy(RECIPE)
    model["routes"] = list(patch["learned_routes"])
    model["candidateRoutes"] = list(patch["candidate_learned_routes"])
    model["proofSearchBases"] = [API]
    model["proofDetailBases"] = [API]
    model["proofProtectedHosts"] = ["api.purstream.ad"]
    row["model"] = model
    providers["purstream"] = row
    knowledge["providers"] = providers
    write(KNOWLEDGE, knowledge)

    print(
        "PURSTREAM_LIVE_API_V1 "
        f"site=purstream.ad api=api.purstream.ad/api/v1 hub_runtime=false "
        f"route_proof={PROOF_VERSION} recipe_proof={RECIPE['proofModelVersion']} "
        "movie=stream/{id} tv=stream/{id}/episode"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
