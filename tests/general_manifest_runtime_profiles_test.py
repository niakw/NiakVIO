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
original_data = json.loads(original)
original_caps = {
    str(key).casefold(): value
    for key, value in original_data.get('provider_capabilities', {}).items()
    if isinstance(value, dict)
}
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
        row = by_id[provider_id]
        filename = str(row.get('filename') or '')
        is_audit_quarantine = '--nuvio-audit-quarantine--' in filename
        bundle = (ROOT / filename).read_text(encoding='utf-8')
        is_scoped = 'NUVIO_CATALOGUE_SCOPE_QUARANTINE_V1' in bundle
        if caps[provider_id].get('strategy') == 'quarantined':
            if is_scoped:
                # A scoped quarantine is a partial runtime state: the wrapper
                # blocks only proven-bad scopes and may remain enabled for the
                # provider's still-valid media types.
                if row.get('enabled') is not False:
                    supported = row.get('supportedTypes') or []
                    if isinstance(supported, str):
                        supported = [supported]
                    assert any(str(value).strip() for value in supported), provider_id
            else:
                # A truly global quarantine remains fail-closed.
                assert row.get('enabled') is False, provider_id
                assert 'NUVIO_PROVIDER_QUARANTINE_V1' in bundle, provider_id
        if is_audit_quarantine:
            if is_scoped:
                # A scoped identity quarantine blocks only proven-bad
                # fixture/media scopes. The provider remains enabled whenever
                # at least one declared scope is still usable.
                if row.get('enabled') is not False:
                    supported = row.get('supportedTypes') or []
                    if isinstance(supported, str):
                        supported = [supported]
                    assert any(str(value).strip() for value in supported), provider_id
            else:
                # Legacy/global audit quarantine is still fail-closed.
                assert row.get('enabled') is False, provider_id
                assert 'NUVIO_PROVIDER_QUARANTINE_V1' in bundle, provider_id
            prior = original_caps.get(provider_id, {}).get('observed_origins')
            if isinstance(prior, list) and prior:
                assert caps[provider_id].get('observed_origins') == prior, (
                    provider_id,
                    prior,
                    caps[provider_id].get('observed_origins'),
                )
    assert d.get('provider_profile_generation', {}).get('provider_count') >= len(ids)
    print(f'general manifest runtime profiles test passed ({len(ids)} providers covered)')
finally:
    OVERRIDES.write_bytes(original)
