#!/usr/bin/env python3
"""Deterministic meta-gap strategy synthesis for NiakVIO Brain.

This layer never mutates provider/publication bytes. It converts current
repair debt plus negative experiment memory into one novel bounded advisor
experiment per provider. The ordinary Brain sandbox/current-byte/identity/
playback/non-regression gates remain authoritative.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from brain_llm_experiment import fingerprint as experiment_fingerprint

ROOT = Path(__file__).resolve().parents[2]
CENSUS = ROOT / "automation" / "provider-census-status.json"
MEMORY = ROOT / "automation" / "brain-repair-memory.json"

PUBLIC_KEYS = {
    "routePolicy", "recipePolicy", "roleOrder", "terminalOnly", "aliasSearch",
    "responseSalvage", "documentRequestMining", "sessionBootstrap", "maxDepth",
    "maxPages", "maxEmbeds", "maxRecipePasses",
}

# The executor remains one of the already-sandboxed advisor profiles.
# Novelty comes from a never-tried experiment composition, not arbitrary code.
FAILURE_EXECUTORS: dict[str, tuple[str, str]] = {
    "provider_transport_gap": (
        "provider_origin_failover_v1",
        "meta-gap-provider-transport-composition",
    ),
    "transport_blocked": (
        "provider_origin_failover_v1",
        "meta-gap-provider-transport-composition",
    ),
    "route_proven_gap": (
        "proven_route_terminal_traversal_v1",
        "meta-gap-route-transition-composition",
    ),
    "search_gap": (
        "search_contract_inference_v1",
        "meta-gap-search-contract-composition",
    ),
    "chain_terminal_gap": (
        "chain_terminal_extractor_v1",
        "meta-gap-terminal-media-composition",
    ),
    "media_extraction_gap": (
        "player_media_extractor_v1",
        "meta-gap-terminal-media-composition",
    ),
    "candidate_replay_gap": (
        "retained_candidate_replay_v1",
        "meta-gap-candidate-replay-composition",
    ),
}

BASE_EXPERIMENTS: dict[str, dict[str, Any]] = {
    "provider_transport_gap": {
        "routePolicy": "owned_plus_peer",
        "recipePolicy": "current_plus_provider",
        "roleOrder": ["api", "detail", "search", "player", "source", "episode", "other"],
        "terminalOnly": False,
        "aliasSearch": False,
        "responseSalvage": True,
        "documentRequestMining": True,
        "sessionBootstrap": True,
        "maxDepth": 4,
        "maxPages": 18,
        "maxEmbeds": 16,
        "maxRecipePasses": 5,
    },
    "route_proven_gap": {
        "routePolicy": "owned_plus_peer_generic",
        "recipePolicy": "current_plus_provider_peer",
        "roleOrder": ["search", "detail", "api", "episode", "player", "source", "other"],
        "terminalOnly": False,
        "aliasSearch": True,
        "responseSalvage": True,
        "documentRequestMining": True,
        "sessionBootstrap": False,
        "maxDepth": 5,
        "maxPages": 30,
        "maxEmbeds": 24,
        "maxRecipePasses": 5,
    },
    "search_gap": {
        "routePolicy": "owned_plus_peer_generic",
        "recipePolicy": "current_plus_provider_peer",
        "roleOrder": ["search", "api", "detail", "player", "source", "episode", "other"],
        "terminalOnly": False,
        "aliasSearch": True,
        "responseSalvage": True,
        "documentRequestMining": True,
        "sessionBootstrap": False,
        "maxDepth": 5,
        "maxPages": 32,
        "maxEmbeds": 20,
        "maxRecipePasses": 5,
    },
    "chain_terminal_gap": {
        "routePolicy": "owned_plus_peer",
        "recipePolicy": "current_plus_provider_peer",
        "roleOrder": ["player", "source", "api", "episode", "detail", "search", "other"],
        "terminalOnly": True,
        "aliasSearch": False,
        "responseSalvage": True,
        "documentRequestMining": True,
        "sessionBootstrap": True,
        "maxDepth": 6,
        "maxPages": 24,
        "maxEmbeds": 34,
        "maxRecipePasses": 6,
    },
    "media_extraction_gap": {
        "routePolicy": "owned_only",
        "recipePolicy": "current_plus_provider",
        "roleOrder": ["player", "source", "api", "episode", "detail", "search", "other"],
        "terminalOnly": True,
        "aliasSearch": False,
        "responseSalvage": True,
        "documentRequestMining": True,
        "sessionBootstrap": False,
        "maxDepth": 6,
        "maxPages": 20,
        "maxEmbeds": 36,
        "maxRecipePasses": 6,
    },
    "candidate_replay_gap": {
        "routePolicy": "owned_only",
        "recipePolicy": "current_plus_provider",
        "roleOrder": ["player", "api", "source", "detail", "episode", "search", "other"],
        "terminalOnly": False,
        "aliasSearch": True,
        "responseSalvage": True,
        "documentRequestMining": True,
        "sessionBootstrap": True,
        "maxDepth": 5,
        "maxPages": 22,
        "maxEmbeds": 30,
        "maxRecipePasses": 6,
    },
}
BASE_EXPERIMENTS["transport_blocked"] = BASE_EXPERIMENTS["provider_transport_gap"]


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _canon(value: object) -> str:
    return str(value or "").strip().casefold().replace("-", "_")


def _provider(value: object) -> str:
    return str(value or "").strip().casefold().replace("_", "-")


def _status_failure(row: dict[str, Any]) -> str:
    status = str(row.get("status") or "").strip().upper()
    issue = str(row.get("dominantIssue") or "").casefold()
    depth = " ".join(str(x or "").casefold() for x in row.get("evidenceDepth") or [])
    if status == "CANDIDATE OK":
        return "candidate_replay_gap"
    if status == "CHAIN REACHED" or "chain_reached" in depth:
        return "chain_terminal_gap"
    if "waf" in issue or "challenge" in issue or "blocked" in issue:
        return "provider_transport_gap"
    if status == "ROUTE PROVEN":
        return "route_proven_gap"
    if "lookup_only" in depth:
        return "search_gap"
    return ""


def _latest_failure_by_provider(memory: dict[str, Any]) -> dict[str, str]:
    ranked: dict[str, tuple[tuple[int, int, int, int], str]] = {}
    rows = []
    if isinstance(memory.get("entries"), list):
        rows.extend(memory.get("entries") or [])
    exp = memory.get("experimentMemory") if isinstance(memory.get("experimentMemory"), dict) else {}
    if isinstance(exp.get("entries"), list):
        rows.extend(exp.get("entries") or [])
    for row in rows:
        if not isinstance(row, dict):
            continue
        provider = _provider(row.get("providerId"))
        failure = _canon(row.get("failureClass"))
        if not provider or failure not in FAILURE_EXECUTORS:
            continue
        score = (
            int(row.get("experimentGeneration") or 0),
            int(row.get("experimentVariant") or 0),
            int(row.get("failures") or 0),
            int(row.get("progresses") or 0),
        )
        if provider not in ranked or score >= ranked[provider][0]:
            ranked[provider] = (score, failure)
    return {provider: value[1] for provider, value in ranked.items()}


def _failed_fingerprints(memory: dict[str, Any]) -> set[tuple[str, str, str]]:
    failed: set[tuple[str, str, str]] = set()
    rows = []
    if isinstance(memory.get("entries"), list):
        rows.extend(memory.get("entries") or [])
    exp = memory.get("experimentMemory") if isinstance(memory.get("experimentMemory"), dict) else {}
    if isinstance(exp.get("entries"), list):
        rows.extend(exp.get("entries") or [])
    for row in rows:
        if not isinstance(row, dict) or int(row.get("consecutiveFailures") or 0) < 1:
            continue
        provider = _provider(row.get("providerId"))
        profile = str(row.get("profile") or "").strip().casefold()
        fp = str(row.get("llmAdvisorExperimentFingerprint") or "").strip().casefold()
        if provider and profile and len(fp) == 64:
            failed.add((provider, profile, fp))
    return failed


def _variant(base: dict[str, Any], provider: str, generation: int) -> dict[str, Any]:
    value = copy.deepcopy(base)
    seed = int(hashlib.sha256(f"{provider}:{generation}".encode("utf-8")).hexdigest()[:8], 16)
    route_choices = ("owned_only", "owned_plus_peer", "owned_plus_peer_generic")
    recipe_choices = ("current_only", "current_plus_provider", "current_plus_provider_peer")
    value["routePolicy"] = route_choices[(seed + generation) % len(route_choices)]
    value["recipePolicy"] = recipe_choices[((seed >> 3) + generation) % len(recipe_choices)]
    roles = list(value["roleOrder"])
    rotate = generation % max(1, len(roles))
    value["roleOrder"] = roles[rotate:] + roles[:rotate]
    value["aliasSearch"] = bool(value["aliasSearch"] or generation % 3 == 1)
    value["responseSalvage"] = bool(value["responseSalvage"] or generation % 2 == 0)
    value["documentRequestMining"] = bool(value["documentRequestMining"] or generation % 3 == 2)
    value["sessionBootstrap"] = bool(value["sessionBootstrap"] or generation % 4 == 3)
    value["maxDepth"] = min(6, max(2, int(value["maxDepth"]) + generation // 3))
    value["maxPages"] = min(36, max(6, int(value["maxPages"]) + (generation % 4) * 2))
    value["maxEmbeds"] = min(36, max(6, int(value["maxEmbeds"]) + (generation % 5)))
    value["maxRecipePasses"] = min(6, max(1, int(value["maxRecipePasses"]) + generation // 4))
    assert set(value) == PUBLIC_KEYS
    return value


def synthesize_rows(
    *,
    census: dict[str, Any] | None = None,
    memory: dict[str, Any] | None = None,
    current_sha: str = "",
    max_rows: int = 64,
) -> list[dict[str, Any]]:
    census = census if isinstance(census, dict) else _load(CENSUS)
    memory = memory if isinstance(memory, dict) else _load(MEMORY)
    repair_queue = {_provider(x) for x in census.get("repairQueue") or [] if _provider(x)}
    provider_rows = {
        _provider(row.get("provider")): row
        for row in census.get("providers") or []
        if isinstance(row, dict) and _provider(row.get("provider"))
    }
    memory_failure = _latest_failure_by_provider(memory)
    failed = _failed_fingerprints(memory)
    rows: list[dict[str, Any]] = []
    for provider in sorted(repair_queue):
        status_failure = _status_failure(provider_rows.get(provider) or {})
        # Current strong causal floors (WAF/CHAIN/CANDIDATE/ROUTE) outrank stale
        # historical labels. Memory fills gaps only when the census is weaker.
        failure = status_failure or memory_failure.get(provider) or ""
        if failure not in FAILURE_EXECUTORS:
            continue
        profile, strategy = FAILURE_EXECUTORS[failure]
        base = BASE_EXPERIMENTS[failure]
        chosen: tuple[dict[str, Any], str] | None = None
        for generation in range(16):
            experiment = _variant(base, provider, generation)
            fp = experiment_fingerprint(experiment)
            if (provider, profile, fp) not in failed:
                chosen = experiment, fp
                break
        if chosen is None:
            continue
        experiment, fp = chosen
        rows.append({
            "providerId": provider,
            "failureClass": failure,
            "targetLayer": "provider",
            "strategy": strategy,
            "profile": profile,
            "confidence": 0.86,
            "priorOnly": True,
            "experiment": experiment,
            "experimentFingerprint": fp,
            "guidanceKind": "meta-gap-synthesis",
            "localForceAmbiguous": False,
            "sourceSha": str(current_sha or "").strip().casefold(),
        })
        if len(rows) >= max_rows:
            break
    return rows
