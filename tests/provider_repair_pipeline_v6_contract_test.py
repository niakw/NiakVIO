#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
workflow=(ROOT/'.github/workflows/provider-recognition-repair-v6.yml').read_text(encoding='utf-8')
pipeline=(ROOT/'scripts/run_provider_repair_pipeline_v6.py').read_text(encoding='utf-8')
upgrade=(ROOT/'scripts/upgrade_provider_repair_v6.py').read_text(encoding='utf-8')
upgrade_v10=(ROOT/'scripts/upgrade_provider_base_runtime_v10.py').read_text(encoding='utf-8')
upgrade_v14=(ROOT/'scripts/upgrade_provider_search_request_plan_v14.py').read_text(encoding='utf-8')
yield_audit=(ROOT/'scripts/audit_provider_repair_yield_v6.py').read_text(encoding='utf-8')
portfolio_compare=(ROOT/'scripts/compare_quick_yield_preservation.py').read_text(encoding='utf-8')
targeted_retry=(ROOT/'scripts/audit_provider_quick_yield_targeted.py').read_text(encoding='utf-8')
merge_repair=(ROOT/'scripts/merge_provider_repair_report_v6.py').read_text(encoding='utf-8')
skip=json.loads((ROOT/'automation/provider-repair-skip.json').read_text(encoding='utf-8'))

assert workflow.startswith('name: LEARN/FORCE - Provider Recognition Repair V6')
assert workflow.count('scripts/run_provider_repair_pipeline_v6.py --mode "$MODE"') == 1
for mode in ('learn','force','repair'):
    assert mode in workflow
assert 'schedule:' in workflow
assert 'allow_upstream_positive_loss' in workflow
assert 'Verify known-green providers were not network re-probed' in workflow
assert 'targetProviders' in workflow
assert 'CANONICAL_REPAIR_ARGS' in workflow
assert 'provider-repair-portfolio-baseline.json' in workflow
assert 'provider-repair-portfolio-candidate.json' in workflow
assert 'provider-repair-portfolio-retry.json' in workflow

known={'allwish','anime-sama','castle','hindmoviez','kehflix','neko-sama','playimdb','streamzo','videasy','wookafr'}
assert set((skip.get('providers') or {}).keys()) == known
assert 'provider not in skipped' in pipeline
assert 'for provider in targets:' in pipeline
assert 'cmd.extend(["--provider", provider])' in pipeline
assert 'scripts/merge_provider_repair_report_v6.py' in pipeline
assert 'scripts/apply_provider_route_recovery_report.py' in pipeline
assert 'scripts/materialize_provider_base_v3_store.py' in pipeline
assert 'scripts/materialize_provider_v3_all.py' in pipeline
for required in (
    'scripts/upgrade_provider_external_identity_route_v11_1.py',
    'scripts/upgrade_provider_source_plan_v12.py',
    'scripts/upgrade_provider_route_plan_v13_2.py',
    'scripts/upgrade_provider_search_request_plan_v14.py',
    'tests/provider_external_identity_route_v11_test.py',
    'tests/provider_source_plan_v12_regression_test.py',
    'tests/provider_route_plan_v13_regression_test.py',
    'tests/provider_search_request_plan_v14_contract_test.py',
    'tests/provider_repair_merge_typed_recipe_test.py',
):
    assert required in pipeline, required
assert '"routePlanRevision": "v14"' in pipeline
assert 'tests/provider_repair_v6_recipe_regression_test.py' in pipeline
assert 'scripts/audit_provider_repair_yield_v6.py' in pipeline
assert '--require-upstream-positive-preserved' in pipeline
assert 'capture_portfolio_yield(PORTFOLIO_BASELINE)' in pipeline
assert 'capture_portfolio_yield(PORTFOLIO_CANDIDATE)' in pipeline
assert 'scripts/compare_quick_yield_preservation.py' in pipeline
assert 'scripts/audit_provider_quick_yield_targeted.py' in pipeline
assert 'portfolioPreservationGatePassed' in pipeline
assert 'upstreamPositivePreservationGatePassed' in pipeline
assert 'publicationAllowed": False' in pipeline
assert 'mainWritesAllowed": False' in pipeline

assert 'raw_providers' in portfolio_compare
assert 'lost_raw' in portfolio_compare
assert 'new wrong-content provider detected' in portfolio_compare
assert '--candidate-retry' in portfolio_compare
assert 'TARGETED_YIELD_RETRY_DONE' in targeted_retry
assert 'attempts = max(1, min(int(args.attempts), 3))' in targeted_retry
assert 'normalize_typed_api_recipe' in merge_repair
assert 'typedRecipeDirectRouteSanitizedCount' in merge_repair
assert 'recipe.pop("directRoute", None)' in merge_repair
assert 'recipe.pop("directRequest", None)' in merge_repair

for marker in (
    'NIAKVIO_PROVIDER_REPAIR_PORTFOLIO_V6',
    'ROUTE_RECOVERY_TERMINAL_SEARCH_RECIPE_V6',
    'ROUTE_RECOVERY_BODY_SEARCH_RECIPE_V6',
    '_record_has_search_query(row)',
    '_repair_recipe_origin_allowed(row)',
    'taskLastRequestIndex',
    'not (movie_candidates or episode_candidates)',
):
    assert marker in upgrade, marker
for marker in (
    'NIAKVIO_PROVIDER_BASE_BOUNDED_EXTERNAL_ROOT_V10',
    '_crawlFollowable(next,responseUrl)',
):
    assert marker in upgrade_v10, marker
for marker in (
    'ROUTE_RECOVERY_SEARCH_REQUEST_PLAN_V14',
    'PROVIDER_SEARCH_REQUEST_PLAN_V14',
    'NIAKVIO_PROVIDER_BASE_SEARCH_REQUEST_PLAN_V14',
    'provider_specific_rules=0',
):
    assert marker in upgrade_v14, marker
assert 'import upgrade_provider_base_runtime_v10 as runtime_v10' in upgrade
assert 'runtime_v10.patch()' in upgrade
assert 'targeted = {' in yield_audit
assert 'if provider_id not in targeted' in yield_audit
assert 'lostUpstreamPositivePairs' in yield_audit
assert 'require_upstream_positive_preserved' in yield_audit
print('provider repair pipeline v6 contract passed')
