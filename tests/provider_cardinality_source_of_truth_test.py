#!/usr/bin/env python3
from __future__ import annotations
import re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CHECK=[
 "scripts/check_provider_non_regression_v1.py",
 "scripts/hub_activation_publication.py",
 "scripts/provider_v3_minimizer.py",
 "scripts/merge_provider_repair_report_v6.py",
 "scripts/build_hub46_blocker_inventory.py",
 "scripts/provider_parallel_sweep_plan_v1.py",
 "scripts/reconcile_provider_catalog_media_types.py",
 "scripts/verify_provider_v3_reverse_rebuild.py",
 "scripts/archive_nonhub_providerbases.py",
 "scripts/upgrade_streamzo_runtime_v1.py",
 "scripts/run_provider_repair_pipeline_v6.py",
 "scripts/run_provider_repair_fast_targeted_v1.py",
 "scripts/build_published_provider_stage.py",
 "scripts/validate_published_provider_config.py",
 "scripts/finalize_provider_repair_disposition_v1_impl.py",
 "scripts/generate_hub46_manifest.py",
 "scripts/build_hub46_native_manifest.py",
 "scripts/route_proof_activation_preservation_v1.py",
 "scripts/domain_refresh_transaction_v2.py",
 "scripts/normalize_hub46_semantic_transport_sources.py",
 "scripts/normalize_hub46_release_gate_sources.py",
]
patterns=[
 re.compile(r"\b(?:EXPECTED(?:_[A-Z_]+)?|CURRENT_PROVIDER_COUNT|EXPECTED_CURRENT|EXPECTED_ACTIVE)\s*=\s*(?:44|46|96)\b"),
 re.compile(r"len\([^\n]+?\)\s*(?:==|!=)\s*(?:44|46|96)\b"),
]
bad=[]
for rel in CHECK:
 text=(ROOT/rel).read_text(encoding="utf-8")
 for pat in patterns:
  if pat.search(text): bad.append(f"{rel}: {pat.pattern}")
assert not bad, "hard-coded current provider cardinality remains:\n"+"\n".join(bad)
print("provider cardinality source-of-truth contract passed")
