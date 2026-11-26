#!/usr/bin/env python3
"""Explicit Brain Learning cohorts execute family oracles without losing siblings."""
from __future__ import annotations
import ast
from pathlib import Path

root = Path(__file__).resolve().parents[1]
source = (root / "scripts/run_brain_learning_queue.py").read_text(encoding="utf-8")
tree = ast.parse(source)
main = next(x for x in tree.body if isinstance(x, ast.FunctionDef) and x.name == "main")
snippet = ast.get_source_segment(source, main)
assert snippet is not None
assert 'p.add_argument("--provider-filter", default=""' in snippet
assert "learning_scope = repair_learning_scope(" in snippet
assert "family_deferred = []" not in snippet
assert "order = family_frontier" in snippet
assert "fair_handoff = bool(learning_scope) and not bool(args.provider)" in snippet
assert 'queue["repairLearningScopeProviders"] = learning_scope' in snippet
assert 'queue["repairLearningDeferredPortfolioProviders"] = portfolio_deferred' in snippet
assert '"explicit-cohort-one-representative-per-causal-family-siblings-pending"' in snippet
assert "if provider_id not in staged_candidates or provider_id not in info_by_id" in snippet
assert "fastRepairHandoffParallelExecutionEnabled" in snippet
assert "if fair_handoff and attempts_this_phase >= 1" in snippet
workflow = (root / ".github/workflows/brain-learning-lab.yml").read_text(encoding="utf-8")
assert 'args+=(--provider-filter "$TARGET_PROVIDER_COHORT")' in workflow
print("Brain explicit Learning multi-provider cohort contract passed")
