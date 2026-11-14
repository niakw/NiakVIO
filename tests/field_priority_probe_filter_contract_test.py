#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
source = (ROOT / "scripts" / "field_priority_probe.py").read_text(encoding="utf-8")

required = (
    'parser.add_argument("--manifest"',
    '"--providers"',
    "resolve_provider_path",
    "requested enabled providers missing from manifest",
    "executor.submit(probe, row, fixture, timeout, manifest_path)",
    '"manifest": str(manifest_path.relative_to(ROOT))',
    '"requestedProviders": sorted(requested)',
)

for token in required:
    assert token in source, token

assert "str(ROOT / filename)" not in source
print("FIELD_PRIORITY_PROBE_FILTER_CONTRACT_OK")
