#!/usr/bin/env python3
"""Do not mint v53 on a stale ROUTE PROVEN label without current route proof.

The negative witness is the *actual semantic shape* of #42504716876 for
4khdhub: an old census ROUTE PROVEN status / retained route count, but
current movie and TV report provider_network_zero_result, depth lookup/none,
and no same-work detail/player/media or terminal stream.

This is a Brain input-evidence contract, not a fake positive playable test.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "niakvio_brain_route_freshness",
    ROOT / "scripts/build_brain_architecture_proposal.py",
)
assert spec and spec.loader
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)

failure_history = {"4khdhub": {"route_transition_graph_v1"}}
installed = {"route_transition_graph_v1"}
observed = {
    "groupId": "route-to-terminal|html_scraper",
    "repairScope": "route-to-terminal",
    "capabilityStrategy": "html_scraper",
    "providers": ["4khdhub"],
    "evidenceDepths": ["lookup", "none"],
    "dominantIssues": ["network_zero_result", "waf_challenge"],
    "transportSignature": "not-applicable",
}
blocked = builder.build_strategy_blueprints(
    {"groups": [observed]}, {"4khdhub"}, failure_history,
    existing_executable_profiles=installed,
)
assert len(blocked) == 1, blocked
plan = blocked[0]
assert plan["forcePromotionEligible"] is False, plan
assert plan["currentRouteEvidenceReady"] is False, plan
assert plan["forcePromotionReason"] == "current-route-identity-proof-unavailable", plan
assert "live and identity-qualified" not in plan["causalTrigger"], plan
assert "current" in plan["causalTrigger"], plan
assert "requalify" in plan["method"], plan
assert "current same-work TMDB and episode correlation" in plan["requiredEvidence"], plan
assert plan["productionWritesAllowed"] is False, plan
assert plan["requiresHumanMerge"] is True, plan

# A still-incomplete catalogue hit alone does not prove a detail/player route.
for depths in ([], ["none"], ["lookup"], ["search"], ["provider", "lookup"]):
    with_depths = dict(observed, evidenceDepths=depths)
    row = builder.build_strategy_blueprints(
        {"groups": [with_depths]}, {"4khdhub"}, failure_history,
        existing_executable_profiles=installed,
    )[0]
    assert row["forcePromotionEligible"] is False, (depths, row)

# When the Brain has a real deeper observed frontier, the causal strategy
# remains eligible for isolated execution, NEVER for provider publication.
qualified = dict(observed, evidenceDepths=["detail", "player"])
valid_plan = builder.build_strategy_blueprints(
    {"groups": [qualified]}, {"4khdhub"}, failure_history,
    existing_executable_profiles=installed,
)[0]
assert valid_plan["currentRouteEvidenceReady"] is True, valid_plan
assert valid_plan["forcePromotionEligible"] is True, valid_plan
assert valid_plan["currentObservedDepths"] == ["detail", "player"], valid_plan
assert valid_plan["productionWritesAllowed"] is False, valid_plan
assert "playback-verified media" in valid_plan["acceptanceProof"], valid_plan

print("BRAIN_CURRENT_ROUTE_EVIDENCE_GATE_OK lookup_only_refused=true detail_frontier_eligible=true playable_proof=false")
