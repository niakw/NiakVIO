#!/usr/bin/env python3
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
overrides = json.loads((ROOT / 'provider-overrides.json').read_text())
hubs = json.loads((ROOT / 'provider-hubs.json').read_text())['providers']
manifest = json.loads((ROOT / 'manifest.json').read_text())['scrapers']
by_id = {str(row['id']).lower(): row for row in manifest}
patches = overrides['provider_patches']
official = overrides['official_domain_hubs']

# Providers that are actually intended to answer mainstream VF movie requests.
expected_enabled_movie = {'purstream', 'frenchstream', 'streamzo', 'movix', 'coflix'}
for provider_id in expected_enabled_movie:
    row = by_id[provider_id]
    assert row['enabled'] is True, provider_id
    assert 'movie' in row['supportedTypes'], provider_id

# Unproven routes stay published but disabled; they may only return after a new
# current deep proof. This prevents address discovery alone from enabling them.
for provider_id in ('flemmix', 'wookafr', 'nakios', 'toflix'):
    assert by_id[provider_id]['enabled'] is False, provider_id

# Papadustream's implementation is series-only. Anime-only movie providers are
# tested separately and must not be counted as mainstream VF movie catalogues.
assert patches['papadustream']['published_types'] == ['tv']
assert by_id['papadustream']['supportedTypes'] == ['tv']

for provider_id in ('streamzo', 'movix', 'coflix', 'flemmix'):
    assert by_id[provider_id]['supportsExternalPlayer'] is True, provider_id
assert 'movie' in by_id['frenchstream']['supportedTypes']
assert not ({'dahmermovies', 'dahmermovies-tv'} & set(by_id))
assert not list((ROOT / 'providers').glob('dahmermovies*.js'))

# A hub/Telegram page is a discovery source, never a terminal provider route.
assert hubs['flemmix']['hub'].rstrip('/') != hubs['flemmix']['direct'].rstrip('/')
assert hubs['coflix']['hub'].rstrip('/') != hubs['coflix']['direct'].rstrip('/')
assert hubs['flemmix']['direct'].startswith('https://flemmix.')
assert hubs['coflix']['direct'].startswith('https://coflix.')
for provider_id in ('frenchstream', 'coflix', 'streamzo', 'flemmix'):
    assert hubs[provider_id].get('terminal_markers'), provider_id

# API-backed providers may not persist or activate a new site address unless a
# meaningful API route is also validated. A generic 404 is not API proof.
for provider_id in ('purstream', 'movix', 'nakios'):
    cfg = official[provider_id]
    assert cfg.get('require_api_validation') is True, provider_id
    assert cfg.get('persist_official_site_without_api') is False, provider_id
    assert 404 not in cfg.get('api_success_statuses', []), provider_id
    if provider_id == 'movix':
        assert cfg.get('api_route_discovery') is True, provider_id
        assert not cfg.get('api_probe_routes'), provider_id
        assert 'fstream' in cfg.get('obsolete_route_tokens', []), provider_id
    else:
        assert cfg.get('api_probe_routes'), provider_id

recovery = 'scripts/provider_patches/vf_catalogue_recovery.py'
for provider_id in ('frenchstream', 'streamzo', 'movix', 'coflix', 'flemmix'):
    patch = patches[provider_id]
    assert recovery in patch.get('patch_scripts', []), provider_id
    options = patch.get('patch_script_options', {}).get(recovery, {})
    expected_types = ['movie'] if provider_id == 'flemmix' else patch.get('published_types')
    assert options.get('types') == expected_types, provider_id
    assert 'fstream.top' in options.get('blocked_hosts', []), provider_id
    assert '/troll/' in options.get('blocked_path_patterns', []), provider_id

# Prefix collisions such as flemmix.me -> flemmix.men may never create .menn.
for path in (ROOT / 'providers').glob('*.js'):
    text = path.read_text(encoding='utf-8', errors='ignore')
    assert not re.search(r'flemmix\.men+n', text, re.I), path.name

promoter = (ROOT / 'scripts/promote_candidates.py').read_text()
assert 'policy_types or list(dict.fromkeys(curated_types + explicit_types))' in promoter
print('VF movie publication policy tests passed')
