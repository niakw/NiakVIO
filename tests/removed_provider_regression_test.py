#!/usr/bin/env python3
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
removed={'dahmermovies','dahmermovies-tv'}
for rel in ['manifest.json','vf/manifest.json']:
    data=json.loads((ROOT/rel).read_text())
    ids={str(row.get('id','')).casefold() for row in data.get('scrapers',[])}
    assert not (ids & removed),(rel,ids & removed)
for path in (ROOT/'providers').glob('dahmermovies*.js'):
    raise AssertionError(f'removed provider artifact remains: {path}')
sources=json.loads((ROOT/'sources.json').read_text())
serialized=json.dumps(sources).casefold()
for provider_id in removed:
    assert provider_id in serialized, f'{provider_id} must remain in explicit exclusions'

# Client-cache invalidation belongs exclusively to the consolidated ARCHI2
# publication transaction. The old standalone bump helper must not return.
sync=(ROOT/'.github/workflows/sync.yml').read_text()
assert 'sync_release_versions.py' in sync
assert 'NUVIO_PUBLISHED_MANIFEST_BASELINE' in sync
assert sync.count('sync_release_versions.py') >= 2, 'audit mutations must be finalized too'
assert 'bump_release_patch_if_manifest_changed.py' not in sync
assert not (ROOT/'scripts/bump_release_patch_if_manifest_changed.py').exists()
resume=ROOT/'.github/workflows/resume-publish.yml'
assert not resume.exists(), 'obsolete resume-publish workflow must not be restored after CI consolidation'
print('removed provider and client-cache regression tests passed')
