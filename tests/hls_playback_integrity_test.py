#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if not spec or not spec.loader:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_node(source: str) -> None:
    with tempfile.NamedTemporaryFile("w", suffix=".cjs", encoding="utf-8", delete=False) as handle:
        handle.write(source)
        path = Path(handle.name)
    try:
        result = subprocess.run(["node", str(path)], capture_output=True, text=True, check=False, timeout=15)
        if result.returncode:
            raise AssertionError((result.stdout + "\n" + result.stderr).strip())
    finally:
        path.unlink(missing_ok=True)


audio = load_module(ROOT / "scripts/provider_patches/hls_master_audio_preserver_v1.py", "hls_audio")
integrity = load_module(ROOT / "scripts/provider_patches/hls_runtime_integrity_v1.py", "hls_integrity")

fixture = 'async function q(t){let x=await p.text();if(!/#EXT-X-STREAM-INF/i.test(x))return [{url:t.url,type:"hls"}];return []}'
patched = audio.apply(fixture)
assert "NUVIO_HLS_MASTER_AUDIO_PRESERVER_V1" in patched
assert "/#EXT-X-MEDIA:[^\\r\\n]*TYPE=AUDIO/i.test(x)" in patched
assert audio.apply(patched) == patched

base_provider = r'''
globalThis.getStreams=async function(){return [{url:"https://media.test/master.m3u8",type:"hls",headers:{Referer:"https://site.test/"}}]};
'''
wrapped = integrity.apply(base_provider, {"timeout_ms": 2000, "max_children": 2})
assert "NUVIO_HLS_RUNTIME_INTEGRITY_V1" in wrapped
assert integrity.apply(wrapped, {"timeout_ms": 2000, "max_children": 2}) == wrapped

# A 200 HTML response behind a .m3u8 URL is a conclusive invalid stream and
# must be removed rather than sent to Nuvio's HLS parser.
run_node(r'''
globalThis.fetch=async function(url){return {ok:true,status:200,url:String(url),headers:{get:function(){return "text/html"}},text:async function(){return "<html>not hls</html>"}}};
''' + wrapped + r'''
(async function(){var rows=await globalThis.getStreams("1","movie");if(!Array.isArray(rows)||rows.length!==0)throw new Error("malformed HLS was not rejected")})().catch(function(e){console.error(e);process.exit(1)});
''')

# A complete master with a video child and an external audio child is valid and
# the original master URL must survive, preserving selectable audio renditions.
master = "#EXTM3U\n#EXT-X-MEDIA:TYPE=AUDIO,GROUP-ID=\"aud\",LANGUAGE=\"fr\",NAME=\"Français\",DEFAULT=YES,AUTOSELECT=YES,URI=\"audio.m3u8\"\n#EXT-X-STREAM-INF:BANDWIDTH=3000000,AUDIO=\"aud\"\nvideo.m3u8\n"
media = "#EXTM3U\n#EXT-X-TARGETDURATION:6\n#EXTINF:6,\nseg.ts\n#EXT-X-ENDLIST\n"
run_node(r'''
const master=''' + repr(master) + r''';const media=''' + repr(media) + r''';
globalThis.fetch=async function(url){var u=String(url);return {ok:true,status:200,url:u,headers:{get:function(){return "application/vnd.apple.mpegurl"}},text:async function(){return u.indexOf("master.m3u8")>=0?master:media}}};
''' + wrapped + r'''
(async function(){var rows=await globalThis.getStreams("1","movie");if(rows.length!==1||rows[0].url!=="https://media.test/master.m3u8")throw new Error("valid A/V HLS master was not preserved")})().catch(function(e){console.error(e);process.exit(1)});
''')

print("HLS playback integrity tests passed")
