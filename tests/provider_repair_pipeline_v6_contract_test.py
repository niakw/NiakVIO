#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
workflow=(ROOT/'.github/workflows/provider-recognition-repair-v6.yml').read_text(encoding='utf-8')
pipeline=(ROOT/'scripts/run_provider_repair_pipeline_v6.py').read_text(encoding='utf-8')
upgrade=(ROOT/'scripts/upgrade_provider_repair_v6.py').read_text(encoding='utf-8')
yield_audit=(ROOT/'scripts/audit_provider_repair_yield_v6.py').read_text(encoding='utf-8')
skip=json.loads((ROOT/'automation/provider-repair-skip.json').read_text(encoding='utf-8'))

assert workflow.startswith('name: LEARN/FORCE - Provider Recognition Repair V6')
assert workflow.count('scripts/run_provider_repair_pipeline_v6.py --mode "$MODE"') == 1
for mode in ('learn','force','repair'):
    assert mode in workflow
assert 'schedule:' in workflow
assert 'allow_upstream_positive_loss' in workflow
assert 'Verify known-green providers were not network re-probed' in workflow

known={'allwish','anime-sama','castle','hindmoviez','kehflix','neko-sama','streamzo','videasy','wookafr'}
assert set((skip.get('providers') or {}).keys()) == known
assert 'provider not in skipped' in pipeline
assert 'for provider in targets:' in pipeline
assert 'cmd.extend(["--provider", provider])' in pipeline
assert 'scripts/merge_provider_repair_report_v6.py' in pipeline
assert 'scripts/apply_provider_route_recovery_report.py' in pipeline
assert 'scripts/materialize_provider_base_v3_store.py' in pipeline
assert 'scripts/materialize_provider_v3_all.py' in pipeline
assert 'scripts/audit_provider_repair_yield_v6.py' in pipeline
assert '--require-upstream-positive-preserved' in pipeline
assert 'publicationAllowed": False' in pipeline
assert 'mainWritesAllowed": False' in pipeline

for marker in (
    'NIAKVIO_PROVIDER_REPAIR_PORTFOLIO_V6',
    'ROUTE_RECOVERY_TERMINAL_SEARCH_RECIPE_V6',
    'ROUTE_RECOVERY_BODY_SEARCH_RECIPE_V6',
    '_record_has_search_query(row)',
    'NIAKVIO_PROVIDER_BASE_BOUNDED_EXTERNAL_ROOT_V10',
    '_crawlFollowable(next,responseUrl)',
):
    assert marker in upgrade, marker
assert 'targeted = {' in yield_audit
assert 'if provider_id not in targeted' in yield_audit
assert 'lostUpstreamPositivePairs' in yield_audit
assert 'require_upstream_positive_preserved' in yield_audit
print('provider repair pipeline v6 contract passed')
