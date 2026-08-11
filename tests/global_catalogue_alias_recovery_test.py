#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / "scripts" / "provider_patches" / "global_catalogue_alias_recovery_v2.py"
spec = importlib.util.spec_from_file_location("global_alias_v2", PATCH)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

base = "module.exports={getStreams:async function(){return [];}};"
patched = module.apply(base, {
    "base_url": "https://catalog.example",
    "provider_name": "Example",
    "max_aliases": 8,
    "max_candidates": 8,
    "max_players": 8,
    "timeout_ms": 5000,
})

assert "NUVIO_GLOBAL_CATALOGUE_ALIAS_RECOVERY_V2" in patched
assert "external_source=imdb_id" in patched
assert "/find/" in patched
assert "original_title" in patched
assert "alternative_titles" in patched
for forbidden in ("Mon ninja et moi 3", "Ternet Ninja 3", "Interstellar"):
    assert forbidden not in patched

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
global.fetch = async function(url) {
  url = String(url);
  calls.push(url);
  if (url.includes('/find/tt1234567?') && url.includes('external_source=imdb_id')) {
    return response(JSON.stringify({movie_results:[{id:424242,title:'Feature Locale',original_title:'Original Feature',release_date:'2024-05-01'}],tv_results:[]}), 200, 'application/json', url);
  }
  if (url.includes('/movie/424242?') && url.includes('language=fr-FR')) {
    return response(JSON.stringify({id:424242,title:'Film Exemple',original_title:'Original Feature',release_date:'2024-05-01'}), 200, 'application/json', url);
  }
  if (url.includes('/movie/424242?') && url.includes('language=en-US')) {
    return response(JSON.stringify({id:424242,title:'Example Feature',original_title:'Original Feature',release_date:'2024-05-01'}), 200, 'application/json', url);
  }
  if (url.includes('/movie/424242/alternative_titles?')) {
    return response(JSON.stringify({titles:[{iso_3166_1:'FR',title:'Titre Alternatif'},{iso_3166_1:'DE',title:'Alternativtitel'}]}), 200, 'application/json', url);
  }
  if (url.startsWith('https://catalog.example/?s=') || url.startsWith('https://catalog.example/search?')) {
    return response('<a href="/original-feature-2024">Original Feature (2024)</a>', 200, 'text/html', url);
  }
  if (url === 'https://catalog.example/original-feature-2024') {
    return response('<html><h1>Original Feature (2024)</h1><iframe src="https://player.example/e/abc"></iframe></html>', 200, 'text/html', url);
  }
  if (url.startsWith('https://catalog.example/')) {
    return response('', 404, 'text/html', url);
  }
  return response('', 404, 'text/plain', url);
};
PATCHED_SOURCE
(async () => {
  const rows = await module.exports.getStreams({id:'tt1234567', mediaType:'movie'});
  assert(Array.isArray(rows) && rows.length === 1, JSON.stringify(rows));
  assert.strictEqual(rows[0].url, 'https://player.example/e/abc');
  assert(calls.some(x => x.includes('/find/tt1234567?') && x.includes('external_source=imdb_id')), calls.join('\n'));
  assert(calls.some(x => x.includes('/movie/424242?') && x.includes('language=fr-FR')), calls.join('\n'));
  assert(calls.some(x => x.includes('/movie/424242/alternative_titles?')), calls.join('\n'));

  calls.length = 0;
  const rows2 = await module.exports.getStreams({id:'tmdb:424242', mediaType:'movie'});
  assert(Array.isArray(rows2) && rows2.length === 1, JSON.stringify(rows2));
  assert(!calls.some(x => x.includes('/find/')), calls.join('\n'));
  assert(calls.some(x => x.includes('/movie/424242?')), calls.join('\n'));
  console.log('global TMDB/IMDb ID-first catalogue alias recovery runtime test passed');
})().catch(err => { console.error(err); process.exit(1); });
'''.replace("PATCHED_SOURCE", patched)

with tempfile.NamedTemporaryFile("w", suffix=".cjs", dir=ROOT, delete=False, encoding="utf-8") as handle:
    handle.write(runner)
    temp = Path(handle.name)
try:
    proc = subprocess.run(["node", str(temp)], cwd=ROOT, capture_output=True, text=True, timeout=30)
    if proc.returncode != 0:
        raise AssertionError(f"node runtime test failed\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}")
    print(proc.stdout.strip())
finally:
    temp.unlink(missing_ok=True)
