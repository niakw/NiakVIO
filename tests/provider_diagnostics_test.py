#!/usr/bin/env python3
from pathlib import Path
import json

root=Path(__file__).resolve().parents[1]
health=(root/'scripts/health_check.mjs').read_text()
worker=(root/'scripts/provider_worker.cjs').read_text()
config=json.loads((root/'health-config.json').read_text())
overrides=json.loads((root/'provider-overrides.json').read_text())
assert 'provider_diagnostics' not in config
assert 'diagnosticOrigins' not in health
assert 'probeDiagnosticOrigins' not in worker
assert 'syntheticTmdbResponse' in worker
assert 'fixtureMetadata: fixture' in health
assert 'synthetic_fixture_fallback' in worker
for patch in overrides.get('provider_patches',{}).values():
    assert 'diagnostic_origins' not in patch
print('provider diagnostics tests passed')
