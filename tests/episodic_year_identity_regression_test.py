#!/usr/bin/env python3
from __future__ import annotations
import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
PATCH = ROOT / 'scripts/provider_patches/global_stream_identity_v1.py'
spec = importlib.util.spec_from_file_location('global_stream_identity_year_regression', PATCH)
assert spec and spec.loader
identity = importlib.util.module_from_spec(spec)
spec.loader.exec_module(identity)

source = "module.exports={getStreams:async()=>[{name:'Server 1',title:'Shared Show 2020',url:'https://cdn.example/shared-show-2020.m3u8'}]};"
patched = identity.apply(source, context={'provider_id': 'example'})
assert 'cross-client-shared-tv-year-soft-v8' in patched
assert 'if(!episodic(q)&&m.year&&years.length' in patched

runner = """
const assert=require('assert');
PATCHED
(async()=>{
  for(const mediaType of ['tv','series','anime']){
    const rows=await module.exports.getStreams({tmdbId:'',mediaType,title:'Shared Show',year:2024,season:1,episode:1});
    assert.equal(rows.length,1,mediaType+': '+JSON.stringify(rows));
  }
  const movieRows=await module.exports.getStreams({tmdbId:'',mediaType:'movie',title:'Shared Show',year:2024});
  assert.equal(movieRows.length,0,'movie year mismatch must remain authoritative: '+JSON.stringify(movieRows));
})().catch(e=>{console.error(e);process.exit(3)});
""".replace('PATCHED', patched)

with tempfile.NamedTemporaryFile('w', suffix='.cjs', encoding='utf-8', delete=False) as handle:
    handle.write(runner)
    path = Path(handle.name)
try:
    proc = subprocess.run(['node', str(path)], cwd=ROOT, text=True, capture_output=True, timeout=20)
    assert proc.returncode == 0, proc.stdout + proc.stderr
finally:
    path.unlink(missing_ok=True)
print('episodic year identity regression tests passed')
