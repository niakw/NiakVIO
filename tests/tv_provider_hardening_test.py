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

purstream_identity = 'scripts/provider_patches/purstream_tv_identity_v3.py'
papa_anime = 'scripts/provider_patches/papadustream_anime_tv_v1.py'
playable_first = 'scripts/provider_patches/nuvio_tv_playable_first_v1.py'
streamzo_identity = 'scripts/provider_patches/streamzo_source_identity_v3.py'
streamzo_public = 'scripts/provider_patches/streamzo_public_catalogue_v2.py'
toflix_vf_v1 = 'scripts/provider_patches/toflix_explicit_vf_v1.py'
toflix_vf = 'scripts/provider_patches/toflix_explicit_vf_v2.py'

assert purstream_identity in patches['purstream'].get('patch_scripts', [])
pur_opts = patches['purstream'].get('patch_script_options', {}).get(purstream_identity, {})
assert float(pur_opts.get('duration_tolerance')) <= 0.35
assert int(pur_opts.get('max_probes')) <= 3
pur_source = (ROOT / purstream_identity).read_text(encoding='utf-8')
assert '#EXTINF' in pur_source and 'durationTolerance' in pur_source
assert 'episodic' in pur_source and 'series' in pur_source and 'anime' in pur_source

assert papa_anime in patches['papadustream'].get('patch_scripts', [])
assert patches['papadustream']['published_types'] == ['movie', 'tv', 'anime']
assert policy['papadustream']['supportedTypes'] == ['movie', 'tv', 'anime']
assert by_id['papadustream']['supportedTypes'] == ['movie', 'tv', 'anime']

for provider_id in ('4khdhubnew', 'animezey', 'vegamovies'):
    scripts = patches[provider_id].get('patch_scripts', [])
    assert playable_first in scripts, provider_id
    opts = patches[provider_id].get('patch_script_options', {}).get(playable_first, {})
    assert 1 <= int(opts.get('max_probes') or 0) <= 8, provider_id

streamzo_scripts = patches['streamzo'].get('patch_scripts', [])
assert streamzo_public in streamzo_scripts
assert streamzo_identity in streamzo_scripts
assert streamzo_scripts.index(streamzo_public) < streamzo_scripts.index(streamzo_identity)
assert playable_first in streamzo_scripts
assert streamzo_scripts.index(streamzo_identity) < streamzo_scripts.index(playable_first)
public_source = (ROOT / streamzo_public).read_text(encoding='utf-8')
assert 'original_title' in public_source and 'maxAliases' in public_source
identity_source = (ROOT / streamzo_identity).read_text(encoding='utf-8')
assert 'original_title' in identity_source and 'aliases.some' in identity_source
assert 'tokens' in identity_source and 'years' in identity_source
assert 'backtrack-les-revenants-2015' not in identity_source.lower()
assert '210702' not in identity_source

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
