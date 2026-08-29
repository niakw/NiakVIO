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

# ARCHI2 now resolves provider routes centrally before discovery/repair rather
# than coupling a French-ISP DNS preflight to every health runtime. Keep the
# route/LKG stage ordered ahead of provider mutation and diagnostics.
assert 'dns_preflight' not in config
assert 'dnsPreflightForCandidate' not in health
assert 'runtime_skipped_by_dns_preflight' not in health
route_stage = 'Resolve official hubs and retain last-known-good routes'
discovery_stage = 'Discover all non-P2P candidates before triage'
profile_stage = 'Apply known runtime profiles before repair'
repair_stage = 'Repair unresolved provider structures'
diagnostics_stage = 'Generate diagnostics after repair'
assert route_stage in workflow and discovery_stage in workflow and profile_stage in workflow and repair_stage in workflow and diagnostics_stage in workflow
assert workflow.index(route_stage) < workflow.index(discovery_stage) < workflow.index(profile_stage) < workflow.index(repair_stage) < workflow.index(diagnostics_stage)
assert 'resolve_provider_hubs.py --apply' in workflow
assert '--include-disabled' in workflow
assert '--output health-output/provider-hub-report.json' in workflow
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
