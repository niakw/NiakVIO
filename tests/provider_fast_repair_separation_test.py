#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_provider_fast_repair.py"
spec = importlib.util.spec_from_file_location("provider_fast_repair", SCRIPT)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

status = {
    "repairQueue": ["a", "b"],
    "providers": [
        {"provider": "a", "status": "ROUTE PROVEN"},
        {"provider": "b", "status": "CHAIN REACHED"},
        {"provider": "c", "status": "FULL OK"},
    ],
}
assert mod.selected_targets(status, set()) == ["a", "b"]
assert mod.selected_targets(status, {"b"}) == ["b"]
assert mod.dynamic_completeness_targets(status, {"dynamicVariantProviders":["c"]}) == {"c"}
assert mod.selected_targets(
    status, {"c"}, architecture_force=True, completeness={"c"}
) == ["c"]
try:
    mod.selected_targets(status, {"c"})
except ValueError:
    pass
else:
    raise AssertionError("explicit non-repair provider must fail closed")
try:
    mod.selected_targets(status, {"d"}, architecture_force=True, completeness={"c"})
except ValueError:
    pass
else:
    raise AssertionError("FORCE must fail closed outside current dynamic completeness debt")

source = SCRIPT.read_text(encoding="utf-8")
for required in (
    "run_provider_brain_repair.py",
    "run_provider_retest.py",
    "acceptedProgramCompiledProviders",
    "fixedInLabProviders",
    "--max-rounds-per-batch",
    "default=1",
    "--architecture-force",
    "dynamicVariantProviders",
):
    assert required in source, required
for forbidden in (
    "materialize_provider_v3_all.py",
    "recover_provider_routes_from_upstreams.py",
    "merge_waf_census_transport.py",
    "provider-waf-browser-session",
):
    assert forbidden not in source, forbidden


workflow = (ROOT / ".github/workflows/provider-fast-repair.yml").read_text(encoding="utf-8")
for required in (
    "Persist current unresolved Fast Brain debt into LEARN handoff",
    "scripts/provider_repair_learn_handoff_v1.py",
    "automation/provider-repair-learn-handoff-v1.json",
    "learnHandoffProviders",
    "FIELD_PROVIDER_FAST_REPAIR_LEARNING_DEBT",
    "learning_dispatch=true",
    "owner=immediate-targeted-learning",
    "learning_dispatch=false reason=github_api_unavailable persisted=true",
    "owner=persisted-fast-handoff",
    "gh workflow run brain-learning-lab.yml",
    '-f target_providers="$learn_handoff_csv"',
    "Import sanitized persistent Learning and Brain LLM priors",
    "scripts/import_external_brain_llm_guidance.py",
    "NiakVIO-Brain-LLM.git",
    "NIAKVIO_BRAIN_LLM_GUIDANCE=",
    "FIELD_PROVIDER_FAST_REPAIR_EXTERNAL_LLM_GUIDANCE",
    "--negative-memory automation/brain-repair-memory.json",
    "empty-after-negative-memory-filter",
    "max_rounds_per_batch",
    "maxRoundsPerBatch",
    "FIELD_PROVIDER_FAST_REPAIR_REQUEUE",
    "brain_llm_advisor_execution_test.py",
    'options: ["1", "2", "3", "4", "5", "6"]',
    "remote-main-trigger",
    "source_trigger_blob",
    "remote_trigger_blob",
    "provider-fast-repair-current-trigger.json",
    'git show "origin/main:.github/triggers/provider-fast-repair.json"',
    "requeue_target_providers",
    "-f target_providers=\"$requeue_target_providers\"",
    "-f waves=\"$requeue_waves\"",
    "-f time_budget_seconds=\"$requeue_budget\"",
    "-f max_rounds_per_batch=\"$requeue_rounds\"",
):
    assert required in workflow, required
# Evidence-only workflow/census history must not restart the exact same
# 0-accepted Fast cohort. Changed Brain memory, executable sources, target
# trigger or semantic provider status must still authorize a retry.
assert "FIELD_PROVIDER_FAST_REPAIR_REQUEUE skipped=no_executable_or_causal_evidence_drift" in workflow
assert 'git merge-base --is-ancestor "$GITHUB_SHA" "$remote_main"' in workflow
assert 'git diff --quiet "$GITHUB_SHA" "$remote_main" --' in workflow
assert "automation/brain-repair-memory.json" in workflow
assert "automation/brain-positive-program-memory.json" in workflow
assert "automation/provider-repair-candidate-evidence.json" in workflow
assert "automation/provider-census-status.json" in workflow
assert 'old_census" = "$new_census"' in workflow
assert ".github/triggers/provider-fast-repair.json; then" in workflow
assert workflow.index("skipped=no_executable_or_causal_evidence_drift") < workflow.index("requeue_target_provider=")
assert "workflow_run" not in workflow
# A stale result has only negative experiment-memory authority. Requeued runs
# can import it solely from a same-repo, same-workflow, unchanged runtime and
# provider byte lineage; this never imports or publishes stale provider bytes.
assert "prior_fast_run_id" in workflow
assert 'prior_fast_run_id="$GITHUB_RUN_ID"' in workflow
assert "Restore compatible stale Fast Brain negative priors" in workflow
assert 'git merge-base --is-ancestor "$prior_sha" "$GITHUB_SHA"' in workflow
assert 'git diff --quiet "$prior_sha" "$GITHUB_SHA"' in workflow
assert "merge_stale_fast_repair_memory.py" in workflow
assert "executable-or-provider-byte-drift" in workflow
assert "provider-fast-repair-$prior" in workflow

assert "arm_learning_trigger" not in workflow
assert "cat > .github/triggers/brain-learning-reconstruction" not in workflow
assert "provider_learning_dispatch_gate.py mark" not in workflow
assert "group: provider-fast-repair-main" in workflow
assert "cancel-in-progress: false" in workflow
assert "cancel-in-progress: true" not in workflow

assert 'force_mode="$(python - <<\'PY\'' in workflow
assert 'publish_proposal="false"' in workflow
assert '-f publish_proposal="$publish_proposal"' in workflow
assert 'args+=(-f architecture_force=true)' in workflow
assert 'architecture_force=$force_mode' in workflow
assert 'publish_proposal=$publish_proposal' in workflow

print("provider fast repair separation contract passed")
