#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "restore_playimdb_proof_v5.py"
MATERIALIZER = ROOT / "scripts" / "materialize_provider_v3_all.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


restore = load_module("restore_playimdb_proof_v5", SCRIPT)
allmat = load_module("materialize_provider_v3_all_for_playimdb_test", MATERIALIZER)

overrides = json.loads((ROOT / "provider-overrides.json").read_text(encoding="utf-8"))
static = json.loads((ROOT / "automation/provider-v3-static-knowledge.json").read_text(encoding="utf-8"))
patches = overrides["provider_patches"]
capabilities = overrides["provider_capabilities"]

# Prove the migration itself recovers the exact active authority from the current
# pre-migration shape, rather than merely testing hand-written expected constants.
fixture = copy.deepcopy(overrides)
play = fixture["provider_patches"]["playimdb"]
play.pop("api_recipe", None)
play["learned_routes"] = ["/api.php?tmdb={id}&type={media}", "/api.php"]
assert restore.migrate(fixture) is True
assert restore.migrate(fixture) is False, "migration must be idempotent"
restore.validate_patch(fixture["provider_patches"]["playimdb"])

# Once committed, the real file must already be in the restored state.
restore.validate_patch(patches["playimdb"])
recipe = patches["playimdb"]["api_recipe"]
assert recipe["recipeKind"] == "typed-resolver-api"
assert recipe["movieRoute"] == restore.MOVIE_ROUTE
assert recipe["episodeRoute"] == restore.EPISODE_ROUTE

model = allmat.provider_model(
    "playimdb",
    patches["playimdb"],
    capabilities["playimdb"],
    static["providers"]["playimdb"],
)
assert model["apiRecipe"] == recipe, "active proof-v5 recipe must win materialization authority"
assert model["identityInput"] == {
    "mode": "tmdb_direct",
    "requiresTmdbBeforeRun": False,
    "requiredFields": ["tmdbId", "mediaType"],
}
assert model["routes"] == restore.LEARNED_ROUTES

print("PLAYIMDB_PROOF_V5_AUTHORITY_OK recipe=typed-resolver-api lanes=movie,tv")
