#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


meta = load_module(
    "force_readiness_meta_gap",
    ROOT / "scripts/brain_layers/declarative_gap_strategy.py",
)
runtime = load_module(
    "force_readiness_runtime",
    ROOT / "scripts/adaptive_runtime/runtime_repair.py",
)

census = json.loads(
    (ROOT / "automation/provider-census-status.json").read_text(encoding="utf-8")
)
queue = {
    str(value or "").strip().casefold().replace("_", "-")
    for value in census.get("repairQueue") or []
    if str(value or "").strip()
}
assert queue, "current repairQueue is unexpectedly empty; update readiness semantics if the project is fully repaired"

provider_rows = {
    str(row.get("provider") or "").strip().casefold().replace("_", "-"): row
    for row in census.get("providers") or []
    if isinstance(row, dict) and str(row.get("provider") or "").strip()
}
assert queue <= set(provider_rows), sorted(queue - set(provider_rows))

# With empty negative memory, every current repair-eligible provider must map to
# an executable causal family and receive a bounded meta-gap experiment.
synthetic = meta.synthesize_rows(
    census=census,
    memory={"entries": [], "experimentMemory": {"entries": []}},
    current_sha="a" * 40,
    max_rows=max(64, len(queue)),
)
by_provider = {
    str(row.get("providerId") or "").strip().casefold().replace("_", "-"): row
    for row in synthetic
    if isinstance(row, dict)
}
assert set(by_provider) == queue, {
    "missing": sorted(queue - set(by_provider)),
    "extra": sorted(set(by_provider) - queue),
}

expected_focus = {
    "provider_transport_gap": "transport-first",
    "route_proven_gap": "proven-route-chain",
    "chain_terminal_gap": "terminal-chain",
    "candidate_replay_gap": "candidate-replay",
}

coverage = {}
for provider in sorted(queue):
    source = provider_rows[provider]
    failure = meta._status_failure(source)
    assert failure in meta.FAILURE_EXECUTORS, (provider, failure, source.get("status"), source.get("dominantIssue"))
    assert failure in runtime.CAUSAL_STRATEGY_BASES, (provider, failure)
    profile, strategy = meta.FAILURE_EXECUTORS[failure]
    generated = by_provider[provider]
    assert generated["failureClass"] == failure, (provider, generated)
    assert generated["profile"] == profile, (provider, generated)
    assert generated["strategy"] == strategy, (provider, generated)
    assert len(str(generated.get("experimentFingerprint") or "")) == 64, provider

    focus = runtime._census_runtime_focus(provider)
    wanted = expected_focus.get(failure)
    if wanted:
        assert focus.get("focus") == wanted, (provider, failure, focus)
    coverage[provider] = {
        "status": source.get("status"),
        "issue": source.get("dominantIssue"),
        "failure": failure,
        "profile": profile,
        "focus": focus.get("focus"),
    }

# The current cohort requires these three causal families. Keep this assertion
# descriptive rather than provider-count based so the gate keeps working as the
# queue shrinks after future successful repairs.
current_families = {row["failure"] for row in coverage.values()}
assert {"provider_transport_gap", "route_proven_gap", "chain_terminal_gap"} <= current_families, current_families

# A family executor is not enough: a novel runtime mechanism must have a bounded
# mutation path, isolated rematerialization and strict playable+identity proof.
bridge = (ROOT / "scripts/apply_brain_llm_force_mutations.py").read_text(encoding="utf-8")
sandbox = (ROOT / "scripts/evaluate_brain_llm_force_candidates.py").read_text(encoding="utf-8")
architecture = (ROOT / "BRAIN_REPAIR_ARCHITECTURE.md").read_text(encoding="utf-8")
for marker in (
    'scope == "provider_bloc"',
    "def _render_generated_bloc_module",
    "def _register_generated_bloc",
    "def _provider_owned_source",
):
    assert marker in bridge, marker
for marker in (
    "materialize_provider_v3_one.py",
    "evaluate_pair(baseline, candidate)",
    "automatic_repair_identity_gate(candidate)",
    "strict runtime improvement",
):
    assert marker in sandbox, marker
assert "Brain-generated runtime Blocs" in architecture

print(
    "Brain FORCE cohort offline readiness passed "
    f"providers={len(queue)} families={','.join(sorted(current_families))}"
)
for provider, row in sorted(coverage.items()):
    print(
        "FIELD_BRAIN_FORCE_READINESS "
        f"provider={provider} failure={row['failure']} "
        f"profile={row['profile']} focus={row['focus']}"
    )
