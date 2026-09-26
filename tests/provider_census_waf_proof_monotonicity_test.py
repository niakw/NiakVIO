#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

render_spec = importlib.util.spec_from_file_location(
    "render_provider_census_status",
    ROOT / "scripts" / "render_provider_census_status.py",
)
assert render_spec and render_spec.loader
render = importlib.util.module_from_spec(render_spec)
render_spec.loader.exec_module(render)

update_spec = importlib.util.spec_from_file_location(
    "update_provider_census_proof_history",
    ROOT / "scripts" / "update_provider_census_proof_history.py",
)
assert update_spec and update_spec.loader
update = importlib.util.module_from_spec(update_spec)
update_spec.loader.exec_module(update)


def waf_row(provider: str, *, progress: str = "none") -> dict:
    return {
        "provider_id": provider,
        "semantic_type": "movie",
        "status": "no_streams",
        "debug_stage": "provider_waf_challenge",
        "debug_progress_stage": progress,
        "verified": 0,
        "contradictions": 0,
        "samples": [],
    }


history: dict = {"providers": {}}
matrix = {
    "providers": [{
        "provider": "historical",
        "historicalVerifiedLanes": ["movie", "tv"],
        "historicalPositiveVersions": ["5.21.36"],
    }]
}
update.seed_historical_lane_flags(history, matrix)
movie = history["providers"]["historical"]["lanes"]["movie"]
tv = history["providers"]["historical"]["lanes"]["tv"]
assert movie["historicalPositive"] is True
assert tv["historicalPositive"] is True
assert movie["historicalPositiveSource"] == "provider-history-matrix"
assert movie["historicalPositiveVersions"] == ["5.21.36"]
assert movie["proofs"] == []

# Historical positivity without an exact retained fixture is a proof floor only.
# It prevents WAF from erasing provider knowledge, but does not pretend playback
# is currently verified or invent a regression fixture.
assert render.provider_state(
    "historical",
    [waf_row("historical")],
    history,
    {},
    {},
    {},
) == "NO PROOF"

route_overrides = {
    "provider_patches": {
        "route": {
            "live_route_gate": {
                "completion_state": "declared-types-qualified",
                "required_types": ["movie"],
                "validated_types": ["movie"],
                "missing_types": [],
                "live_validated_route_count": 2,
                "provider_request_count": 2,
            }
        }
    }
}
assert render.provider_state(
    "route",
    [waf_row("route")],
    {},
    {},
    route_overrides,
    {},
) == "ROUTE PROVEN"

assert render.provider_state(
    "chain",
    [waf_row("chain", progress="chain_reached")],
    {},
    {},
    {},
    {},
) == "CHAIN REACHED"

# A provider with no route, chain, candidate or historical provider evidence may
# still be classified as environment/harness blocked.
assert render.provider_state(
    "unknown",
    [waf_row("unknown")],
    {},
    {},
    {},
    {},
) == "HARNESS/ENV BLOCKED"

# The same proof monotonicity applies when an unresolved-scope census carries a
# previous row and reconciles a fresh WAF challenge.
assert render._carried_non_green_status(
    {
        "dominantIssue": "provider_waf_challenge",
        "candidateProof": [],
        "routeProof": ["2 live routes / movie"],
        "evidenceDepth": ["movie=none"],
        "historicalProof": [],
    },
    "route",
    {},
) == "ROUTE PROVEN"

assert render._carried_non_green_status(
    {
        "dominantIssue": "provider_waf_challenge",
        "candidateProof": [],
        "routeProof": [],
        "evidenceDepth": ["movie=none"],
        "historicalProof": ["movie: historical lane positive"],
    },
    "historical",
    {},
) == "NO PROOF"

print("provider census WAF proof monotonicity contract passed")
