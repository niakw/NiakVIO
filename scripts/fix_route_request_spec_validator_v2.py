#!/usr/bin/env python3
from pathlib import Path

path = Path('scripts/upgrade_route_recovery_request_specs_v1.py')
text = path.read_text(encoding='utf-8')
old = '''    for needle in (\n        '\"executionRoutes\": execution_routes',\n        'generic_execution_route(row)',\n        'row.get(\"requestSpecReusable\") is True',\n        'patch[\"learned_routes\"] = execution_routes',\n    ):\n        if needle not in recovery:\n            raise AssertionError(f\"recovery request-spec wiring missing: {needle}\")\n'''
new = '''    for needle in (\n        '\"executionRoutes\": execution_routes',\n        'generic_execution_route(row)',\n        'row.get(\"requestSpecReusable\") is True',\n        'runtime_routes, preserved_baseline_plan = select_runtime_routes(',\n        'patch[\"learned_routes\"] = runtime_routes',\n        'model[\"routes\"] = runtime_routes',\n        '\"genericExecutionRouteCount\": len(execution_routes)',\n        '\"runtimePlanPreserved\": preserved_baseline_plan',\n    ):\n        if needle not in recovery:\n            raise AssertionError(f\"recovery request-spec wiring missing: {needle}\")\n    if 'patch[\"learned_routes\"] = execution_routes' in recovery:\n        raise AssertionError('obsolete direct execution-route overwrite must not bypass conservative runtime-plan selection')\n'''
if new in text:
    print('ROUTE_REQUEST_SPEC_VALIDATOR_V2_ALREADY_PRESENT')
elif text.count(old) == 1:
    path.write_text(text.replace(old, new, 1), encoding='utf-8')
    print('ROUTE_REQUEST_SPEC_VALIDATOR_V2_APPLIED')
else:
    raise SystemExit(f'route request-spec validator anchor count={text.count(old)}')
