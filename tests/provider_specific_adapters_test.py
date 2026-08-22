import importlib.util
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path('scripts').resolve()))
from provider_engine_normalizer import validate_provider_isolation


def load(path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


movix = load(Path('scripts/provider_patches/movix_multi_source.py'))
sanitizer = load(Path('scripts/provider_patches/stream_output_sanitizer.py'))
toflix = load(Path('scripts/provider_patches/toflix_official_endpoint.py'))

legacy = 'module.exports={getStreams:function(){return Promise.resolve([])}};\n/* NUVIO_MOVIX_MULTI_SOURCE_V1 */\nlegacy foreign provider bridge'
clean = movix.apply(legacy)
assert 'NUVIO_MOVIX_MULTI_SOURCE_V1' not in clean
assert 'legacy foreign provider bridge' not in clean
assert movix.apply(clean) == clean

cfg = json.loads(Path('provider-overrides.json').read_text(encoding='utf-8'))
# Purstream may retain generic runtime/domain configuration, but no active
# Purstream-specific repair implementation is allowed in the provider chain.
purstream_cfg = cfg['provider_patches']['purstream']
assert not [
    path for path in purstream_cfg.get('patch_scripts', [])
    if '/purstream_' in str(path)
]
assert not [
    path for path in purstream_cfg.get('patch_script_options', {})
    if '/purstream_' in str(path)
]
violations = validate_provider_isolation(cfg, Path('.').resolve())
assert violations == [], '\n'.join(violations)

with tempfile.TemporaryDirectory() as tmp:
    # macOS exposes /var as a symlink to /private/var. Resolve the synthetic
    # root just like validate_provider_isolation resolves each script path so
    # the containment check is platform-independent.
    root = Path(tmp).resolve()
    scripts = root / 'scripts' / 'provider_patches'
    scripts.mkdir(parents=True)
    (scripts / 'a.py').write_text('TARGET = "https://api.provider-b.example/v1/data"\n', encoding='utf-8')
    synthetic = {
        'provider_patches': {
            'provider-a': {'patch_scripts': ['scripts/provider_patches/a.py']},
            'provider-b': {'official_api': 'https://api.provider-b.example'},
        }
    }
    synthetic_violations = validate_provider_isolation(synthetic, root)
    assert len(synthetic_violations) == 1
    assert 'provider-a' in synthetic_violations[0] and 'provider-b' in synthetic_violations[0]

s = sanitizer.apply(
    'async function getStreams(){return []};module.exports={getStreams};',
    options={'blocked_hosts': ['fstream.top'], 'blocked_path_patterns': ['/troll/'], 'probe_direct_media': True, 'min_vod_duration_seconds': 60},
)
assert 'NUVIO_STREAM_OUTPUT_SANITIZER_V4' in s
assert 'fstream.top' in s
assert '/troll/' in s
assert 'minVodDurationSeconds' in s
assert 'total<config.minVodDurationSeconds' in s
assert sanitizer.apply(s, options={'blocked_hosts': ['fstream.top'], 'blocked_path_patterns': ['/troll/'], 'probe_direct_media': True, 'min_vod_duration_seconds': 60}) == s

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
print('provider-specific extraction adapters and isolation tests passed')
