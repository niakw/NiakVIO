#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
source = (ROOT / "scripts" / "reconstruct_provider_v3_batch_diagnostic.py").read_text(encoding="utf-8")

assert 'parser.add_argument("--start-index"' in source
assert 'parser.add_argument("--count"' in source
assert 'parser.add_argument("--repair-attempts"' in source
assert 'selected = queue[start - 1:end]' in source
assert 'for absolute_index, provider in enumerate(selected, start=start):' in source
assert 'FIELD_PROVIDER_REPAIR_BEGIN' in source
assert 'FIELD_PROVIDER_REPAIR_RESULT' in source
assert 'FIELD_PROVIDER_REPAIR_STALLED' in source
assert '_stage_runtime_repair_candidates(' in source
assert 'FIELD_PROVIDER_BATCH_PROVIDER_DEFER' in source
assert 'repair-exhausted' in source
assert 'defer-to-learn' in source
assert 'learnRequired' in source
assert 'deferred_to_learn' in source
assert 'continueAfterRepairExhausted": True' in source
assert 'providerScopedFailuresDeferToLearn": True' in source
assert 'refuseAdvanceAfterUnresolved": False' in source
assert 'repairFirst": True' in source
assert 'publicationGate": False' in source
assert 'diagnosticOnly": False' in source
assert 'prove_final_bundle(' in source
assert 'finalize_provider(' in source
assert 'return 1' in source  # reserved for non-provider/global hard failures
assert 'ThreadPoolExecutor' not in source
assert 'as_completed' not in source
assert 'refused_provider = provider_id' not in source
assert 'refusing_next=' not in source

repair_defer_at = source.index('repair_exhausted=true')
window = source[repair_defer_at:repair_defer_at + 900]
assert 'learn=true' in window
assert 'continue' in window, "repair-exhausted provider must defer to Learn and advance"

# A candidate can qualify while its finalized rebuild regresses. That failure is
# Learn evidence, not permission to leave the broken promoted DATA as authority.
assert 'PROVIDER_V3_DEFER_FINALIZATION_ROLLBACK_V2' in source
assert 'pre_finalize_static_row = copy.deepcopy(static_row)' in source
assert 'pre_finalize_patch = copy.deepcopy(patch)' in source
assert 'providers[provider_id] = pre_finalize_static_row' in source
assert 'patches[provider_id] = pre_finalize_patch' in source
assert 'final_proof["promotedDataRolledBack"] = True' in source
assert '"promotedDataRolledBack": True' in source

print(
    "PROVIDER_V3_BATCH_DIAGNOSTIC_CONTRACT_OK "
    "bounded_slice=true repair_first=true defer_to_learn=true "
    "failed_final_rollback=true continue_after_provider_failure=true "
    "publication_gate=false final_bundle_reprobe=true"
)
