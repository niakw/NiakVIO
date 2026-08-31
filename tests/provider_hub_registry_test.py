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
        }
    }
}
resolver.update_provider_patch(movix_config, 'movix', hubs['movix'], 'https://movix.example/', 'https://api.movix.example', {})
assert movix_config['provider_patches']['movix']['fixed_endpoint']['api'] == 'https://api.movix.example'
assert movix_config['provider_patches']['movix']['fixed_endpoint']['referer'] == 'https://movix.example/'
assert hubs['movix']['hub'] == 'https://movix.online/'
assert resolver.host(hubs['movix']['direct_fallback']) == 'movix.fun'
assert 'fstream.top' in hubs['movix']['blocked_hosts']

movix_html = '<a href="https://movix.fun/">Accéder à Movix</a>'
movix_candidates, preferred = resolver.choose_official('movix', hubs['movix'], hubs['movix']['hub'], movix_html)
assert preferred == 'https://movix.fun'
assert movix_candidates[0]['score'] >= 80

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
assert resolver._seed_known_candidates(fallback_authority_cfg, authority_history) == []

lkg_only_cfg = {'hub': None, 'sources': [], 'direct_candidates': []}
lkg_seed = resolver._seed_known_candidates(lkg_only_cfg, authority_history)
assert [row['source_type'] for row in lkg_seed] == ['history_lkg']

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
assert sync.index('resolve_provider_hubs.py') < sync.index('discover_candidates.py')
assert 'finalize_upstream_lkg.py' in sync
assert '--apply' in sync, 'only the canonical ARCHI2 pipeline may apply hub/domain changes'
assert '--apply' not in domain_refresh
assert 'git push' not in domain_refresh and 'git commit' not in domain_refresh
assert 'provider-domain-history.json' in domain_refresh
assert 'git diff --exit-code' in domain_refresh
assert 'upload-artifact' in domain_refresh

print('provider hub registry tests passed')