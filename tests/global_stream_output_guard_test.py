#!/usr/bin/env python3
from pathlib import Path
import json
import subprocess
import tempfile
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from apply_provider_overrides import apply_overrides

MARKER = 'NUVIO_GLOBAL_STREAM_OUTPUT_GUARD_V3'


def execute(source: bytes, provider_id: str = 'synthetic') -> list[dict]:
    patched, records = apply_overrides(provider_id, source)
    text = patched.decode()
    assert MARKER in text
    guard = text[text.index(MARKER):]
    assert "async function" not in guard, "guard must remain compatible with Nuvio dynamic runtime"
    assert "await " not in guard, "guard must use Promise chains, not raw await"
    assert any(item.get('type') == 'global_stream_output_guard' for item in records)
    with tempfile.TemporaryDirectory() as td:
        provider = Path(td) / 'provider.js'
        provider.write_text(text)
        script = f'''const p=require({json.dumps(str(provider))}); const fn=typeof p==='function'?p:p.getStreams; Promise.resolve(fn()).then(x=>console.log(JSON.stringify(x)));'''
        output = subprocess.check_output(['node', '-e', script], text=True)
        return json.loads(output.strip())


streams = execute(b'''var arbitrary={getStreams:async function(){return [
 {name:"Movie 1080p Dual-Audio",title:"VFF + VO",url:"https://cdn.example/video.m3u8",headers:{}},
 {name:"bad",url:"https://cdn.example/file.avi"},
 {name:"dup",url:"https://cdn.example/video.m3u8"}
]}}; module.exports=arbitrary;''')
assert len(streams) == 1, streams
assert streams[0]['quality'] == '1080p', streams
assert streams[0]['language'] == 'MULTI', streams
assert streams[0]['headers']['Range'] == 'bytes=0-', streams
assert streams[0]['headers']['Accept'] == '*/*', streams
assert streams[0]['headers']['User-Agent'], streams

# Function-only CommonJS exports are also wrapped.
function_streams = execute(b'''module.exports=async function(){return [{name:"720p VO",url:"https://cdn.example/movie.mp4"}]};''')
assert function_streams[0]['quality'] == '720p', function_streams
assert function_streams[0]['language'] == 'VO', function_streams

# Every provider currently referenced by a published manifest must be patchable,
# regardless of its minifier/bundler variable names.
manifest_paths = [ROOT / 'manifest.json', ROOT / 'vf' / 'manifest.json', ROOT / 'vo' / 'manifest.json', ROOT / 'vostfr' / 'manifest.json']
referenced: dict[str, str] = {}
for manifest_path in manifest_paths:
    if not manifest_path.exists():
        continue
    payload = json.loads(manifest_path.read_text())
    for item in payload.get('scrapers', []):
        filename = item.get('filename') or item.get('url') or ''
        if 'providers/' not in filename:
            continue
        relative = filename[filename.index('providers/'):].split('?', 1)[0]
        provider_id = str(item.get('id') or item.get('name') or Path(relative).stem).casefold()
        referenced[relative] = provider_id

assert referenced, 'no manifest providers discovered'
for relative, provider_id in sorted(referenced.items()):
    provider_path = ROOT / relative
    assert provider_path.exists(), f'missing referenced provider: {relative}'
    patched, records = apply_overrides(provider_id, provider_path.read_bytes())
    assert MARKER.encode() in patched, f'guard missing after patch: {relative}'
    assert MARKER.encode() in provider_path.read_bytes() or any(item.get('type') == 'global_stream_output_guard' for item in records), relative

print(f'global stream output guard test passed ({len(referenced)} referenced providers patchable)')

# A previously published V2 guard is removed rather than stacked.
legacy = b"module.exports={getStreams:function(){return Promise.resolve([])}};\n/* NUVIO_GLOBAL_STREAM_OUTPUT_GUARD_V2 */\n;(function(){ var wrapped=async function(){return []}; })();"
patched, records = apply_overrides('legacy', legacy)
legacy_text = patched.decode()
assert 'NUVIO_GLOBAL_STREAM_OUTPUT_GUARD_V2' not in legacy_text
assert legacy_text.count(MARKER) == 1
assert any(item.get('type') == 'global_stream_output_guard' for item in records)
