#!/usr/bin/env python3
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
spec=spec_from_file_location('reapply',ROOT/'scripts/reapply_published_overrides.py')
mod=module_from_spec(spec); spec.loader.exec_module(mod)
assert mod.bump_provider_version('1.0.0')=='1.0.1'
assert mod.bump_provider_version('2.9.99')=='2.9.100'
assert mod.bump_provider_version('bad')=='1.0.1'
assert mod.configured_published_types({
    'provider_patches': {
        'demo': {'published_types': ['movie', 'tv', 'bogus', 'anime']}
    }
}, 'DEMO') == ['movie', 'tv', 'anime']

# Only the generated adaptive wrapper's historical hard-coded French claim may
# be removed. Genuine/native language metadata outside that wrapper must stay.
source=b'''const nativeRow={language:"fr",headers:{Referer:"https://native.example/"}};\n/* NUVIO_ADAPTIVE_RUNTIME_RECOVERY_V3:deadbeef */\n;(function(g,c){function recover(){return [{url:"https://cdn.example/a.m3u8",language:"fr",headers:{Referer:"https://site.example/"}}]}})(typeof globalThis!=="undefined"?globalThis:this,{});\n'''
cleaned,count=mod.strip_unproven_adaptive_language(source)
assert count==1
text=cleaned.decode('utf-8')
assert 'const nativeRow={language:"fr",headers:' in text
assert 'url:"https://cdn.example/a.m3u8",headers:' in text
assert 'url:"https://cdn.example/a.m3u8",language:"fr",headers:' not in text
cleaned_again,count_again=mod.strip_unproven_adaptive_language(cleaned)
assert count_again==0
assert cleaned_again==cleaned

print('reapplied provider versioning tests passed')
