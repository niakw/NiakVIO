#!/usr/bin/env python3
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OVERRIDES = ROOT / 'provider-overrides.json'

# This regression exercises the real generator, but a repository test may not
# leave generated runtime-profile state behind. Release hashes are produced
# inside npm test before the final regressions, so leaking this mutation makes a
# successful test command corrupt the working tree and invalidates integrity.
original = OVERRIDES.read_bytes()
try:
    subprocess.run(
        ['python3', str(ROOT / 'scripts/build_provider_runtime_profiles.py')],
        check=True,
        cwd=ROOT,
    )
    d = json.loads(OVERRIDES.read_text())
    m = json.loads((ROOT / 'manifest.json').read_text())
    ids = {str(x.get('id')).casefold() for x in m.get('scrapers', []) if x.get('id')}
    caps_raw = d.get('provider_capabilities', {})
    caps = {str(key).casefold(): value for key, value in caps_raw.items() if isinstance(value, dict)}
    missing = sorted(ids - set(caps))
    assert not missing, f'missing capability profiles: {missing}'
    valid = {
        'iframe_player',
        'mixed_embed_resolver',
        'api_stream_resolver',
        'direct_media',
        'html_scraper',
        'official_domain_hub',
        'quarantined',
    }
    bad = sorted(
        (provider_id, caps[provider_id].get('strategy'))
        for provider_id in ids
        if caps[provider_id].get('strategy') not in valid
    )
    assert not bad, bad
    by_id = {
        str(row.get('id')).casefold(): row
        for row in m.get('scrapers', [])
        if row.get('id')
    }
    for provider_id in ids:
        if caps[provider_id].get('strategy') != 'quarantined':
            continue
        row = by_id[provider_id]
        assert row.get('enabled') is False, provider_id
        bundle = (ROOT / str(row.get('filename') or '')).read_text(encoding='utf-8')
        assert 'NUVIO_PROVIDER_QUARANTINE_V1' in bundle, provider_id
    assert d.get('provider_profile_generation', {}).get('provider_count') >= len(ids)
    print(f'general manifest runtime profiles test passed ({len(ids)} providers covered)')
finally:
    OVERRIDES.write_bytes(original)
