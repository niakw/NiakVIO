#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
source = (ROOT / "scripts" / "reconstruct_provider_v3_sequential_live.py").read_text(encoding="utf-8")

assert "ThreadPoolExecutor" not in source
assert "as_completed" not in source
assert "for index, provider in enumerate(queue, start=1):" in source
assert "run_until_qualified(provider, model, minimum, timeout)" in source
assert "finalize_provider(" in source
assert source.count("materialize_one(provider_id)") >= 2
assert "prove_final_bundle(" in source
assert "refusing to materialize or advance to provider" in source
assert "active_coverage_main()" in source
assert '"globalCandidateMaterialization": False' in source

loop_at = source.index("for index, provider in enumerate(queue, start=1):")
candidate_materialize_at = source.index("candidate_materialized = materialize_one(provider_id)", loop_at)
probe_at = source.index("run_until_qualified(provider, model, minimum, timeout)", candidate_materialize_at)
finalize_at = source.index("finalize_provider(", probe_at)
final_materialize_at = source.index("materialized = materialize_one(provider_id)", finalize_at)
proof_at = source.index("prove_final_bundle(", final_materialize_at)
pass_at = source.index("FIELD_PROVIDER_SEQUENTIAL_PASS", proof_at)
assert loop_at < candidate_materialize_at < probe_at < finalize_at < final_materialize_at < proof_at < pass_at

one_path = ROOT / "scripts" / "materialize_provider_v3_one.py"
one = one_path.read_text(encoding="utf-8")
assert "materialize_one" in one
assert "build_provider_data_model" in one
assert "validate_managed_fixes" in one
assert "minimize_text" in one
assert "reconcile_domain_substitutions" in one
assert "FIELD_PROVIDER_DOMAIN_SUBSTITUTIONS_RECONCILED" in one

spec = importlib.util.spec_from_file_location("materialize_provider_v3_one_contract", one_path)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

sample = {
    "provider_patches": {
        "flemmix": {
            "domain_substitutions": {
                "legacy.example": "flemmix.men",
                "ww1.wiflix-adresses.fun": "flemmix.men",
            },
            "replacements": {
                "flemmix.men": "flemmix.kim",
                "ww1.wiflix-adresses.fun": "flemmix.kim",
                "unrelated.example": "elsewhere.example",
            },
            "runtime_domain_replacements": {},
        }
    }
}
changed = module.reconcile_domain_substitutions(sample)
assert changed == ["flemmix"], changed
mapping = sample["provider_patches"]["flemmix"]["domain_substitutions"]
assert mapping["legacy.example"] == "flemmix.kim", mapping
assert mapping["ww1.wiflix-adresses.fun"] == "flemmix.kim", mapping
assert mapping["flemmix.men"] == "flemmix.kim", mapping
assert "unrelated.example" not in mapping, mapping

print(
    "Provider v3 sequential reconstruction contract passed: candidate N materialize -> "
    "live proof -> DATA finalize -> final N materialize -> final JS live proof -> only then N+1; "
    "stale domain substitution chains collapse to the current replacement terminal."
)
