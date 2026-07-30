#!/usr/bin/env python3
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
config=json.loads((ROOT/'health-config.json').read_text())
assert config['modes']['deep'].get('fixture_limit_per_category') is True
health=(ROOT/'scripts/health_check.mjs').read_text()
assert 'profile.requiredCategories' in health
assert "groups[category]" in health
worker=(ROOT/'scripts/provider_worker.cjs').read_text()
assert 'Empty output is never proof' in worker
sync=(ROOT/'scripts/discover_candidates.py').read_text()
assert 'published-baseline' in sync
assert 'provider_lkg_registry' in sync
assert 'Last published local artifact' in sync
print('category regression and baseline policy tests passed')
