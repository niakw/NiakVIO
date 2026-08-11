#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OVERRIDES = ROOT / 'provider-overrides.json'
PACKAGE = ROOT / 'package.json'
GLOBAL_TEST = ROOT / 'tests' / 'global_provider_policy_test.py'
OLD = 'scripts/provider_patches/global_catalogue_alias_recovery_v1.py'
NEW = 'scripts/provider_patches/global_catalogue_alias_recovery_v2.py'

cfg = json.loads(OVERRIDES.read_text(encoding='utf-8'))
cfg['schema_version'] = max(7, int(cfg.get('schema_version') or 0))
policy = cfg.get('catalogue_resolution_policy')
if not isinstance(policy, dict):
    raise SystemExit('catalogue_resolution_policy missing')
policy['version'] = 2
policy['id_first'] = True
policy['tmdb_and_imdb_first'] = True
policy['global_discovery_hook'] = NEW
policy.setdefault('options', {})['max_aliases'] = 8
OVERRIDES.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

package = json.loads(PACKAGE.read_text(encoding='utf-8'))
command = package['scripts']['test']
new_test = 'python3 tests/global_catalogue_alias_recovery_test.py'
if new_test not in command:
    command += ' && ' + new_test
package['scripts']['test'] = command
PACKAGE.write_text(json.dumps(package, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

test = GLOBAL_TEST.read_text(encoding='utf-8')
test = test.replace('NUVIO_GLOBAL_CATALOGUE_ALIAS_RECOVERY_V1', 'NUVIO_GLOBAL_CATALOGUE_ALIAS_RECOVERY_V2')
test = test.replace(
    'assert cat["enabled"] is True and cat["id_first"] is True\n',
    'assert cat["enabled"] is True and cat["id_first"] is True\nassert cat["tmdb_and_imdb_first"] is True\nassert cat["version"] == 2\n',
)
test = test.replace(
    'for token in (\n    "alternative_titles",\n    "original_title",\n    "language=en-US",\n',
    'for token in (\n    "alternative_titles",\n    "original_title",\n    "external_source=imdb_id",\n    "/find/",\n    "language=en-US",\n',
)
GLOBAL_TEST.write_text(test, encoding='utf-8')

print('global catalogue policy migrated to TMDB/IMDb V2')
