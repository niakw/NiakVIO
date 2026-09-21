#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_provider_remat_test.py"
source = SCRIPT.read_text(encoding="utf-8")

for required in (
    "materialize_provider_v3_one.py",
    "run_provider_retest.py",
    "select_providers",
    "publicationAllowed",
    "changedByteProviders",
):
    assert required in source, required

for forbidden in (
    "run_provider_brain_repair.py",
    "run_adaptive_deep_repair.py",
    "recover_provider_routes_from_upstreams.py",
    "probe_waf_browser_session.py",
):
    assert forbidden not in source, forbidden

assert '"non-full", "repair", "all"' in source
assert 'action="append"' in source
print("provider remat/test separation contract passed")
