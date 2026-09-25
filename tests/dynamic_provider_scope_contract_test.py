#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from current_provider_scope import active_provider_count, visible_provider_count

text=(ROOT/"tests/provider_js_lego_ownership_test.py").read_text(encoding="utf-8")
assert "visible_provider_count" in text
assert "visible_provider_ids" in text
assert "active_provider_count" not in text
assert "providers=96" not in text
assert visible_provider_count() >= active_provider_count()

# Scalability is owned by the canonical Repair V6 workflow. It must derive
# targets from the census repairQueue / explicit symptomatic provider and prove
# that network reprobes never escape that selected symptom set.
wf=(ROOT/".github/workflows/provider-recognition-repair-v6.yml").read_text(encoding="utf-8")
assert "empty means census repairQueue only" in wf
assert "Run canonical recognition and correction only for unresolved providers" in wf
assert 'args=(python scripts/run_provider_repair_pipeline_v6.py --mode "$MODE")' in wf
assert 'args+=(--provider "$TARGET_PROVIDER")' in wf
assert "automation/provider-route-recovery-v6-targeted.json" in wf
assert "Verify only census symptoms were network re-probed" in wf
assert "PROVIDER_REPAIR_CENSUS_SCOPE_PROOF" in wf
assert "assert len(include)==46" not in wf
assert '= "46"' not in wf

# The obsolete full-catalogue TEMP max-repair workflow was a second Repair
# architecture that re-probed every visible provider; it must stay removed.
assert not (ROOT/".github/workflows/temp-individual-provider-max-repair.yml").exists()

print(f"dynamic provider scope contracts passed visible={visible_provider_count()} active={active_provider_count()}")
