import copy
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

spec = importlib.util.spec_from_file_location('resolver', ROOT / 'scripts' / 'resolve_provider_hubs.py')
resolver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(resolver)

config = json.loads((ROOT / 'provider-overrides.json').read_text())
hubs = resolver.merge_hub_registry(config)
for provider_id in ('frenchstream', 'movix', 'nakios', 'toflix', 'flemmix', 'wookafr', '4khdhub', 'movies4u'):
    assert provider_id in hubs, provider_id
    assert hubs[provider_id].get('direct_fallback'), provider_id
    assert hubs[provider_id].get('sources') or hubs[provider_id].get('direct_candidates'), provider_id

# Frenchstream and Movix have separate official address sources. fstream.top is
# only a blocked output/player host and must never become a terminal site.
assert hubs['frenchstream']['hub'] == 'https://fstream.org/'
assert {resolver.host(url) for url in hubs['frenchstream']['direct_candidates']} >= {'fs16.lol', 'fs03.lol'}
assert 'fstream.top' in hubs['frenchstream']['blocked_hosts']
assert resolver.same_brand('frenchstream', 'https://fs17.lol/', hubs['frenchstream'])

# Domain rollbacks/rotations must not create replacement cycles.
cycle_config = {
    'provider_patches': {
        'frenchstream': {
            'official_site': 'https://fs16.lol/',
            'replacements': {'fs03.lol': 'fs16.lol'},
            'runtime_domain_replacements': {'fs03.lol': 'fs16.lol'},
            'required_values': ['fs16.lol'],
        }
    }
}
cycle_hub = copy.deepcopy(hubs['frenchstream'])
resolver.update_provider_patch(cycle_config, 'frenchstream', cycle_hub, 'https://fs03.lol/', None, {})
cycle_patch = cycle_config['provider_patches']['frenchstream']
assert 'fs03.lol' not in cycle_patch['replacements']
assert cycle_patch['replacements']['fs16.lol'] == 'fs03.lol'
assert cycle_patch['required_values'] == []

# Provider-specific endpoint bootstraps follow the same resolved domain.
toflix_config = {
    'provider_patches': {
        'toflix': {
            'official_site': 'https://tfx05.lol/',
            'replacements': {'toflix.site': 'tfx05.lol'},
            'runtime_domain_replacements': {'toflix.site': 'tfx05.lol'},
            'required_values': ['tfx05.lol'],
            'patch_scripts': ['scripts/provider_patches/toflix_official_endpoint.py'],
            'patch_script_options': {},
        }
    }
}
resolver.update_provider_patch(toflix_config, 'toflix', hubs['toflix'], 'https://tfx06.lol/', 'https://api.tfx06.lol', {})
toflix_patch = toflix_config['provider_patches']['toflix']
toflix_options = toflix_patch['patch_script_options']['scripts/provider_patches/toflix_official_endpoint.py']
assert toflix_options['site'] == 'https://tfx06.lol'
assert toflix_options['fallback_api'] == 'https://api.tfx06.lol/toflix_api.php'

movix_config = {
    'provider_patches': {
        'movix': {
            'official_site': 'https://movix.fun/',
            'replacements': {'movix.cash': 'movix.fun'},
            'runtime_domain_replacements': {'movix.cash': 'movix.fun'},
            'required_values': ['movix.fun'],
            'fixed_endpoint': {'resolver_function': 'detectApi', 'api': 'https://api.movix.fun', 'referer': 'https://movix.fun/'},
            'api_recipe': {'base': 'https://api.movix.fun', 'referer': 'https://movix.fun/', 'movieRoute': '/api/catalog/movie/{id}'},
            'patch_scripts': ['scripts/provider_patches/vf_catalogue_recovery.py'],
            'patch_script_options': {
                'scripts/provider_patches/vf_catalogue_recovery.py': {
                    'strategy': 'api_fixed',
                    'base_url': 'https://movix.fun',
                    'api_url': 'https://api.movix.fun',
                }
            },
        }
    }
}
resolver.update_provider_patch(movix_config, 'movix', hubs['movix'], 'https://movix.example/', 'https://api.movix.example', {})
movix_patch = movix_config['provider_patches']['movix']
assert movix_patch['fixed_endpoint']['api'] == 'https://api.movix.example'
assert movix_patch['fixed_endpoint']['referer'] == 'https://movix.example/'
assert movix_patch['api_recipe']['base'] == 'https://api.movix.example'
assert movix_patch['api_recipe']['referer'] == 'https://movix.example/'
movix_recovery = movix_patch['patch_script_options']['scripts/provider_patches/vf_catalogue_recovery.py']
assert movix_recovery['base_url'] == 'https://movix.example'
assert movix_recovery['api_url'] == 'https://api.movix.example'
assert hubs['movix']['hub'] == 'https://movix.online/'
assert resolver.host(hubs['movix']['direct_fallback']) == 'movix.fun'
assert 'fstream.top' in hubs['movix']['blocked_hosts']

movix_html = '<a href="https://movix.fun/">Accéder à Movix</a>'
movix_candidates, preferred = resolver.choose_official('movix', hubs['movix'], hubs['movix']['hub'], movix_html)
assert preferred == 'https://movix.fun'
assert movix_candidates and isinstance(movix_candidates[0], dict), movix_candidates
assert movix_candidates[0].get('score') is not None, movix_candidates
assert movix_candidates[0]['score'] >= 80

# Purstream's wiki can render its current address dynamically. The official
# Telegram announcements are a second authoritative route source, so a hub HTML
# placeholder cannot strand the resolver on an old terminal.
purstream_sources = hubs['purstream'].get('sources') or []
assert any(
    source.get('type') == 'telegram_public'
    and str(source.get('url') or '').rstrip('/') == 'https://t.me/s/purstreamm'
    for source in purstream_sources
)

# Root-only API discovery must not erase a proven provider base path.
purstream_route_config = {
    'provider_patches': {
        'purstream': {
            'official_site': 'https://purstream.id',
            'official_api': 'https://api.purstream.id/api/v1',
            'replacements': {},
            'runtime_domain_replacements': {},
            'fixed_endpoint': {
                'resolver_function': 'detectPurstreamDomain',
                'api': 'https://api.purstream.id/api/v1',
                'referer': 'https://purstream.id/',
            },
            'api_recipe': {
                'base': 'https://api.purstream.id/api/v1',
                'referer': 'https://purstream.id/',
                'movieRoute': '/media/{id}/sheet',
            },
        }
    }
}
resolver.update_provider_patch(
    purstream_route_config,
    'purstream',
    hubs['purstream'],
    'https://purstream.id',
    'https://api.purstream.id',
    {},
)
purstream_route_patch = purstream_route_config['provider_patches']['purstream']
assert purstream_route_patch['official_api'] == 'https://api.purstream.id/api/v1'
assert purstream_route_patch['fixed_endpoint']['api'] == 'https://api.purstream.id/api/v1'
assert purstream_route_patch['api_recipe']['base'] == 'https://api.purstream.id/api/v1'

# Telegram selection must use the highest message id rather than document
# position. This remains correct with pinned or reordered messages.
wooka_html = '''
<div class="tgme_widget_message" data-post="Wookafr2/120">
  <div>Wooka : nouvelle adresse officielle</div>
  <a href="https://wookafr.old/">Accéder au site</a>
</div>
<div class="tgme_widget_message" data-post="Wookafr2/131">
  <div>Wooka : URL du nouveau site officiel</div>
  <a href="https://wookafr.center/">Ouvrir Wooka</a>
</div>
<div class="tgme_widget_message" data-post="Wookafr2/125">
  <div>Partenaire externe</div>
  <a href="https://unrelated.example/">Voir le partenaire</a>
</div>
'''
wooka_candidates, preferred = resolver.choose_official('wookafr', hubs['wookafr'], hubs['wookafr']['hub'], wooka_html)
assert preferred == 'https://wookafr.center'
assert wooka_candidates and isinstance(wooka_candidates[0], dict), wooka_candidates
assert wooka_candidates[0].get('message_id') is not None, wooka_candidates
assert wooka_candidates[0]['message_id'] == 131
assert all(resolver.host(row['url']) != 'unrelated.example' for row in wooka_candidates)


# Six curated address contracts from hub_6.xlsx must remain explicit and
# independently testable. Hubs are discovery sources; only terminal sites can
# become provider routes.
for provider_id in ('1shows', 'allwish', 'anidb', 'cinefreak', 'moonflix', 'zinkmovies'):
    assert provider_id in hubs, provider_id
    assert hubs[provider_id].get('sources'), provider_id
    assert hubs[provider_id].get('direct_candidates'), provider_id

assert hubs['1shows']['hub'] == 'https://flixnetwork.is/'
assert hubs['1shows']['direct_fallback'] == 'https://1flixto.icu/'
one_shows_html = '''
<article class="tile" data-domain="1flixto.icu" data-search="1flixto.icu 1flix.to">
  <span class="tile-domain">1flixto.icu</span>
  <p class="tile-alt">Alternative to <b>1flix.to</b></p>
  <a class="t-visit" href="https://1flixto.icu">Visit →</a>
</article>
'''
one_shows_candidates, preferred = resolver.choose_official(
    '1shows', hubs['1shows'], hubs['1shows']['hub'], one_shows_html
)
assert preferred == 'https://1flixto.icu'
assert resolver.same_brand('1shows', preferred, hubs['1shows'])

assert hubs['allwish']['resolver'] == 'telegram_description'
allwish_html = '''
<div class="tgme_channel_info">
  <div class="tgme_channel_info_description">All-Wish official domain:
    <a href="https://all-wish.me/">https://all-wish.me/</a>
  </div>
</div>
<div class="tgme_widget_message" data-post="allwishme/44">
  <div>Latest community post</div>
  <a href="https://example.org/">example.org</a>
</div>
'''
_allwish_candidates, preferred = resolver.choose_official(
    'allwish', hubs['allwish'], hubs['allwish']['hub'], allwish_html
)
assert preferred == 'https://all-wish.me'

assert hubs['anidb']['hub'] == 'https://tbcpl.click/'
anidb_html = '''
<a data-category="anime" data-name="anidb" href="https://anidb.pics"
   target="_blank" title="AniDB"><span>anidb.pics</span></a>
'''
_anidb_candidates, preferred = resolver.choose_official(
    'anidb', hubs['anidb'], hubs['anidb']['hub'], anidb_html
)
assert preferred == 'https://anidb.pics'

assert hubs['cinefreak']['resolver'] == 'latest_telegram_domain'
cinefreak_html = '''
<div class="tgme_widget_message" data-post="cinefreaktop/90">
  <div>CineFreak : nouvelle adresse officielle</div>
  <a href="https://example.invalid/">example.invalid</a>
  <a href="https://cinefreak.ch/">cinefreak.ch</a>
  <a href="https://example.org/">example.org</a>
</div>
'''
cinefreak_candidates, preferred = resolver.choose_official(
    'cinefreak', hubs['cinefreak'], hubs['cinefreak']['hub'], cinefreak_html
)
assert preferred == 'https://cinefreak.ch'
assert cinefreak_candidates and isinstance(cinefreak_candidates[0], dict), cinefreak_candidates
assert cinefreak_candidates[0].get('url') is not None, cinefreak_candidates
assert resolver.host(cinefreak_candidates[0]['url']) == 'cinefreak.ch'

assert hubs['moonflix']['resolver'] == 'latest_telegram_domain'
moonflix_html = '''
<div class="tgme_widget_message" data-post="Moonflix_official_Channel/120">
  <div>MoonFlix : URL du nouveau site officiel</div>
  <a href="https://moonflix.website/browse">MoonFlix</a>
</div>
'''
_moonflix_candidates, preferred = resolver.choose_official(
    'moonflix', hubs['moonflix'], hubs['moonflix']['hub'], moonflix_html
)
assert preferred == 'https://moonflix.website/browse'

assert hubs['zinkmovies']['hub'] == 'https://zinkmovies.org/'
zink_html = '<a href="https://new3.zinkmovies.mobi/" rel="nofollow noindex">Click Here to Enter</a>'
_zink_candidates, preferred = resolver.choose_official(
    'zinkmovies', hubs['zinkmovies'], hubs['zinkmovies']['hub'], zink_html
)
assert preferred == 'https://new3.zinkmovies.mobi'

# Route authority order: hub > explicit direct > search/LKG. Historical
# routes are never allowed to override a declared source.
authority_history = {
    'current': {'url': 'https://stale.example/', 'host': 'stale.example'}
}
hub_authority_cfg = {
    'hub': 'https://hub.example/',
    'sources': [{'type': 'hub', 'url': 'https://hub.example/', 'priority': 110}],
    'direct_candidates': ['https://direct.example/'],
    'direct_fallback': 'https://direct.example/',
}
assert resolver.has_authoritative_hub_source(hub_authority_cfg)
assert resolver._seed_known_candidates(hub_authority_cfg, authority_history) == []

direct_authority_cfg = {
    'hub': None,
    'sources': [],
    'direct_candidates': ['https://direct.example/'],
    'direct_fallback': 'https://direct.example/',
}
assert resolver.has_authoritative_direct_source(direct_authority_cfg)
direct_seed = resolver._seed_known_candidates(direct_authority_cfg, authority_history)
assert [row['source_type'] for row in direct_seed] == ['curated_direct']
assert all(row['source_type'] != 'history_lkg' for row in direct_seed)

fallback_authority_cfg = {
    'hub': None,
    'sources': [],
    'direct_candidates': [],
    'direct_fallback': 'https://direct.example/',
}
assert resolver.has_authoritative_direct_source(fallback_authority_cfg)
fallback_seed = resolver._seed_known_candidates(fallback_authority_cfg, authority_history)
assert [row['url'] for row in fallback_seed] == ['https://direct.example']
assert all(row['source_type'] != 'history_lkg' for row in fallback_seed)

lkg_only_cfg = {'hub': None, 'sources': [], 'direct_candidates': []}
lkg_seed = resolver._seed_known_candidates(lkg_only_cfg, authority_history)
assert [row['source_type'] for row in lkg_seed] == ['history_lkg']

# A temporary authoritative-hub outage preserves the last published terminal as
# LKG without pretending it was freshly validated. This is the Purstream failure
# mode observed on Nuvio: dynamic/empty hub HTML must not become an empty route.
purstream_retained_cfg = copy.deepcopy(hubs['purstream'])
purstream_retained_cfg['_published_official_site'] = 'https://purstream.id'
assert resolver.retained_lkg_site('purstream', purstream_retained_cfg, {}) == 'https://purstream.id'
purstream_history = {
    'current': {
        'url': 'https://purstream.id',
        'host': 'purstream.id',
        'source_type': 'hub',
        'source': 'https://purstream.wiki/',
    }
}
assert resolver.retained_lkg_site('purstream', purstream_retained_cfg, purstream_history) == 'https://purstream.id'


# Discovery sources are not terminals, even when an official Telegram post names
# the hub itself with strong brand/address wording. This reproduces the
# 2026-09-01 Purstream contamination path exactly.
polluted_purstream_history = {
    'current': {
        'url': 'https://purstream.wiki',
        'host': 'purstream.wiki',
        'source_type': 'telegram_public',
        'source': 'https://t.me/s/purstreamm',
    }
}
assert resolver.retained_lkg_site(
    'purstream',
    purstream_retained_cfg,
    polluted_purstream_history,
) == 'https://purstream.id'

_original_telegram_links = resolver.telegram_links
try:
    resolver.telegram_links = lambda _document, _base: [{
        'url': 'https://purstream.wiki',
        'label': 'Purstream site officiel',
        'context': 'Purstream nouvelle adresse officielle',
        'message_id': 999,
        'document_index': 0,
    }]
    telegram_cfg = copy.deepcopy(hubs['purstream'])
    telegram_cfg['resolver'] = 'latest_telegram_domain'
    candidates, selected = resolver.choose_official(
        'purstream',
        telegram_cfg,
        'https://t.me/s/purstreamm',
        '<html></html>',
    )
    assert all(resolver.host(str(row.get('url') or '')) != 'purstream.wiki' for row in candidates)
    assert resolver.host(str(selected or '')) != 'purstream.wiki'
finally:
    resolver.telegram_links = _original_telegram_links

try:
    resolver.update_provider_patch(
        {'provider_patches': {'purstream': {}}},
        'purstream',
        purstream_retained_cfg,
        'https://purstream.wiki',
        None,
        {},
    )
except ValueError:
    pass
else:
    raise AssertionError('Purstream discovery hub must never be publishable as terminal')

# A successful fresh always replaces the current route. The former route is
# history only; it is never allowed to remain current after hub/direct moved.
fresh_history = {
    'current': {
        'url': 'https://old.example',
        'host': 'old.example',
        'source_type': 'history_lkg',
        'source': 'provider-domain-history.json',
    },
    'previous': [],
}
resolver.update_history_row(fresh_history, {
    'status': 'site_validated',
    'official_site': 'https://new.example',
    'selected_source_type': 'hub',
    'selected_source': 'https://hub.example/',
})
assert fresh_history['current']['url'] == 'https://new.example'
assert fresh_history['current']['source_type'] == 'hub'
assert fresh_history['current']['source'] == 'https://hub.example/'
assert fresh_history['previous'][0]['url'] == 'https://old.example'

direct_fresh_history = {
    'current': {
        'url': 'https://old-direct.example',
        'host': 'old-direct.example',
        'source_type': 'history_lkg',
        'source': 'provider-domain-history.json',
    },
    'previous': [],
}
resolver.update_history_row(direct_fresh_history, {
    'status': 'site_validated',
    'official_site': 'https://new-direct.example',
    'selected_source_type': 'curated_direct',
    'selected_source': 'provider-hubs.json',
})
assert direct_fresh_history['current']['url'] == 'https://new-direct.example'
assert direct_fresh_history['current']['source_type'] == 'curated_direct'
assert direct_fresh_history['previous'][0]['url'] == 'https://old-direct.example'

# Deep discovery uses Yandex first and DuckDuckGo as a bounded fallback.
engines = resolver.search_engine_urls('example provider')
assert engines[0][0] == 'yandex' and 'yandex.com/search/' in engines[0][1]
assert engines[1][0] == 'duckduckgo' and 'duckduckgo.com/html/' in engines[1][1]

# Search-only discoveries require two consecutive confirmations, while a hub,
# Telegram or curated source can be accepted immediately.
history = {}
confirmed, detail = resolver._apply_confirmation(history, 'https://example.test', 'search', 2)
assert not confirmed and detail['observed'] == 1
confirmed, detail = resolver._apply_confirmation(history, 'https://example.test', 'search', 2)
assert confirmed and detail['observed'] == 2
confirmed, detail = resolver._apply_confirmation(history, 'https://example.test', 'hub', 2)
assert confirmed and detail['required'] == 1

registry = json.loads((ROOT / 'provider-hubs.json').read_text())
history_registry = json.loads((ROOT / 'provider-domain-history.json').read_text())
assert registry.get('schema_version', 0) >= 3
assert history_registry.get('schema_version') == 1

# Hub-backed history must preserve provenance, not freeze today's terminal URL.
# The terminal may rotate at any time; the configured hub remains authoritative.
for provider_id in ('flemmix', '1shows', 'allwish', 'anidb', 'cinefreak', 'moonflix', 'zinkmovies'):
    current = ((history_registry.get('providers') or {}).get(provider_id) or {}).get('current') or {}
    assert current.get('url'), (provider_id, current)
    assert resolver.same_brand(provider_id, str(current['url']), hubs[provider_id]), (provider_id, current)
    authoritative_sources = {
        str(source.get('url') or '').rstrip('/')
        for source in hubs[provider_id].get('sources') or []
        if source.get('type') in {'hub', 'telegram_public', 'redirect'} and source.get('url')
    }
    assert str(current.get('source') or '').rstrip('/') in authoritative_sources, (provider_id, current)
    assert current.get('source_type') in {'hub', 'telegram_public', 'redirect', 'curated_official_hub'}, (provider_id, current)

assert 'dahmermovies' not in registry['providers']
assert 'dahmermovies-tv' not in registry['providers']
raw = json.dumps(registry, ensure_ascii=False).casefold()
for private_note_fragment in ('recherche yandex', 'premier bloc button', 'lien sur "click here"'):
    assert private_note_fragment not in raw
for provider_id, row in registry['providers'].items():
    assert isinstance(row, dict), provider_id
    assert row.get('sources') or row.get('direct_candidates') or row.get('search_queries'), provider_id
    for source in row.get('sources') or []:
        assert source.get('type') in {'hub', 'telegram_public', 'redirect', 'search'}, (provider_id, source)
        assert source.get('url') or source.get('query'), (provider_id, source)

sync = (ROOT / '.github' / 'workflows' / 'sync.yml').read_text()
domain_refresh = (ROOT / '.github' / 'workflows' / 'domain-refresh.yml').read_text()
# CORE Verify & Publish is validation/observation only. Authoritative
# domain mutation belongs exclusively to CORE Domain Refresh.
assert 'resolve_provider_hubs.py' in sync
assert '--mode deep' in sync
assert 'discover_candidates.py' not in sync
assert 'finalize_upstream_lkg.py' not in sync
assert '--apply' not in sync
assert '--apply' in domain_refresh, 'CORE Domain Refresh must apply validated route changes'
assert 'push origin HEAD:main' in domain_refresh and 'git commit' in domain_refresh
assert 'provider-domain-history.json' in domain_refresh
assert 'provider-overrides.json' in domain_refresh
assert 'git diff --exit-code' in domain_refresh
assert domain_refresh.count('gh workflow run sync.yml') == 1, 'route publication must trigger exactly one Provider Pipeline dispatch'
assert 'upload-artifact' in domain_refresh

print('provider hub registry tests passed')

# Security invariant: provider route state is a web/catalogue origin, never a
# downloadable executable, installer, disk image, archive, direct media or asset.
assert resolver.is_provider_terminal_site_url('https://provider.example/') is True
assert resolver.is_provider_terminal_site_url('https://provider.example/catalogue') is True
for unsafe in (
    'app.exe', 'setup.msi', 'bundle.msix', 'android.apk', 'android.xapk', 'ios.ipa',
    'mac.dmg', 'mac.pkg', 'linux.AppImage', 'linux.deb', 'linux.rpm',
    'disk.iso', 'disk.img', 'vm.vhdx', 'vm.qcow2', 'archive.zip', 'archive.7z',
    'script.ps1', 'script.sh', 'movie.m3u8', 'movie.mp4', 'logo.png', 'doc.pdf',
):
    assert resolver.is_provider_terminal_site_url('https://provider.example/' + unsafe) is False, unsafe
assert resolver.is_forbidden_terminal_content_type('application/octet-stream') is True
assert resolver.is_forbidden_terminal_content_type('application/vnd.android.package-archive') is True
assert resolver.is_forbidden_terminal_content_type('video/mp4') is True
assert resolver.is_forbidden_terminal_content_type('text/html; charset=utf-8') is False

stable_history = {
    'current': {
        'url': 'https://stable.example',
        'host': 'stable.example',
        'validated_at': '2026-08-30T12:00:00+00:00',
        'source_type': 'hub',
        'source': 'https://hub.example/',
    },
    'previous': [],
}
resolver.update_history_row(stable_history, {
    'status': 'site_validated',
    'official_site': 'https://stable.example',
    'selected_source_type': 'hub',
    'selected_source': 'https://hub.example/',
})
assert stable_history['current']['validated_at'] == '2026-08-30T12:00:00+00:00'

unsafe_config = {
    'provider_patches': {
        'demo': {
            'official_site': 'https://download.demo.example/app.apk',
            'replacements': {'demo.example': 'download.demo.example'},
            'runtime_domain_replacements': {'demo.example': 'download.demo.example'},
        }
    }
}
unsafe_hubs = {
    'demo': {
        'direct_candidates': ['https://demo.example/'],
    }
}
unsafe_history = {
    'demo': {
        'current': {
            'url': 'https://download.demo.example/app.apk',
            'host': 'download.demo.example',
            'source_type': 'history_lkg',
            'source': 'provider-domain-history.json',
        },
        'previous': [],
    }
}
sanitized = resolver.sanitize_unsafe_published_routes(unsafe_config, unsafe_hubs, unsafe_history)
assert sanitized and sanitized[0]['provider_id'] == 'demo'
assert unsafe_config['provider_patches']['demo']['official_site'] == 'https://demo.example'
assert unsafe_config['provider_patches']['demo']['replacements'] == {}
assert unsafe_config['provider_patches']['demo']['runtime_domain_replacements'] == {}
assert unsafe_history['demo']['current']['url'] == 'https://demo.example'
assert unsafe_history['demo']['current']['source_type'] == 'curated_direct'

print('unsafe terminal payloads must never become provider origins')
