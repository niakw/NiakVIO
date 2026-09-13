#!/usr/bin/env python3
"""Restore PlayIMDb's already-proven typed resolver authority.

This migration does not discover a new route. It promotes the proof-v5 recipe that
NiakVIO already retains in candidate structured DATA back into the active execution
authority after an older reconciliation reduced ``learned_routes`` to the movie
route + bare ``/api.php`` and left ``api_recipe`` absent.

The restored recipe is the historical NiakVIO contract that previously proved both
movie and TV lanes: TMDB-direct vaplayer resolver, explicit season/episode for TV,
and nextgencloudfabric playback/request context.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OVERRIDES = ROOT / "provider-overrides.json"
PROVIDER_ID = "playimdb"

MOVIE_ROUTE = "https://streamdata.vaplayer.ru/api.php?tmdb={tmdbId}&type=movie"
EPISODE_ROUTE = (
    "https://streamdata.vaplayer.ru/api.php?tmdb={tmdbId}&type=tv"
    "&season={season}&episode={episode}"
)
LEARNED_ROUTES = [
    "/api.php?tmdb={tmdbId}&type=movie",
    "/api.php?tmdb={tmdbId}&type=tv&season={season}&episode={episode}",
]
REQUIRED_HEADER_VALUES = {
    "origin": "https://nextgencloudfabric.com",
    "referer": "https://nextgencloudfabric.com/",
}


def load() -> dict[str, Any]:
    value = json.loads(OVERRIDES.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("provider-overrides.json must contain an object")
    return value


def _validate_request(name: str, request: object) -> None:
    if not isinstance(request, dict):
        raise ValueError(f"playimdb {name} request missing")
    if str(request.get("method") or "").upper() != "GET":
        raise ValueError(f"playimdb {name} must use GET")
    headers = request.get("headers")
    if not isinstance(headers, dict):
        raise ValueError(f"playimdb {name} headers missing")
    lowered = {str(key).lower(): str(value) for key, value in headers.items()}
    for key, expected in REQUIRED_HEADER_VALUES.items():
        if lowered.get(key) != expected:
            raise ValueError(f"playimdb {name} {key} drift: {lowered.get(key)!r}")
    if not lowered.get("user-agent"):
        raise ValueError(f"playimdb {name} user-agent missing")


def validate_patch(patch: dict[str, Any]) -> None:
    if int(patch.get("route_proof_version") or 0) < 5:
        raise ValueError("playimdb requires proof-v5 authority")
    recipe = patch.get("api_recipe")
    if not isinstance(recipe, dict):
        raise ValueError("playimdb active api_recipe missing")
    if int(recipe.get("proofModelVersion") or 0) < 5:
        raise ValueError("playimdb active recipe is not proof-v5")
    if recipe.get("recipeKind") != "typed-resolver-api":
        raise ValueError("playimdb active recipe must be typed-resolver-api")
    if recipe.get("allowGenericFallback") is not False:
        raise ValueError("playimdb generic fallback must remain disabled")
    if recipe.get("movieRoute") != MOVIE_ROUTE:
        raise ValueError("playimdb movie route drift")
    if recipe.get("episodeRoute") != EPISODE_ROUTE:
        raise ValueError("playimdb episode route drift")
    _validate_request("movie", recipe.get("movieRequest"))
    _validate_request("episode", recipe.get("episodeRequest"))
    routes = [str(value) for value in patch.get("learned_routes") or []]
    if routes != LEARNED_ROUTES:
        raise ValueError(f"playimdb active learned routes drift: {routes!r}")
    identity = patch.get("identity_input")
    if not isinstance(identity, dict) or identity.get("mode") != "tmdb_direct":
        raise ValueError("playimdb identity must remain tmdb_direct")


def migrate(data: dict[str, Any]) -> bool:
    patches = data.get("provider_patches")
    if not isinstance(patches, dict):
        raise ValueError("provider_patches missing")
    patch = patches.get(PROVIDER_ID)
    if not isinstance(patch, dict):
        raise ValueError("playimdb patch missing")

    candidate = patch.get("candidate_api_recipe")
    if not isinstance(candidate, dict):
        raise ValueError("playimdb candidate proof-v5 recipe missing")
    candidate = copy.deepcopy(candidate)
    if int(candidate.get("proofModelVersion") or 0) < 5:
        raise ValueError("playimdb candidate recipe is not proof-v5")

    # The historical accepted recipe was explicitly typed. Restoring this marker is
    # material: ProviderBase permits the terminal TMDB resolver to execute directly
    # only for this proof-backed family.
    candidate["recipeKind"] = "typed-resolver-api"
    candidate["allowGenericFallback"] = False
    candidate["movieRoute"] = MOVIE_ROUTE
    candidate["episodeRoute"] = EPISODE_ROUTE

    changed = False
    if patch.get("candidate_api_recipe") != candidate:
        patch["candidate_api_recipe"] = copy.deepcopy(candidate)
        changed = True
    if patch.get("api_recipe") != candidate:
        patch["api_recipe"] = copy.deepcopy(candidate)
        changed = True
    if patch.get("learned_routes") != LEARNED_ROUTES:
        patch["learned_routes"] = list(LEARNED_ROUTES)
        changed = True

    identity = patch.get("identity_input")
    expected_identity = {
        "mode": "tmdb_direct",
        "requires_tmdb_before_run": False,
        "required_fields": ["tmdbId", "mediaType"],
    }
    if identity != expected_identity:
        patch["identity_input"] = expected_identity
        changed = True

    validate_patch(patch)
    return changed


def main() -> int:
    data = load()
    changed = migrate(data)
    if changed:
        OVERRIDES.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    print(
        "FIELD_PLAYIMDB_PROOF_V5_AUTHORITY "
        f"changed={str(changed).lower()} recipe_kind=typed-resolver-api lanes=movie,tv"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
