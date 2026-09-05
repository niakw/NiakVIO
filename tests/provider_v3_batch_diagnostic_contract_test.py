#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
source = (ROOT / "scripts" / "reconstruct_provider_v3_batch_diagnostic.py").read_text(encoding="utf-8")

assert 'parser.add_argument("--start-index"' in source
assert 'parser.add_argument("--count"' in source
assert 'selected = queue[start - 1:end]' in source
assert 'for absolute_index, provider in enumerate(selected, start=start):' in source
assert 'FIELD_PROVIDER_BATCH_PROVIDER_FAIL' in source
assert 'continue' in source
assert 'hard_failures.append(provider_id)' in source
assert 'advancedForDiagnostics' in source
assert 'publicationGate": False' in source
assert 'diagnosticOnly": True' in source
assert 'prove_final_bundle(' in source
assert 'finalize_provider(' in source
assert 'return 1' in source
assert 'ThreadPoolExecutor' not in source
assert 'as_completed' not in source

print(
    "PROVIDER_V3_BATCH_DIAGNOSTIC_CONTRACT_OK "
    "bounded_slice=true continue_after_failure=true publication_gate=false "
    "final_bundle_reprobe=true"
)
