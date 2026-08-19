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
assert spec.loader is not None
spec.loader.exec_module(mod)

canonical = mod.manifest_providers('manifest.json')
canonical_manifest = json.loads((ROOT / 'manifest.json').read_text(encoding='utf-8'))
assert len(canonical) >= 90, len(canonical)
assert len({str(row['id']).casefold() for row in canonical}) == len(canonical)
for row in canonical:
    assert row['source'].is_file(), row['id']
    assert row['manifest'] == 'manifest.json', row['id']

# Any alternate manifest used by a repair/lab must be an in-repository projection
# that points to locally present provider bundles. This keeps the staging contract
# generic without retaining a historical playback-hotfix repository.
with tempfile.TemporaryDirectory(dir=ROOT, prefix='.native-manifest-test-') as tmp:
    temp_root = Path(tmp)
    selected = canonical_manifest.get('scrapers', [])[:2]
    assert len(selected) == 2
    alternate = temp_root / 'manifest.json'
    alternate.write_text(json.dumps({'name': 'Native staging fixture', 'scrapers': selected}), encoding='utf-8')
    alternate_rel = alternate.relative_to(ROOT)

    rows = mod.manifest_providers(alternate_rel)
    assert [str(row['id']).casefold() for row in rows] == [str(row['id']).casefold() for row in selected]
    assert all(row['source'].is_file() for row in rows)

    destination = temp_root / 'assets'
    staged = mod.stage_manifest_providers(destination, alternate_rel)
    assert [row['id'] for row in staged] == [row['id'] for row in rows]
    for row in staged:
        copied = destination / row['asset']
        assert copied.read_bytes() == row['source'].read_bytes(), row['id']

try:
    mod.manifest_providers('../outside.json')
except SystemExit as error:
    assert 'must live inside the repository' in str(error)
else:
    raise AssertionError('manifest traversal must fail closed')

print('generic in-repository manifest staging tests passed')
