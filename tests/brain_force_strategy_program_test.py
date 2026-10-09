#!/usr/bin/env python3
"""Brain 7B typed recovery algorithm compiler: safety, novelty and determinism."""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "brain_force_strategy_program", ROOT / "scripts/brain_force_strategy_program.py",
)
assert spec and spec.loader
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

base = {
    "searchSources": ["configured", "learned", "peer"],
    "directSources": ["positive", "peer", "learned"],
    "requestSources": ["historical", "current", "peer"],
    "roleOrder": ["source", "player", "api", "detail"],
    "transitionMode": "owned-combined",
    "terminalRoleFilter": True,
    "budgets": {"search": 16, "direct": 40, "requests": 48, "transitions": 24},
}
code = m.compile_recovery_program(base)
assert "search_paths = _unique_routes(" in code
assert "request_recipes = _unique_request_recipes(" in code
assert "second_order_role_preferences" in code
assert "new_strategy_id" not in code
assert "positive_program_routes(provider_id)" in code
assert "_owned_transition_prefixes" in code
assert m.compile_recovery_program(dict(base)) == code
# Even a pure peer/generic model experiment cannot suppress the verified
# provider-local search and request fallback. The new hypothesis remains
# present but cannot erase the successful older causal inputs.
exploration = dict(base)
exploration["searchSources"] = ["peer", "generic"]
exploration["directSources"] = ["peer"]
exploration["requestSources"] = ["peer", "historical"]
generated = m.compile_recovery_program(exploration)
assert "search_paths = _unique_routes(configured_search, learned_search, peer_search, generic_search" in generated
assert "direct_paths = _unique_routes(configured_direct, learned_direct, peer_direct" in generated
assert "request_recipes = _unique_request_recipes(current_request_recipes, provider_request_recipes, peer_request_recipes" in generated

for bad in (
    {**base, "searchSources": ["../provider-private-source"]},
    {**base, "searchSources": ["peer", "peer"]},
    {**base, "roleOrder": ["source", "invalid"]},
    {**base, "transitionMode": "__import__('os').system('false')"},
    {**base, "terminalRoleFilter": "true"},
    {**base, "budgets": {**base["budgets"], "requests": 9000}},
    {**base, "requestSources": ["current", "historical"],
     "directSources": ["positive", "learned"],
     "searchSources": ["configured", "learned"],
     "transitionMode": "owned-direct",
     "terminalRoleFilter": False},
    {**base, "providerId": "unsafe-provider-override"},
):
    try:
        m.compile_recovery_program(bad)
    except ValueError:
        pass
    else:
        raise AssertionError("invalid/tautological Brain program accepted: " + repr(bad))
print("Brain FORCE typed recovery program compiler tests passed")
