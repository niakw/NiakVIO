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
assert "recovery-first-v4-timer-safe" in wrapped
assert 'typeof setTimeout==="function"' in wrapped
assert 'typeof clearTimeout==="function"' in wrapped
assert integrity.apply(wrapped, {"timeout_ms": 2000, "max_children": 2}) == wrapped

# A syntactically valid HLS header without any variant/media structure is not
# itself a stream. With no player/source context to recover, it is rejected.
run_node(r'''
globalThis.fetch=async function(url){return {ok:true,status:200,url:String(url),headers:{get:function(){return "application/vnd.apple.mpegurl"}},text:async function(){return "#EXTM3U\n#EXT-X-VERSION:3\n"}}};
''' + integrity.apply(r'''globalThis.getStreams=async function(){return [{url:"https://media.test/bare.m3u8",type:"hls"}]};''', {"timeout_ms": 2000}) + r'''
(async function(){var rows=await globalThis.getStreams("1","movie");if(!Array.isArray(rows)||rows.length!==0)throw new Error("unrecoverable header-only HLS was not rejected")})().catch(function(e){console.error(e);process.exit(1)});
''')

# Recovery-first regression: the native row points at a header-only HLS, but
# its normal Referer page embeds a player that exposes the real HLS source.
# Niakvio must follow that public player path, adapt Referer/Origin to the
# immediate player context and return the recovered playable source.
recovery_provider = r'''
globalThis.getStreams=async function(){return [{url:"https://broken.example/header.m3u8",type:"hls",headers:{Referer:"https://catalog.example/title"}}]};
'''
recovery_wrapped = integrity.apply(recovery_provider, {
    "timeout_ms": 2000,
    "max_children": 2,
    "max_recovery_pages": 4,
    "max_recovery_candidates": 12,
})
run_node(r'''
const media="#EXTM3U\n#EXT-X-TARGETDURATION:6\n#EXTINF:6,\nseg.ts\n#EXT-X-ENDLIST\n";
globalThis.fetch=async function(url,init){var u=String(url),h=(init&&init.headers)||{};
 if(u==="https://broken.example/header.m3u8")return {ok:true,status:200,url:u,headers:{get:function(){return "application/vnd.apple.mpegurl"}},text:async function(){return "#EXTM3U\n#EXT-X-VERSION:3\n"}};
 if(u==="https://catalog.example/title")return {ok:true,status:200,url:u,headers:{get:function(){return "text/html"}},text:async function(){return '<iframe src="https://player.example/e/abc"></iframe>'}};
 if(u==="https://player.example/e/abc")return {ok:true,status:200,url:u,headers:{get:function(){return "text/html"}},text:async function(){return '<script>const source="https://cdn.example/live/master.m3u8";</script>'}};
 if(u==="https://cdn.example/live/master.m3u8"){
   if(h.Referer!=="https://player.example/e/abc")throw new Error("recovered media did not receive player Referer: "+JSON.stringify(h));
   if(h.Origin!=="https://player.example")throw new Error("recovered media did not receive player Origin: "+JSON.stringify(h));
   return {ok:true,status:200,url:u,headers:{get:function(){return "application/vnd.apple.mpegurl"}},text:async function(){return media}};
 }
 return {ok:false,status:404,url:u,headers:{get:function(){return "text/plain"}},text:async function(){return ""}};
};
''' + recovery_wrapped + r'''
(async function(){var rows=await globalThis.getStreams("1","movie");if(rows.length!==1)throw new Error("recoverable HLS was dropped: "+JSON.stringify(rows));if(rows[0].url!=="https://cdn.example/live/master.m3u8")throw new Error("wrong recovered URL: "+JSON.stringify(rows));if(rows[0].headers.Referer!=="https://player.example/e/abc")throw new Error("returned Referer not adapted: "+JSON.stringify(rows[0].headers));if(rows[0].headers.Origin!=="https://player.example")throw new Error("returned Origin not adapted: "+JSON.stringify(rows[0].headers))})().catch(function(e){console.error(e);process.exit(1)});
''')

# If a row is labelled HLS but the endpoint itself conclusively serves a video
# container, normalize the output instead of rejecting a perfectly playable
# source just because the provider metadata was wrong.
direct_provider = integrity.apply(r'''globalThis.getStreams=async function(){return [{url:"https://media.example/opaque",type:"hls"}]};''', {"timeout_ms": 2000})
run_node(r'''
globalThis.fetch=async function(url){var u=String(url);return {ok:true,status:200,url:u,headers:{get:function(){return "video/mp4"}},text:async function(){throw new Error("binary response must not be decoded as text")}}};
''' + direct_provider + r'''
(async function(){var rows=await globalThis.getStreams("1","movie");if(rows.length!==1||rows[0].url!=="https://media.example/opaque"||rows[0].type!=="mp4")throw new Error("mislabelled direct media was not normalized: "+JSON.stringify(rows))})().catch(function(e){console.error(e);process.exit(1)});
''')

# A 200 HTML response behind a .m3u8 URL is conclusively invalid only after its
# body/context also fail to expose a recoverable media/player candidate.
run_node(r'''
globalThis.fetch=async function(url){return {ok:true,status:200,url:String(url),headers:{get:function(){return "text/html"}},text:async function(){return "<html>not hls</html>"}}};
''' + integrity.apply(r'''globalThis.getStreams=async function(){return [{url:"https://media.test/not-hls.m3u8",type:"hls"}]};''', {"timeout_ms": 2000}) + r'''
(async function(){var rows=await globalThis.getStreams("1","movie");if(!Array.isArray(rows)||rows.length!==0)throw new Error("malformed HLS was not rejected after recovery")})().catch(function(e){console.error(e);process.exit(1)});
''')

# Ordering regression: a catalogue wrapper can create an embed row after the
# ordinary HLS guard was installed. The final gate must replace that earlier
# guard, run last, resolve the embed and expose only the direct HLS media URL.
ordered = integrity.apply(
    r'''globalThis.getStreams=async function(){return []};''',
    {"timeout_ms": 2000},
)
ordered += r'''
;(function(){var native=globalThis.getStreams;globalThis.getStreams=async function(){await native.apply(this,arguments);return [{url:"https://catalog.example/embed/player",name:"streamzo #1",quality:"Unknown",headers:{Referer:"https://catalog.example/title"}}]}})();
'''
ordered = integrity.apply(ordered, {
    "timeout_ms": 2000,
    "max_recovery_pages": 4,
    "max_recovery_candidates": 12,
    "probe_all_urls": True,
    "fail_closed_unknown": True,
})
assert ordered.count("NUVIO_HLS_RUNTIME_INTEGRITY_V1:") == 1
assert ordered.rfind("NUVIO_HLS_RUNTIME_INTEGRITY_V1:") > ordered.rfind("streamzo #1")
assert "final-output-order-v5-timer-safe" in ordered
run_node(r'''
const media="#EXTM3U\n#EXT-X-TARGETDURATION:6\n#EXTINF:6,\nseg.ts\n#EXT-X-ENDLIST\n";
globalThis.fetch=async function(url){var u=String(url);
 if(u==="https://catalog.example/embed/player")return {ok:true,status:200,url:u,headers:{get:function(){return "text/html"}},text:async function(){return '<script>const source="https://cdn.example/final.m3u8";</script>'}};
 if(u==="https://cdn.example/final.m3u8")return {ok:true,status:200,url:u,headers:{get:function(){return "application/vnd.apple.mpegurl"}},text:async function(){return media}};
 return {ok:false,status:404,url:u,headers:{get:function(){return "text/plain"}},text:async function(){return ""}};
};
''' + ordered + r'''
(async function(){var rows=await globalThis.getStreams("1","movie");if(rows.length!==1||rows[0].url!=="https://cdn.example/final.m3u8"||rows[0].type!=="hls")throw new Error("post-recovery embed was not resolved by the final gate: "+JSON.stringify(rows))})().catch(function(e){console.error(e);process.exit(1)});
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
