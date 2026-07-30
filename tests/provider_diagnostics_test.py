#!/usr/bin/env python3
from pathlib import Path
import json

root=Path(__file__).resolve().parents[1]
health=(root/'scripts/health_check.mjs').read_text()
worker=(root/'scripts/provider_worker.cjs').read_text()
config=json.loads((root/'health-config.json').read_text())
overrides=json.loads((root/'provider-overrides.json').read_text())
workflow=(root/'.github/workflows/sync.yml').read_text()
assert 'provider_diagnostics' not in config
assert 'diagnosticOrigins' not in health
assert 'probeDiagnosticOrigins' not in worker
assert 'syntheticTmdbResponse' in worker
assert 'fixtureMetadata: fixture' in health
assert 'synthetic_fixture_fallback' in worker
for patch in overrides.get('provider_patches',{}).values():
    assert 'diagnostic_origins' not in patch

preflight=config.get('dns_preflight') or {}
assert preflight.get('enabled') is True
assert preflight.get('primary_french_isp') == 'sfr'
assert preflight.get('fallback_french_isps') == ['orange', 'free']
assert preflight.get('skip_runtime_on_confirmed_french_block') is True
assert 'dnsPreflightForCandidate' in health
assert 'runtime_skipped_by_dns_preflight' in health
assert workflow.index('Test DNS and locate validated alternative domains') < workflow.index('Test provider access and repair failed routes')

print('provider diagnostics tests passed')
