#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
source = (ROOT / "scripts" / "reconstruct_provider_v3_batch_diagnostic.py").read_text(encoding="utf-8")
validator = (ROOT / "scripts" / "validate_provider_v3_routes_sequential.py").read_text(encoding="utf-8")

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

# Candidate/live DATA can be better even if the final rebuilt JS still regresses.
# Keep that validated DATA, but demote provider/publication authority and defer
# the remaining bundle/runtime problem to Learn.
assert 'PROVIDER_V3_PRESERVE_VALIDATED_DATA_ON_FINAL_FAILURE_V3' in source
assert 'def _demote_unverified_finalization(' in source
assert 'validated-data-retained-final-bundle-unverified' in source
assert 'recognition["publicationAuthority"] = False' in source
assert 'recognized["publicationAuthority"] = False' in source
assert 'live_gate["publication_authority"] = False' in source
assert 'final_proof["validatedDataRetained"] = True' in source
assert 'final_proof["providerAuthorityDemoted"] = True' in source
assert 'providers[provider_id] = pre_finalize_static_row' not in source
assert 'promotedDataRolledBack' not in source

# Explicit failed-live routes stay as diagnostic evidence only; they must not
# survive as executable routeData in a qualified/finalized Provider model.
assert 'PROVIDER_V3_FAILED_LIVE_NOT_EXECUTION_DATA_V1' in validator
assert 'row.get("validationState") != "failed-live"' in validator

print(
    "PROVIDER_V3_BATCH_DIAGNOSTIC_CONTRACT_OK "
    "bounded_slice=true repair_first=true defer_to_learn=true "
    "validated_data_retained=true provider_authority_demoted=true "
    "failed_live_execution_data=false continue_after_provider_failure=true "
    "publication_gate=false final_bundle_reprobe=true"
)
