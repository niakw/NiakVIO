#!/usr/bin/env python3
"""Domain refresh publication races: only evidence, never executable drift."""
from __future__ import annotations
import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location(
    "domain_evidence_gate",ROOT/"scripts/domain_refresh_publication_drift_gate.py")
assert spec and spec.loader
gate=importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)
safe=[
    "M\tMEMORY.md",
    "M\tPROVIDER_CENSUS_STATUS.md",
    "M\tautomation/brain-llm-force-memory.json",
    "A\tautomation/hosted-repair-evidence/42364560525.json",
    "A\tautomation/hosted-repair-evidence/42364560525-evaluation.json",
    "A\tautomation/hosted-repair-evidence/42364560525-http-observation.json",
    "A\tautomation/hosted-repair-evidence/42364560525-mutations.json",
    "A\tautomation/hosted-repair-evidence/42364560525-player-markup.json",
]
assert gate.classify_drift(safe) == (True, [])
assert gate.classify_drift(["automation/provider-census-status.json"]) == (True, [])
for bad in (
    "M\tautomation/hosted-repair-evidence/42364560525.json",
    "D\tautomation/hosted-repair-evidence/42364560525.json",
    "automation/hosted-repair-evidence/42364560525.json",
    "A\tautomation/hosted-repair-evidence/42364560525-provider.js",
    "A\tautomation/hosted-repair-evidence/42364560525-context.json",
    "M\tprovider-overrides.json",
    "M\tproviders/4khdhub.js",
    "M\tscripts/provider_worker.cjs",
    "M\t.github/workflows/domain-refresh.yml",
    "D\tprovider-bases/demo.js",
):
    ok,rejected=gate.classify_drift(safe+[bad])
    assert not ok and bad in rejected, (bad,ok,rejected)
print("DOMAIN_REFRESH_RACE_EVIDENCE_CONTRACT_OK append_only=true provider_mutation=blocked")
