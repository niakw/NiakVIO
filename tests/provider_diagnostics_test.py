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

# ARCHI2 keeps DNS/domain evidence before runtime repair. Assert semantic
# stage ordering rather than obsolete human-facing step names.
dns_stage = 'Resolve DNS and validated domain migrations'
profile_stage = 'Apply known runtime profiles before repair'
repair_stage = 'Repair unresolved provider structures'
diagnostics_stage = 'Generate diagnostics after repair'
assert dns_stage in workflow and profile_stage in workflow and repair_stage in workflow and diagnostics_stage in workflow
assert workflow.index(dns_stage) < workflow.index(profile_stage) < workflow.index(repair_stage) < workflow.index(diagnostics_stage)
assert 'provider_dns_preflight.mjs' in workflow
assert 'apply_dns_migration_overrides.py' in workflow
assert 'run_adaptive_quick_repair.py' in workflow
assert 'run_adaptive_deep_repair.py' in workflow

assert 'fixture_status_counts' in health
assert 'failure_class' in health
assert 'error_details' in health
assert 'sanitizeStructuredError' in health
assert 'runtime_errors: Array.isArray(worker.runtime_errors) ? worker.runtime_errors.map(sanitizeStructuredError)' in health
assert 'score=${result.score}' in health
assert "stream_count: streams.length" in health
assert 'maxSettingsProfiles' in health
assert 'NUVIO_INVALID_REQUEST_ARGUMENT' in worker
assert 'runtime_errors: profileErrors' in worker
assert 'fixture_metadata' not in worker
assert overrides['runtime_repair']['require_playable_stream_proof'] is True
assert overrides['patch_profiles']['metadata_context_recovery']['runtime_auto_apply'] is False

print('provider diagnostics tests passed')
