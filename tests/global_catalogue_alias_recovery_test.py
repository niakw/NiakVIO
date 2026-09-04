#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
PATCH = ROOT / "scripts" / "provider_patches" / "global_catalogue_alias_recovery_v2.py"
spec = importlib.util.spec_from_file_location("global_alias_v2", PATCH)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

base = """module.exports={getStreams:async function(input){
  const id=String(input&&input.tmdbId||input||"");
  if(id==="515151")return [{name:"Example",title:"Example - Film",url:"https://player.example/embed-515151.html"}];
  return [];
}};"""
options = {
    "base_url": "https://catalog.example",
    "provider_name": "Example",
    "max_aliases": 8,
    "max_candidates": 8,
    "max_players": 8,
    "timeout_ms": 5000,
    "budget_ms": 20000,
    "direct_paths": ["/{slug}"],
    "search_paths": ["/?s={query}", "/search?q={query}"],
    "detail_id_attributes": ["data-film-id"],
    "mirror_routes": ["/api/mirrors/film/{id}"],
    "mirror_types": ["movie", "anime"],
    "mirror_allow_episodic": False,
}
patched = module.apply(base, options)
assert '"baseUrl":""' in patched
assert "function baseUrl()" in patched
assert "https://catalog.example" not in patched

assert "NUVIO_GLOBAL_CATALOGUE_ALIAS_RECOVERY_V2" in patched
assert '"implementationRevision":"authoritative-recovery-v12-html-scanner"' in patched
assert "function providerDeadline()" in patched
assert "function workDeadline()" in patched
assert "__nuvioProviderDeadlineMs" in patched
assert "api.themoviedb.org" not in patched
assert "TMDB_API_KEY" not in patched
assert "__nuvioMediaContext" in patched
assert "tmdbMetadata" in patched
assert "detailIdAttributes" in patched
assert "mirrorRoutes" in patched
for forbidden in ("StreamZo", "Mon ninja et moi 3", "Ternet Ninja 3", "Interstellar"):
    assert forbidden not in patched

# Existing V2/LKG wrappers remain upgradeable and idempotent.
legacy_runtime = '''/* NUVIO_GLOBAL_CATALOGUE_ALIAS_RECOVERY_V1:legacy */
;(function(g,c){})(typeof globalThis!=="undefined"?globalThis:this,{});\n''' + base
without_legacy = module.apply(legacy_runtime, options)
assert "NUVIO_GLOBAL_CATALOGUE_ALIAS_RECOVERY_V1" not in without_legacy
assert without_legacy.count("NUVIO_GLOBAL_CATALOGUE_ALIAS_RECOVERY_V2:") == 1
assert module.apply(patched, options) == patched

runner = r'''
const assert = require('assert');
const calls = [];
function response(body, status=200, type='application/json', url='') {
  return {
    ok: status >= 200 && status < 400,
    status,
    url,
    headers: { get(name) { return String(name).toLowerCase() === 'content-type' ? type : null; } },
    async json() { return JSON.parse(body); },
    async text() { return body; },
  };
}
const metadata = {
  id: 424242,
  title: 'Film Exemple',
  original_title: 'Original Feature',
  release_date: '2024-05-01',
  alternative_titles: {titles:[
    {iso_3166_1:'FR',title:'Titre Alternatif'},
    {iso_3166_1:'US',title:'Feature Alternate'}
  ]},
  external_ids: {imdb_id:'tt1234567'},
  __nuvioTmdbNamespace:'movie',
  __nuvioTmdbId:'424242'
};
global.NIAKVIO_PROVIDER_MODEL = {officialSite:'https://catalog.example'};
global.__nuvioMediaContext = {
  tmdbId:'424242',
  imdbId:'tt1234567',
  canonicalMediaType:'movie',
  tmdbMetadata:metadata
};
global.fetch = async function(url) {
  url = String(url);
  calls.push(url);
  if (url.includes('themoviedb.org')) throw new Error('catalogue layer must never call TMDB');
  if (url.startsWith('https://catalog.example/?s=') || url.startsWith('https://catalog.example/search?')) {
    return response('<a href="/original-feature-2024">Original Feature (2024)</a>', 200, 'text/html', url);
  }
  if (url === 'https://catalog.example/original-feature-2024') {
    return response('<html data-film-id="77"><h1>Original Feature (2024)</h1></html>', 200, 'text/html', url);
  }
  if (url === 'https://catalog.example/api/mirrors/film/77') {
    return response(JSON.stringify({players:{VF:[{url:'https://player.example/e/abc'}]}}), 200, 'application/json', url);
  }
  if (url.startsWith('https://catalog.example/')) return response('', 404, 'text/html', url);
  return response('', 404, 'text/plain', url);
};
PATCHED_SOURCE
(async () => {
  const rows = await module.exports.getStreams({
    tmdbId:'424242',
    mediaType:'movie',
    tmdbMetadata:metadata,
  });
  assert(Array.isArray(rows) && rows.length === 0, JSON.stringify(rows));
  assert.strictEqual(calls.length, 0, 'zero provider output must not trigger catalogue recovery');

  // Opaque provider/player URLs are not content identity evidence. Technical
  // embed/html tokens must not make Core discard an otherwise valid native row.
  calls.length = 0;
  const nativeMetadata = {
    id:515151,
    title:'Native Example',
    original_title:'Native Example',
    release_date:'2024-06-01',
    alternative_titles:{titles:[]},
    __nuvioTmdbNamespace:'movie',
    __nuvioTmdbId:'515151'
  };
  global.__nuvioMediaContext = {
    tmdbId:'515151',
    canonicalMediaType:'movie',
    tmdbMetadata:nativeMetadata
  };
  const nativeRows = await module.exports.getStreams({
    tmdbId:'515151', mediaType:'movie', tmdbMetadata:nativeMetadata
  });
  assert(Array.isArray(nativeRows) && nativeRows.length === 1, JSON.stringify(nativeRows));
  assert.strictEqual(nativeRows[0].url, 'https://player.example/embed-515151.html');
  assert(!calls.some(x => x.startsWith('https://catalog.example/')), calls.join('\n'));

  calls.length = 0;
  const animeMetadata = {
    id: 999,
    title:'Anime Exemple',
    original_title:'Anime Example',
    release_date:'2024-01-01',
    alternative_titles:{titles:[]},
    __nuvioTmdbNamespace:'tv',
    __nuvioTmdbId:'999'
  };
  global.__nuvioMediaContext = {
    tmdbId:'999',
    canonicalMediaType:'anime',
    tmdbMetadata:animeMetadata
  };
  const episodic = await module.exports.getStreams({
    tmdbId:'999', mediaType:'anime', season:1, episode:1, tmdbMetadata:animeMetadata
  });
  assert(Array.isArray(episodic) && episodic.length === 0, JSON.stringify(episodic));
  assert(!calls.some(x => x.includes('/api/mirrors/film/')), calls.join('\n'));

  console.log('global catalogue layer preserves zero-output exit and filters positive rows only');
})().catch(err => { console.error(err); process.exit(1); });
'''.replace("PATCHED_SOURCE", patched)

with tempfile.NamedTemporaryFile("w", prefix="niakvio-alias-", suffix=".cjs", delete=False, encoding="utf-8") as handle:
    handle.write(runner)
    temp = Path(handle.name)
try:
    proc = subprocess.run(["node", str(temp)], cwd=ROOT, capture_output=True, text=True, timeout=30)
    if proc.returncode != 0:
        raise AssertionError(f"node runtime test failed\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}")
    print(proc.stdout.strip())
finally:
    temp.unlink(missing_ok=True)
