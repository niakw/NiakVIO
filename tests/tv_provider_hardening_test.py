#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
overrides = json.loads((ROOT / 'provider-overrides.json').read_text(encoding='utf-8'))
policy = json.loads((ROOT / 'provider-type-policy.json').read_text(encoding='utf-8'))['providers']
manifest = json.loads((ROOT / 'manifest.json').read_text(encoding='utf-8'))['scrapers']
by_id = {str(row.get('id') or '').casefold(): row for row in manifest}
patches = overrides['provider_patches']

purstream_identity = 'scripts/provider_patches/purstream_tv_identity_v3.py'
papa_anime = 'scripts/provider_patches/papadustream_anime_tv_v1.py'
playable_first = 'scripts/provider_patches/nuvio_tv_playable_first_v1.py'
streamzo_identity = 'scripts/provider_patches/streamzo_source_identity_v2.py'
toflix_vf_v1 = 'scripts/provider_patches/toflix_explicit_vf_v1.py'
toflix_vf = 'scripts/provider_patches/toflix_explicit_vf_v2.py'

assert purstream_identity in patches['purstream'].get('patch_scripts', [])
pur_opts = patches['purstream'].get('patch_script_options', {}).get(purstream_identity, {})
assert float(pur_opts.get('duration_tolerance')) <= 0.35
assert int(pur_opts.get('max_probes')) <= 3
pur_source = (ROOT / purstream_identity).read_text(encoding='utf-8')
assert '#EXTINF' in pur_source and 'durationTolerance' in pur_source
assert 'episodic' in pur_source and 'series' in pur_source and 'anime' in pur_source

assert papa_anime in patches['papadustream'].get('patch_scripts', [])
assert patches['papadustream']['published_types'] == ['movie', 'tv', 'anime']
assert policy['papadustream']['supportedTypes'] == ['movie', 'tv', 'anime']
assert by_id['papadustream']['supportedTypes'] == ['movie', 'tv', 'anime']

for provider_id in ('4khdhubnew', 'animezey', 'vegamovies'):
    scripts = patches[provider_id].get('patch_scripts', [])
    assert playable_first in scripts, provider_id
    opts = patches[provider_id].get('patch_script_options', {}).get(playable_first, {})
    assert 1 <= int(opts.get('max_probes') or 0) <= 8, provider_id

streamzo_scripts = patches['streamzo'].get('patch_scripts', [])
assert streamzo_identity in streamzo_scripts
assert playable_first in streamzo_scripts
assert streamzo_scripts.index(streamzo_identity) < streamzo_scripts.index(playable_first)
identity_source = (ROOT / streamzo_identity).read_text(encoding='utf-8')
assert 'tokens' in identity_source and 'years' in identity_source
assert 'backtrack-les-revenants-2015' not in identity_source.lower()
assert '210702' not in identity_source

toflix_scripts = patches['toflix'].get('patch_scripts', [])
assert toflix_vf in toflix_scripts
assert toflix_vf_v1 not in toflix_scripts
toflix_opts = patches['toflix'].get('patch_script_options', {}).get(toflix_vf, {})
assert toflix_opts.get('require_french_host') is True
toflix_source = (ROOT / toflix_vf).read_text(encoding='utf-8')
assert 'NUVIO_TOFLIX_EXPLICIT_VF_V2' in toflix_source
assert 'VOSTFR' in toflix_source and 'return false' in toflix_source
assert 'frenchHost' in toflix_source and 'explicitVf' in toflix_source
assert 'out.language="fr"' in toflix_source
assert 'requireFrenchHost' in toflix_source
assert 'new URL' not in toflix_source
assert r'^https?:\/\/french\.' in toflix_source

playable_source = (ROOT / playable_first).read_text(encoding='utf-8')
assert '__native_fetch' in playable_source
assert '.text()' in playable_source
assert 'arrayBuffer' not in playable_source
for status in ('401', '403', '404', '410'):
    assert status in playable_source

print('Nuvio TV provider hardening policy tests passed')
