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
assert 'FIELD_PROVIDER_BATCH_PROVIDER_FAIL' in source
assert 'repair-exhausted' in source
assert 'refusedToAdvance' in source
assert 'refuseAdvanceAfterUnresolved' in source
assert 'repairFirst": True' in source
assert 'publicationGate": False' in source
assert 'diagnosticOnly": False' in source
assert 'prove_final_bundle(' in source
assert 'finalize_provider(' in source
assert 'return 1' in source
assert 'ThreadPoolExecutor' not in source
assert 'as_completed' not in source

fail_at = source.index('FIELD_PROVIDER_BATCH_PROVIDER_FAIL')
assert 'break' in source[fail_at:fail_at + 1200], "unresolved provider must stop the slice"

print(
    "PROVIDER_V3_BATCH_DIAGNOSTIC_CONTRACT_OK "
    "bounded_slice=true repair_first=true continue_after_failure=false "
    "publication_gate=false final_bundle_reprobe=true"
)
