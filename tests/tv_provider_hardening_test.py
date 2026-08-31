#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
overrides = json.loads((ROOT / 'provider-overrides.json').read_text(encoding='utf-8'))
policy = json.loads((ROOT / 'provider-type-policy.json').read_text(encoding='utf-8'))['providers']
manifest = json.loads((ROOT / 'manifest.json').read_text(encoding='utf-8'))['scrapers']
by_id = {str(row.get('id') or '').casefold(): row for row in manifest}
patches = overrides['provider_patches']

papa_anime = 'scripts/provider_patches/papadustream_anime_tv_v1.py'
playable_first = 'scripts/provider_patches/nuvio_tv_playable_first_v1.py'
toflix_vf_v1 = 'scripts/provider_patches/toflix_explicit_vf_v1.py'
toflix_vf = 'scripts/provider_patches/toflix_explicit_vf_v2.py'

# Media identity/presentation is Core/capability safety, never a Purstream-only
# exception. Provider-specific Purstream media repair scripts are forbidden from
# the active provider chain; generic compatibility/domain configuration may stay.
purstream_scripts = [str(value) for value in patches['purstream'].get('patch_scripts', [])]
assert not [path for path in purstream_scripts if '/purstream_' in path], purstream_scripts
purstream_options = patches['purstream'].get('patch_script_options', {})
assert not [path for path in purstream_options if '/purstream_' in str(path)], purstream_options
runtime_safety_source = (ROOT / 'scripts/provider_patches/runtime_capability_media_safety_v4.py').read_text(encoding='utf-8')
assert 'field-safety-v7-stream-scoped-p2p-vod-duration' in runtime_safety_source
assert 'collisionFixtures' in runtime_safety_source

assert papa_anime in patches['papadustream'].get('patch_scripts', [])
assert patches['papadustream']['published_types'] == ['movie', 'tv', 'anime']
assert policy['papadustream']['supportedTypes'] == ['movie', 'tv', 'anime']
assert by_id['papadustream']['supportedTypes'] == ['movie', 'tv', 'anime']

for provider_id in ('4khdhubnew', 'animezey', 'vegamovies'):
    scripts = patches[provider_id].get('patch_scripts', [])
    assert playable_first in scripts, provider_id
    opts = patches[provider_id].get('patch_script_options', {}).get(playable_first, {})
    assert 1 <= int(opts.get('max_probes') or 0) <= 8, provider_id

# StreamZo catalogue/identity recovery is Core-owned. Provider-local
# streamzo_* recovery scripts are forbidden; only generic capability/runtime
# modules may remain in its provider chain.
streamzo_scripts = [str(value) for value in patches['streamzo'].get('patch_scripts', [])]
assert not [path for path in streamzo_scripts if '/streamzo_' in path], streamzo_scripts
streamzo_options = patches['streamzo'].get('patch_script_options', {})
assert not [path for path in streamzo_options if '/streamzo_' in str(path)], streamzo_options
assert playable_first in streamzo_scripts

streamzo_capability = overrides['provider_capabilities']['streamzo']
assert streamzo_capability['strategy'] == 'mixed_embed_resolver'
assert streamzo_capability['request_type_aliases'] == {'anime': 'tv'}
assert streamzo_capability['identity_request_source'] == 'original_nuvio_request'
catalogue_core = 'scripts/provider_patches/global_catalogue_alias_recovery_v2.py'
catalogue_opts = streamzo_options.get(catalogue_core, {})
assert catalogue_opts.get('detail_id_attributes') == ['data-film-id']
assert catalogue_opts.get('mirror_routes') == ['/api/mirrors/film/{id}']
assert catalogue_opts.get('mirror_types') == ['movie', 'anime']
assert catalogue_opts.get('mirror_allow_episodic') is False

toflix_scripts = patches['toflix'].get('patch_scripts', [])
assert toflix_vf in toflix_scripts
assert toflix_vf_v1 not in toflix_scripts
toflix_opts = patches['toflix'].get('patch_script_options', {}).get(toflix_vf, {})
assert toflix_opts.get('require_french_host') is True
toflix_source = (ROOT / toflix_vf).read_text(encoding='utf-8')
assert 'NUVIO_TOFLIX_EXPLICIT_VF_V2' in toflix_source
assert 'VOSTFR' in toflix_source and 'return false' in toflix_source
assert 'frenchHost' in toflix_source and 'explicitVf' in toflix_source
assert 'out.language="fr"' in toflix_source
assert 'requireFrenchHost' in toflix_source
assert 'new URL' not in toflix_source
assert r'^https?:\/\/french\.' in toflix_source

playable_source = (ROOT / playable_first).read_text(encoding='utf-8')
assert '__native_fetch' in playable_source
assert '.text()' in playable_source
assert 'arrayBuffer' not in playable_source
assert 'followRedirects' in playable_source
assert '__NUVIO_TV_RUNTIME__' in playable_source
assert 'fourArgNative' in playable_source
for status in ('401', '403', '404', '410'):
    assert status in playable_source

# Runtime-contract regression: Desktop/Mobile also expose __native_fetch, so that
# symbol alone must never activate the TV probe. The official Desktop/Mobile
# fetch bridge forwards a fifth followRedirects argument; NuvioTV uses the
# four-argument native bridge and wraps it with options.signal handling.
spec = importlib.util.spec_from_file_location(
    'nuvio_tv_playable_first_test_module', ROOT / playable_first
)
assert spec is not None and spec.loader is not None
playable_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(playable_module)

base_provider = """
globalThis.__native_fetch=function(){return JSON.stringify({ok:true,status:200,statusText:'OK',url:'https://media.example/test.m3u8',headers:{'content-type':'application/vnd.apple.mpegurl'},body:'#EXTM3U\\n#EXT-X-ENDLIST'});};
let probeCount=0;
__FETCH_IMPL__
module.exports={getStreams:async()=>[{title:'Runtime scope control',url:'https://media.example/test.m3u8'}]};
"""

desktop_fetch = """
globalThis.fetch=async function(url,options){
  options=options||{};
  var method=(options.method||'GET').toUpperCase();
  var headers=options.headers||{};
  var body=options.body||'';
  var followRedirects=options.redirect!=='manual';
  probeCount++;
  var result=__native_fetch(url,method,JSON.stringify(headers),body,followRedirects);
  var parsed=JSON.parse(result);
  return {status:parsed.status,headers:{get:function(name){return parsed.headers[name.toLowerCase()]||null;}},text:function(){return Promise.resolve(parsed.body);}};
};
"""

tv_fetch = """
globalThis.fetch=async function(url,options){
  options=options||{};
  var method=(options.method||'GET').toUpperCase();
  var headers=options.headers||{};
  var body=options.body||'';
  var signal=options.signal||null;
  if(signal&&signal.aborted)throw new Error('aborted');
  probeCount++;
  var result=__native_fetch(url,method,JSON.stringify(headers),body);
  var parsed=JSON.parse(result);
  return {status:parsed.status,headers:{get:function(name){return parsed.headers[name.toLowerCase()]||null;}},text:function(){return Promise.resolve(parsed.body);}};
};
"""


def execute_runtime_case(fetch_impl: str) -> dict:
    provider_source = base_provider.replace('__FETCH_IMPL__', fetch_impl)
    patched = playable_module.apply(
        provider_source,
        options={'max_probes': 1, 'timeout_ms': 1500},
    )
    program = patched + """
;(async function(){
  const rows=await module.exports.getStreams();
  console.log(JSON.stringify({count:rows.length,probeCount:probeCount}));
})().catch(function(error){console.error(error&&error.stack||error);process.exitCode=1;});
"""
    with tempfile.NamedTemporaryFile(
        mode='w', suffix='.cjs', encoding='utf-8', delete=False
    ) as handle:
        handle.write(program)
        path = Path(handle.name)
    try:
        completed = subprocess.run(
            ['node', str(path)],
            text=True,
            capture_output=True,
            timeout=10,
            check=False,
        )
    finally:
        path.unlink(missing_ok=True)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    lines = [line.strip() for line in completed.stdout.splitlines() if line.strip()]
    assert lines, completed.stdout + completed.stderr
    return json.loads(lines[-1])


desktop_result = execute_runtime_case(desktop_fetch)
assert desktop_result == {'count': 1, 'probeCount': 0}, desktop_result

tv_result = execute_runtime_case(tv_fetch)
assert tv_result == {'count': 1, 'probeCount': 1}, tv_result

# Existing bundles already carrying the original V1 marker must be upgraded in
# place. Appending another wrapper would leave the unsafe first wrapper active.
legacy_wrapped = (
    '/* NUVIO_TV_PLAYABLE_FIRST_V1 */\n'
    + playable_module.LEGACY_TV_PREDICATE
    + '\nmodule.exports={getStreams:async()=>[]};\n'
)
upgraded = playable_module.apply(legacy_wrapped)
assert playable_module.LEGACY_TV_PREDICATE not in upgraded
assert playable_module.TV_PREDICATE in upgraded
assert upgraded.count('NUVIO_TV_PLAYABLE_FIRST_V1') == 1

print('Nuvio TV provider hardening policy tests passed')
