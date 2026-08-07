#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MARKER = '[Nuvio Runtime Repair] Using fixture title metadata'
EXPECTED = {
    'anime-ultime': '667e5fba43cdd8840b4625ce13ae71cd2d4bdea3d668297a5a845c21b0e0399f',
    'dulourd': 'e62064b45a10a505612be560f20cbd39ad34be7fa69c4fcafe51d9714f72aa05',
    'waveanime': '1a87a44dbbfb3bc6e7757c401eb0730e994f8661a8cc3b77741c3b36ba522c90',
}
ALLOWED_SOURCES = {'gowaru', 'published-baseline'}
OLD = {
    'providers/anime-ultime--nuvio--f4764da821cbba42.js',
    'providers/dulourd--published-baseline--5801a7212df4ccfd.js',
    'providers/waveanime--nuvio--ddb3016b783859b3.js',
    'providers/wookafr--published-baseline--0e26ebd372c411f5.js',
}

manifest = json.loads((ROOT / 'manifest.json').read_text())
entries = {str(row.get('id')).casefold(): row for row in manifest.get('scrapers', [])}
provenance = json.loads((ROOT / 'PROVENANCE.json').read_text()).get('providers', {})
for provider_id, digest in EXPECTED.items():
    relative = entries[provider_id]['filename']
    target = ROOT / relative
    assert target.is_file(), relative
    assert hashlib.sha256(target.read_bytes()).hexdigest() == digest
    assert MARKER not in target.read_text(encoding='utf-8', errors='strict')

    name = target.name
    prefix = f'{provider_id}--'
    suffix = f'--{digest[:16]}.js'
    assert name.startswith(prefix) and name.endswith(suffix), name
    source = name[len(prefix):-len(suffix)]
    assert source in ALLOWED_SOURCES, (provider_id, source)

    row = provenance[provider_id]
    assert row['published_filename'] == relative
    assert row['sha256'] == digest
    assert not any(item.get('profile') == 'metadata_context_recovery' for item in row.get('local_patches', []) if isinstance(item, dict))

# WookaFR was manually validated in Nuvio and may move through a newer accepted
# content-addressed lineage (upstream Nuvio, adaptive repair, or immutable
# Desktop runtime compatibility). The invariant is the published bytes/hash and
# provenance, not one historical lineage label.
wookafr_relative = entries['wookafr']['filename']
wookafr_target = ROOT / wookafr_relative
assert wookafr_target.is_file(), wookafr_relative
wookafr_digest = hashlib.sha256(wookafr_target.read_bytes()).hexdigest()
wookafr_name = wookafr_target.name
wookafr_prefix = 'wookafr--'
wookafr_suffix = f'--{wookafr_digest[:16]}.js'
assert wookafr_name.startswith(wookafr_prefix) and wookafr_name.endswith(wookafr_suffix), wookafr_name
wookafr_source = wookafr_name[len(wookafr_prefix):-len(wookafr_suffix)]
assert wookafr_source in {'nuvio', 'adaptive-repair', 'desktop-runtime-v1'}, wookafr_source
assert MARKER not in wookafr_target.read_text(encoding='utf-8', errors='strict')
assert entries['wookafr']['enabled'] is True
assert provenance['wookafr']['published_filename'] == wookafr_relative
assert provenance['wookafr']['sha256'] == wookafr_digest

for relative in OLD:
    assert not (ROOT / relative).exists(), relative
print('deep repair rollback test passed')