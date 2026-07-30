import importlib.util
from pathlib import Path

def load(path):
    spec=importlib.util.spec_from_file_location(path.stem,path)
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod
movix=load(Path('scripts/provider_patches/movix_multi_source.py'))
purstream=load(Path('scripts/provider_patches/purstream_bridge.py'))
m=movix.apply('module.exports={getStreams:function(){return Promise.resolve([])}};')
assert 'NUVIO_MOVIX_MULTI_SOURCE_V1' in m
assert '/api/purstream/movie/' in m and 'api.movix.fun' in m
p=purstream.apply('module.exports={getStreams:function(){return Promise.resolve([])}};')
assert 'NUVIO_PURSTREAM_BRIDGE_V1' in p
assert '/api/purstream/movie/' in p
hub=Path('scripts/resolve_provider_hubs.py').read_text()
assert 'dynamic_official_url' in hub and 'persist_official_site_without_api' in hub
print('provider specific adapters tests passed')
