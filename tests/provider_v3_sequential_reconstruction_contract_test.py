#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
source = (ROOT / "scripts" / "reconstruct_provider_v3_sequential_live.py").read_text(encoding="utf-8")

assert "ThreadPoolExecutor" not in source
assert "as_completed" not in source
assert "for index, provider in enumerate(queue, start=1):" in source
assert "run_until_qualified(provider, model, minimum, timeout)" in source
assert "finalize_provider(" in source
assert "materialize_one(provider_id)" in source
assert "prove_final_bundle(" in source
assert "refusing to advance to provider" in source
assert "active_coverage_main()" in source

finalize_at = source.index("finalize_provider(", source.index("for index, provider"))
materialize_at = source.index("materialize_one(provider_id)", finalize_at)
proof_at = source.index("prove_final_bundle(", materialize_at)
pass_at = source.index("FIELD_PROVIDER_SEQUENTIAL_PASS", proof_at)
assert finalize_at < materialize_at < proof_at < pass_at

one = (ROOT / "scripts" / "materialize_provider_v3_one.py").read_text(encoding="utf-8")
assert "materialize_one" in one
assert "build_provider_data_model" in one
assert "validate_managed_fixes" in one
assert "minimize_text" in one

print(
    "Provider v3 sequential reconstruction contract passed: candidate live proof -> "
    "DATA finalize -> one-provider rematerialization -> final JS live proof -> next provider."
)
