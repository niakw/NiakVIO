#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HEALTH = ROOT / 'scripts' / 'health_check.mjs'
TEST = ROOT / 'tests' / 'global_provider_policy_test.py'

source = HEALTH.read_text(encoding='utf-8')
anchor = '''  const categoriesNeedingFallback = new Set(\n    profile.requiredCategories.filter((category) => {\n      const rows = primaryResults.filter((item) => item.fixture?.category === category);\n      return rows.length > 0\n        && !rows.some((item) => item.status === 'healthy')\n        && !rows.some((item) => item.status === 'excluded');\n    }),\n  );\n'''
replacement = anchor + "  let fallbackExecuted = false;\n"
if 'let fallbackExecuted = false;' not in source:
    if anchor not in source:
        raise SystemExit('fallback state anchor missing')
    source = source.replace(anchor, replacement, 1)

execute_anchor = "      for (const fixture of categoryFallbacks) {\n        await executeFixture(fixture, 'fallback');\n"
execute_replacement = "      for (const fixture of categoryFallbacks) {\n        fallbackExecuted = true;\n        await executeFixture(fixture, 'fallback');\n"
if 'fallbackExecuted = true;' not in source:
    if execute_anchor not in source:
        raise SystemExit('fallback execution anchor missing')
    source = source.replace(execute_anchor, execute_replacement, 1)

source = source.replace('fallback_triggered: useFallback,', 'fallback_triggered: fallbackExecuted,')
source = source.replace("activation_fixture_phase: useFallback ? 'fallback' : 'primary',", "activation_fixture_phase: fallbackExecuted ? 'fallback' : 'primary',")
if 'useFallback' in source:
    raise SystemExit('stale useFallback reference remains')
HEALTH.write_text(source, encoding='utf-8')

test = TEST.read_text(encoding='utf-8')
block = '''\nhealth_source = (ROOT / "scripts" / "health_check.mjs").read_text(encoding="utf-8")\nassert "let fallbackExecuted = false;" in health_source\nassert "fallbackExecuted = true;" in health_source\nassert "useFallback" not in health_source\n'''
if 'assert "useFallback" not in health_source' not in test:
    marker = '\nprint("global ID-first catalogue/media and broad activation policy tests passed")\n'
    if marker not in test:
        raise SystemExit('global policy test marker missing')
    test = test.replace(marker, block + marker, 1)
TEST.write_text(test, encoding='utf-8')

print('global fallback execution state fixed')
