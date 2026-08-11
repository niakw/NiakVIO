#!/usr/bin/env python3
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
overrides = json.loads((ROOT / 'provider-overrides.json').read_text())
hubs = json.loads((ROOT / 'provider-hubs.json').read_text())['providers']
manifest = json.loads((ROOT / 'manifest.json').read_text())['scrapers']
activation = json.loads((ROOT / 'provider-activation-lkg.json').read_text())
health_report = json.loads((ROOT / 'health-report.json').read_text())
type_policy = json.loads((ROOT / 'provider-type-policy.json').read_text())['providers']
by_id = {str(row['id']).lower(): row for row in manifest}
promotion_by_id = {
    str(row.get('id') or '').lower(): row
    for row in health_report.get('providers', [])
    if isinstance(row, dict) and str(row.get('id') or '').strip()
}
patches = overrides['provider_patches']
official = overrides['official_domain_hubs']

# Mainstream VF movie providers must remain represented as movie-capable
# providers. Activation follows the current deep proof policy: a provider may
# stay enabled, or this exact deep run must record a conclusive failed-gate
# decision. CI-inconclusive/network-only evidence may never silently shrink the
# catalogue. This mirrors validate_activation_preservation.py rather than
# hard-coding stale activation forever.
expected_vf_movie = {
    'purstream', 'frenchstream', 'streamzo', 'movix', 'coflix', 'wookafr',
    'flemmix', 'nakios', 'toflix', 'papadustream',
}
conclusive_disable_actions = {
    'published-disabled-failed-gates',
    'published-disabled-probation-or-performance',
    'disabled-sustained-outage',
}
for provider_id in sorted(expected_vf_movie):
    row = by_id[provider_id]
    assert 'movie' in row['supportedTypes'], provider_id
    if row['enabled'] is True:
        assert provider_id in activation['active_ids'], provider_id
        continue
    report = promotion_by_id[provider_id]
    action = str(report.get('action') or '')
    assert report.get('enabled') is False, provider_id
    assert action != 'published-disabled-ci-inconclusive-no-valid-runtime-evidence', provider_id
    assert action in conclusive_disable_actions, (provider_id, action)
    if action != 'disabled-sustained-outage':
        assert report.get('failed_gates'), provider_id

# User-confirmed mappings are exact and must survive future sync/repair jobs.
assert by_id['toflix']['supportedTypes'] == ['movie', 'tv', 'anime']
assert type_policy['toflix']['supportedTypes'] == ['movie', 'tv', 'anime']
assert by_id['papadustream']['supportedTypes'] == ['movie', 'tv']
assert patches['papadustream']['published_types'] == ['movie', 'tv']
assert type_policy['papadustream']['supportedTypes'] == ['movie', 'tv']

for provider_id in ('purstream', 'coflix', 'frenchstream', 'movix', 'nakios', 'streamzo'):
    assert by_id[provider_id]['supportedTypes'] == ['movie', 'tv', 'anime'], provider_id
    assert type_policy[provider_id]['supportedTypes'] == ['movie', 'tv', 'anime'], provider_id

# Goated is a manually confirmed Interstellar provider in Nuvio and its
# activation must likewise survive an isolated GitHub-runner failure.
assert by_id['goated']['enabled'] is True
assert 'movie' in by_id['goated']['supportedTypes']
assert 'goated' in activation['active_ids']

for provider_id in ('movix', 'coflix', 'flemmix'):
    assert by_id[provider_id]['supportsExternalPlayer'] is True, provider_id
# StreamZo historically exposed embeds. Once the globally audited direct-media
# bundle is promoted, every surviving output is a content-proven HLS/container
# and the provider must no longer advertise an external-player requirement.
if '--nuvio-tv-global--' in str(by_id['streamzo'].get('filename') or ''):
    assert by_id['streamzo']['supportsExternalPlayer'] is False
else:
    assert by_id['streamzo']['supportsExternalPlayer'] is True
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

# API-backed providers may not persist a new site address unless a meaningful
# API route is also validated. This controls domain mutation, not activation.
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
sanitizer_v5 = 'scripts/provider_patches/stream_output_sanitizer_v5.py'
sanitizer_v6 = 'scripts/provider_patches/stream_output_sanitizer_v6.py'
for provider_id in ('frenchstream', 'streamzo', 'movix', 'coflix', 'flemmix'):
    patch = patches[provider_id]
    scripts = patch.get('patch_scripts', [])
    assert recovery in scripts, provider_id
    if provider_id == 'coflix':
        # Coflix is NuvioTV-reachable while desktop/mobile remain blocked, so it
        # must use the explicit fail-closed successor. V6 embeds V5 and rejects
        # any all-URL probe overflow instead of publishing an unproven row.
        assert sanitizer_v6 in scripts, provider_id
        assert sanitizer_v5 not in scripts, provider_id
        strict = patch.get('patch_script_options', {}).get(sanitizer_v6, {})
        assert strict.get('probe_all_urls') is True, provider_id
        assert int(strict.get('max_probes') or 0) > 0, provider_id
    else:
        assert sanitizer_v5 in scripts, provider_id
    options = patch.get('patch_script_options', {}).get(recovery, {})
    expected_types = ['movie'] if provider_id == 'flemmix' else patch.get('published_types')
    assert options.get('types') == expected_types, provider_id
    assert 'fstream.top' in options.get('blocked_hosts', []), provider_id
    # A path name is not proof of invalid media. The response body must prove
    # `#EXTM3U`; HTML/403 responses and the known fake host remain rejected.
    assert '/troll/' not in options.get('blocked_path_patterns', []), provider_id

# Prefix collisions such as flemmix.me -> flemmix.men may never create .menn.
for path in (ROOT / 'providers').glob('*.js'):
    text = path.read_text(encoding='utf-8', errors='ignore')
    assert not re.search(r'flemmix\.men+n', text, re.I), path.name

promoter = (ROOT / 'scripts/promote_candidates.py').read_text()
assert 'policy_types or list(dict.fromkeys(curated_types + explicit_types))' in promoter
print('VF movie publication policy tests passed')
