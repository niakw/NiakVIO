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

wf=(ROOT/".github/workflows/temp-individual-provider-max-repair.yml").read_text(encoding="utf-8")
assert "assert len(include)==46" not in wf
assert '= "46"' not in wf
assert "math.ceil(provider_count*0.75)" in wf
assert '"acceptanceRatio":0.75' in wf

print(f"dynamic provider scope contracts passed visible={visible_provider_count()} active={active_provider_count()}")
