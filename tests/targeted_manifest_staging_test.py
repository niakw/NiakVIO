#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
module_path = ROOT / 'scripts/prepare_native_corpus_client.py'
spec = importlib.util.spec_from_file_location('prepare_native_corpus_client', module_path)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

canonical = {row['id'].casefold(): row for row in mod.manifest_providers('manifest.json')}
hotfix = {row['id'].casefold(): row for row in mod.manifest_providers('playback-hotfix/manifest.json')}
canonical_manifest = {
    str(row.get('id') or '').casefold(): row
    for row in json.loads((ROOT / 'manifest.json').read_text(encoding='utf-8')).get('scrapers', [])
    if isinstance(row, dict) and row.get('id')
}
hotfix_manifest = {
    str(row.get('id') or '').casefold(): row
    for row in json.loads((ROOT / 'playback-hotfix/manifest.json').read_text(encoding='utf-8')).get('scrapers', [])
    if isinstance(row, dict) and row.get('id')
}

assert set(hotfix) == {'4khdhub', 'moviesdrive', 'moviesmod', 'movieshunt'}, hotfix.keys()
assert 'moviesdrive' in canonical
assert canonical['moviesdrive']['source'] == (ROOT / canonical_manifest['moviesdrive']['filename']).resolve()
for provider_id, row in hotfix.items():
    assert row['source'] == (ROOT / hotfix_manifest[provider_id]['filename']).resolve(), provider_id
    assert row['source'].is_file(), provider_id
    assert row['manifest'] == 'playback-hotfix/manifest.json', provider_id

# The historical emergency manifest is intentionally a distinct selectable tree;
# the canonical manifest may be regenerated at any time and must not be pinned to
# one content-addressed filename in this staging contract test.
assert canonical['moviesdrive']['source'] != hotfix['moviesdrive']['source']

with tempfile.TemporaryDirectory() as tmp:
    destination = Path(tmp) / 'assets'
    staged = mod.stage_manifest_providers(destination, 'playback-hotfix/manifest.json')
    assert [row['id'] for row in staged] == ['4khdhub', 'MOVIESDRIVE', 'MOVIESMOD', 'movieshunt']
    for row in staged:
        copied = destination / row['asset']
        assert copied.read_bytes() == row['source'].read_bytes(), row['id']

try:
    mod.manifest_providers('../outside.json')
except SystemExit as error:
    assert 'must live inside the repository' in str(error)
else:
    raise AssertionError('manifest traversal must fail closed')

print('targeted deployed-manifest staging tests passed')
