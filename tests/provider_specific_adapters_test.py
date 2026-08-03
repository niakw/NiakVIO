import importlib.util
from pathlib import Path


def load(path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


movix = load(Path('scripts/provider_patches/movix_multi_source.py'))
purstream = load(Path('scripts/provider_patches/purstream_bridge.py'))
sanitizer = load(Path('scripts/provider_patches/stream_output_sanitizer.py'))
toflix = load(Path('scripts/provider_patches/toflix_official_endpoint.py'))

legacy = 'module.exports={getStreams:function(){return Promise.resolve([])}};\n/* NUVIO_MOVIX_MULTI_SOURCE_V1 */\nlegacy purstream bridge'
clean = movix.apply(legacy)
assert 'NUVIO_MOVIX_MULTI_SOURCE_V1' not in clean
assert 'legacy purstream bridge' not in clean
assert movix.apply(clean) == clean

p = purstream.apply('module.exports={getStreams:function(){return Promise.resolve([])}};')
assert 'NUVIO_PURSTREAM_BRIDGE_V1' in p
assert '/api/purstream/movie/' in p

s = sanitizer.apply(
    'async function getStreams(){return []};module.exports={getStreams};',
    options={'blocked_hosts': ['fstream.top'], 'probe_direct_media': True},
)
assert 'NUVIO_STREAM_OUTPUT_SANITIZER_V2' in s
assert 'fstream.top' in s
assert sanitizer.apply(s, options={'blocked_hosts': ['fstream.top'], 'probe_direct_media': True}) == s

t = toflix.apply('var _cachedEndpoint=null;function detectToflixEndpoint(){return Promise.resolve({})}module.exports={getStreams:async()=>[]};')
assert 'NUVIO_TOFLIX_OFFICIAL_ENDPOINT_V1' in t
assert 'tfx05.lol' in t

hub = Path('scripts/resolve_provider_hubs.py').read_text()
assert 'provider-hubs.json' in hub
assert 'latest_telegram_domain' in hub
assert 'direct_fallback' in hub
assert 'persist_official_site_without_api' in hub
assert 'provider-domain-history.json' in hub
assert 'search_engine_urls' in hub
assert 'telegram_links' in hub
assert 'retained_last_known_good' in hub
print('provider specific adapters tests passed')
