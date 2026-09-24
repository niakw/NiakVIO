#!/usr/bin/env python3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
source=(ROOT/"scripts/run_provider_repair_pipeline_v6.py").read_text(encoding="utf-8")
assert "def reapply_transport_overlay(*, phase: str)" in source
assert source.count("reapply_transport_overlay(phase=phase)")==2,source.count("reapply_transport_overlay(phase=phase)")
refresh=source[source.index("def refresh_census("):source.index("def persist_repair_candidate_evidence(")]
persisted=source[source.index("def render_persisted_byte_census("):source.index("def rematerialize_repair_scope(")]
for block in (refresh,persisted):
 assert block.count("reapply_transport_overlay(phase=phase)")==1
 assert block.index("reapply_transport_overlay(phase=phase)") < block.index('scripts/build_provider_repair_batch_plan.py')
helper=source[source.index("def reapply_transport_overlay("):source.index("def refresh_census(")]
assert "merge_waf_census_transport.py" in helper
assert "render_provider_census_status_from_state.py" in helper
print("Repair internal transport overlay persistence contract passed")
