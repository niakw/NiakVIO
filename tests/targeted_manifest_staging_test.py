#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
module_path = ROOT / 'scripts/prepare_native_corpus_client.py'
spec = importlib.util.spec_from_file_location('prepare_native_corpus_client', module_path)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

canonical = {row['id'].casefold(): row for row in mod.manifest_providers('manifest.json')}
hotfix = {row['id'].casefold(): row for row in mod.manifest_providers('playback-hotfix/manifest.json')}

assert set(hotfix) == {'4khdhub', 'moviesdrive', 'moviesmod', 'movieshunt'}, hotfix.keys()
assert 'moviesdrive' in canonical
assert canonical['moviesdrive']['source'].name != hotfix['moviesdrive']['source'].name
assert canonical['moviesdrive']['source'].name == 'moviesdrive--nuvio--5c1560b0f357722d.js'
assert hotfix['moviesdrive']['source'].name == 'moviesdrive--emergency-native-first--bf1b8ea425de3e7a.js'
assert hotfix['4khdhub']['source'].name == '4khdhub--emergency-native-first--7085d8f0adcfe55c.js'
assert all(row['source'].is_file() for row in hotfix.values())
assert all(row['manifest'] == 'playback-hotfix/manifest.json' for row in hotfix.values())

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
