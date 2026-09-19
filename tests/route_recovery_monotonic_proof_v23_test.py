#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
RECOVERY_PATH = ROOT / "scripts" / "recover_provider_routes_from_upstreams.py"
spec = importlib.util.spec_from_file_location("recover_provider_routes_from_upstreams_v23_test", RECOVERY_PATH)
assert spec is not None and spec.loader is not None
recovery = importlib.util.module_from_spec(spec)
spec.loader.exec_module(recovery)

OLD_RECIPE = {
    "proofModelVersion": 5,
    "base": "https://api.live.example/api/v1",
    "searchRoute": "/search/{query}",
    "movieRoute": "/stream/{id}",
    "episodeRoute": "/stream/{id}/episode?season={season}&episode={episode}",
}
NEW_RECIPE = {
    "proofModelVersion": 5,
    "base": "https://api.new.example/v2",
    "searchRoute": "/find/{query}",
    "movieRoute": "/movie/{id}",
    "episodeRoute": "/show/{id}/{season}/{episode}",
}


def write(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def base_state(*, executable: bool = True) -> tuple[dict, dict]:
    patch = {
        "candidate_learned_routes": ["/candidate/{id}"],
        "learned_routes": ["/search/{query}", "/stream/{id}", "/stream/{id}/episode?season={season}&episode={episode}"],
        "proof_search_bases": ["https://api.live.example/api/v1"],
        "proof_detail_bases": ["https://api.live.example/api/v1"],
        "proof_protected_hosts": ["api.live.example"],
        "route_proof": {"version": 5, "authority": "live-proof"},
        "route_proof_version": 5 if executable else 0,
    }
    model = {
        "candidateRoutes": ["/candidate/{id}"],
        "routes": list(patch["learned_routes"]),
        "proofSearchBases": list(patch["proof_search_bases"]),
        "proofDetailBases": list(patch["proof_detail_bases"]),
        "proofProtectedHosts": list(patch["proof_protected_hosts"]),
        "routeProof": copy.deepcopy(patch["route_proof"]),
        "routeProofVersion": 5 if executable else 0,
    }
    if executable:
        patch["api_recipe"] = copy.deepcopy(OLD_RECIPE)
        model["apiRecipe"] = copy.deepcopy(OLD_RECIPE)
    else:
        patch["candidate_api_recipe"] = copy.deepcopy(OLD_RECIPE)
        model["candidateApiRecipe"] = copy.deepcopy(OLD_RECIPE)
    return patch, model


def run_case(patch: dict, model: dict, recovered: dict) -> tuple[dict, dict]:
    with tempfile.TemporaryDirectory(prefix="niakvio-v23-test-") as tmp:
        root = Path(tmp)
        overrides = root / "provider-overrides.json"
        knowledge = root / "provider-v3-static-knowledge.json"
        write(overrides, {"provider_patches": {"proof-test": copy.deepcopy(patch)}})
        write(knowledge, {"providers": {"proof-test": {"model": copy.deepcopy(model)}}})
        old_overrides, old_knowledge = recovery.OVERRIDES, recovery.KNOWLEDGE
        try:
            recovery.OVERRIDES = overrides
            recovery.KNOWLEDGE = knowledge
            report = {
                "schemaVersion": recovery.PROOF_VERSION,
                "providerCount": 1,
                "providers": [dict({"providerId": "proof-test"}, **recovered)],
            }
            recovery.apply_recovery(report)
        finally:
            recovery.OVERRIDES, recovery.KNOWLEDGE = old_overrides, old_knowledge
        out_patch = read(overrides)["provider_patches"]["proof-test"]
        out_model = read(knowledge)["providers"]["proof-test"]["model"]
        return out_patch, out_model


# 1) A zero current probe cannot delete an independently proof-v5 authority.
patch, model = base_state(executable=True)
out_patch, out_model = run_case(
    patch,
    model,
    {
        "status": "no-proven-route",
        "source": {"repo": "upstream", "sha": "new-zero-sha"},
        "routes": [],
        "executionRoutes": [],
        "routeData": [],
        "tasks": [],
    },
)
assert out_patch.get("api_recipe") == OLD_RECIPE, out_patch.get("api_recipe")
assert out_model.get("apiRecipe") == OLD_RECIPE, out_model.get("apiRecipe")
assert out_patch.get("proof_search_bases") == ["https://api.live.example/api/v1"]
assert out_patch.get("proof_detail_bases") == ["https://api.live.example/api/v1"]
assert out_patch.get("proof_protected_hosts") == ["api.live.example"]
assert out_patch.get("route_proof", {}).get("executionAuthorityPreserved") is True
assert out_patch.get("route_proof", {}).get("lastRepairProbe", {}).get("positiveExecutionEvidence") is False

# 2) Candidate-only knowledge is NOT an execution authority and remains fail-closed.
patch, model = base_state(executable=False)
out_patch, out_model = run_case(
    patch,
    model,
    {
        "status": "no-proven-route",
        "source": {"repo": "upstream", "sha": "zero-sha"},
        "routes": [],
        "executionRoutes": [],
        "routeData": [],
        "tasks": [],
    },
)
assert "api_recipe" not in out_patch
assert "apiRecipe" not in out_model

# 3) Fresh positive proof still replaces the old authority.
patch, model = base_state(executable=True)
out_patch, out_model = run_case(
    patch,
    model,
    {
        "status": "proven",
        "source": {"repo": "upstream", "sha": "positive-sha"},
        "routes": ["/find/{query}", "/movie/{id}", "/show/{id}/{season}/{episode}"],
        "executionRoutes": ["/find/{query}", "/movie/{id}", "/show/{id}/{season}/{episode}"],
        "routeData": [],
        "apiRecipe": copy.deepcopy(NEW_RECIPE),
        "tasks": [],
    },
)
assert out_patch.get("api_recipe") == NEW_RECIPE, out_patch.get("api_recipe")
assert out_model.get("apiRecipe") == NEW_RECIPE, out_model.get("apiRecipe")
assert out_patch.get("route_proof", {}).get("executionAuthorityPreserved") is not True

print("route recovery monotonic proof v23 tests passed")
