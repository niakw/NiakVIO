#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/run_brain_learning_queue.py"
spec = importlib.util.spec_from_file_location("brain_learning_wave_merge", SCRIPT)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

def row(provider: str, profile: str, outcome: str) -> dict:
    return {
        "providerId": provider,
        "providerVersion": "*",
        "failureClass": "synthetic-gap",
        "signature": f"sig-{provider}",
        "profile": profile,
        "experimentVariant": 4,
        "experimentGeneration": 5,
        "attempts": 1,
        "successes": 0,
        "failures": 1,
        "consecutiveFailures": 1,
        "progresses": 0,
        "lastOutcome": outcome,
        "lastReason": "synthetic",
        "lastSeenAt": "2026-09-22T13:00:00+00:00",
        "memoryRole": "fair-share-exact-experiment-ledger",
        "executionObserved": True,
    }

a = row("family-a-provider", "runtime_response_salvage_v1", "rejected")
b = row("family-b-provider", "document_request_contract_mining_v1", "not_generated")
base = {
    "publicationAllowed": False,
    "productionWritesAllowed": False,
    "experimentMemory": {"schemaVersion": 1, "entries": []},
}

ab = mod.merge_wave_experiment_entries(base, [[a], [b]])
ba = mod.merge_wave_experiment_entries(base, [[b], [a]])

assert ab == ba, (ab, ba)
entries = ab["experimentMemory"]["entries"]
assert [x["providerId"] for x in entries] == ["family-a-provider", "family-b-provider"], entries
assert all(x["executionObserved"] is True for x in entries)

# A second wave must accumulate evidence through the same canonical merge,
# rather than replacing the first wave's provider-local memory.
a2 = dict(a)
a2["attempts"] = 2
a2["lastOutcome"] = "exploration_progress_nonpublishable"
next_state = mod.merge_wave_experiment_entries(ab, [[a2]])
by_provider = {x["providerId"]: x for x in next_state["experimentMemory"]["entries"]}
assert by_provider["family-a-provider"]["attempts"] == 3, by_provider
assert by_provider["family-b-provider"]["attempts"] == 1, by_provider

source = SCRIPT.read_text(encoding="utf-8")
for needle in (
    "causal_family_waves",
    "causal_family_frontier",
    "merge_wave_experiment_entries",
    "fastRepairHandoffParallelExecutionEnabled",
):
    assert needle in source, needle

# Regression for Repair->Learning Fast-Handoff initialization. The real handoff
# previously crashed before provider 1 because causal_waves read fair_handoff
# before the local had been assigned. Keep the runtime dependency order locked.
owner_assignment = source.index("brain_owned_repair, brain_owner_authority = brain_owned_current_repair_providers(")
scope_assignment = source.index("learning_scope = repair_learning_scope(")
fair_assignment = source.index("fair_handoff = bool(learning_scope) and not bool(args.provider)")
frontier_assignment = source.index("family_frontier, family_deferred = causal_family_frontier(")
wave_assignment = source.index("causal_waves = causal_family_waves(full_handoff_order, batch_plan, max_parallel=4) if fair_handoff else []")
assert owner_assignment < scope_assignment < fair_assignment < frontier_assignment < wave_assignment, (owner_assignment, scope_assignment, fair_assignment, frontier_assignment, wave_assignment)
assert "fastRepairHandoffDeferredFamilySiblings" in source
assert "brain_owned_current_repair_providers(" in source
assert "repair_learning_scope(" in source
assert 'queue["brainOwnedCurrentRepairProviders"] = brain_owned_repair' in source
assert "fair_handoff = bool(learning_scope) and not bool(args.provider)" in source
assert "bool(handoff_priority) and not bool(args.provider)" not in source
assert "order = family_frontier" in source
assert "family_deferred = []" not in source
assert "scoped_order, batch_plan, info_by_id" in source
assert "causal_family_frontier(order, batch_plan, by_id)" not in source
assert 'queue["repairLearningDeferredPortfolioProviders"] = portfolio_deferred' in source
assert 'p.add_argument("--provider-filter", default=""' in source
assert 'explicit_cohort if explicit_cohort' in source
assert 'brain_owned_repair' in source
assert 'handoff_priority' in source
assert 'queue["explicitLearningCohort"] = explicit_cohort' in source

# One family oracle is chosen from the strongest current observation, not
# merely the first provider in caller order. The cohort itself remains intact.
plan = {
    "groups": [{
        "groupId": "family-a",
        "providers": ["first-noisy", "second-observed", "third-healthy"],
    }]
}
provider_info = {
    "first-noisy": {
        "status": "runtime_error", "score": 90, "needs_route_search": True,
        "server_accessible": False, "server_successful_response": False, "host_count": 0,
    },
    "second-observed": {
        "status": "no_streams", "score": 35, "needs_route_search": False,
        "server_accessible": True, "server_successful_response": True, "host_count": 2,
    },
    "third-healthy": {
        "status": "healthy", "score": 0, "needs_route_search": False,
        "server_accessible": True, "server_successful_response": True, "host_count": 3,
    },
}
frontier, deferred = mod.causal_family_frontier(
    ["first-noisy", "second-observed", "third-healthy"], plan, provider_info
)
assert frontier == ["second-observed"], (frontier, deferred)
assert deferred == ["first-noisy", "third-healthy"], (frontier, deferred)

# Missing diagnostics stay deterministic and preserve caller order.
frontier, deferred = mod.causal_family_frontier(["alpha", "beta"], {
    "groups": [{"groupId": "family-b", "providers": ["alpha", "beta"]}]
})
assert frontier == ["alpha"] and deferred == ["beta"], (frontier, deferred)

workflow = (ROOT / ".github/workflows/brain-learning-lab.yml").read_text(encoding="utf-8")
assert 'TARGET_PROVIDER_COHORT: ${{ steps.learning-slot.outputs.provider_filter || \'\' }}' in workflow
assert 'args+=(--provider-filter "$TARGET_PROVIDER_COHORT")' in workflow

# A busy provider's newer wave must not flush an earlier single executed
# failure for a different provider. Prior Learning used rows[-1000:] before
# Repair could apply its provider-fair negative-memory selector.
cold = row("uhdmovies", "terminal_request_program_inference_v1", "rejected")
hot = [
    row("4khdhub", f"route_transition_graph_v{index}", "rejected")
    for index in range(1, 15)
]
overflow = mod.merge_phase_learning_state(
    {
        "publicationAllowed": False,
        "productionWritesAllowed": False,
        "experimentMemory": {"schemaVersion": 1, "entries": [cold]},
    },
    hot,
    max_entries=10,
)
survivors = overflow["experimentMemory"]["entries"]
assert len(survivors) == 10, len(survivors)
assert any(r["providerId"] == "uhdmovies" for r in survivors), (
    "earlier underrepresented provider evidence was lost after wave overflow"
)
assert mod._learning_memory_capacity() == 16000, (
    "Learning and production must use the same persisted bounded capacity"
)

print("Brain Learning causal-wave memory merge tests passed")
