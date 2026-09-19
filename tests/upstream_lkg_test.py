import json
import tempfile
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from upstream_lkg import (
    create_pending, finalize_pending, load_manifest_snapshot,
    load_provider_snapshot, load_registry, record_pending_source,
    validate_manifest_quality, write_pending,
)

manifest = {
    'scrapers': [
        {'id': 'alpha', 'filename': 'providers/alpha.js'},
        {'id': 'beta', 'filename': 'providers/beta.js'},
    ]
}
validate_manifest_quality(manifest, 'demo', {'sources': {}})
try:
    validate_manifest_quality({'scrapers': [{'id': 'a', 'filename': 'a.js'}, {'id': 'a', 'filename': 'b.js'}]}, 'demo', {'sources': {}})
except ValueError as exc:
    assert 'duplicate' in str(exc)
else:
    raise AssertionError('duplicate identifiers must fail')

with tempfile.TemporaryDirectory() as td:
    root = Path(td)
    stage = root / 'checked-artifact' / 'staging'
    stage.mkdir(parents=True)
    pending = create_pending(stage)
    record_pending_source(
        pending, stage, 'demo', manifest,
        'https://example.test/manifest.json',
        {
            'alpha': (b'module.exports={manifest:{id:"alpha"},getStreams:async()=>[]};', 'https://example.test/providers/alpha.js'),
            'beta': (b'module.exports={manifest:{id:"beta"},getStreams:async()=>[]};', 'https://example.test/providers/beta.js'),
        },
    )
    pending_path = write_pending(pending, stage)
    result = finalize_pending(pending_path, root=root)
    assert result['changed_sources'] == 1
    registry = load_registry(root)
    loaded = load_manifest_snapshot(registry, 'demo', root)
    assert loaded and len(loaded[0]['scrapers']) == 2
    assert load_provider_snapshot(registry, 'demo', 'alpha', root).startswith(b'module.exports')

print('upstream LKG tests passed')
