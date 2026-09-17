#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = (ROOT / '.github/workflows/domain-refresh.yml').read_text(encoding='utf-8')
RECONCILE = (ROOT / 'scripts/reconcile_provider_domain_metadata.py').read_text(encoding='utf-8')
GUARD = (ROOT / 'scripts/validate_domain_refresh_non_destructive.py').read_text(encoding='utf-8')
PROVENANCE = (ROOT / 'scripts/reconcile_domain_refresh_provenance.py').read_text(encoding='utf-8')

assert 'validate_domain_refresh_non_destructive.py' in WORKFLOW
assert 'reconcile_domain_refresh_provenance.py' in WORKFLOW
assert 'provider-v3-materialization.before.json' in WORKFLOW
assert 'provenance.before.json' in WORKFLOW
assert 'reconcile_provider_domain_metadata.py --rebuild "${ARGS[@]}"' in WORKFLOW
assert 'ARGS+=(--provider "$provider_id")' in WORKFLOW
assert 'finalize_provider_v3_minimizer.py --check' in WORKFLOW
assert 'python scripts/finalize_provider_v3_minimizer.py\n' not in WORKFLOW
assert 'python scripts/prune_unreferenced_providers.py' not in WORKFLOW
assert 'repair_disposition changed during Domain Refresh' in GUARD
assert 'untouched provider patch mutated' in GUARD
assert 'unrelated provider bundles' in GUARD
assert 'parser.add_argument("--provider", action="append", default=[])' in RECONCILE
assert 'if selected and provider_id not in selected' in RECONCILE
assert 'published_filename' in PROVENANCE and 'final_minimizer' in PROVENANCE

print('DOMAIN_REFRESH_NON_DESTRUCTIVE_WORKFLOW_OK scoped_reconcile=1 global_minimizer_apply=0 global_prune=0 repair_evidence_guard=1 unrelated_bundle_guard=1')
