#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
source=(ROOT/"scripts"/"health_check.mjs").read_text(encoding="utf-8")

for required in (
    "NUVIO_HEALTH_PROVIDER_FILTER",
    "normalizedProviderFilterId",
    "health provider filter missing staged candidates",
    "FIELD_HEALTH_PROVIDER_FILTER",
    "registry.candidates = selected",
):
    assert required in source, required

assert "requestedProviderFilter.size > 0" in source
assert "replaceAll('_', '-')" in source

print("health provider filter contract passed")
