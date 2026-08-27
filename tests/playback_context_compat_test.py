#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
from pathlib import Path


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if not spec or not spec.loader:
        raise AssertionError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run_node(source: str, harness: str) -> dict:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "provider.js").write_text(source, encoding="utf-8")
        (root / "harness.cjs").write_text(harness, encoding="utf-8")
        proc = subprocess.run(
            ["node", str(root / "harness.cjs")],
            cwd=root,
            text=True,
            capture_output=True,
            timeout=20,
        )
        if proc.returncode != 0:
            raise AssertionError(
                f"node harness failed rc={proc.returncode}\nstdout={proc.stdout}\nstderr={proc.stderr}"
            )
        return json.loads(proc.stdout.strip().splitlines()[-1])


def test_hls_hook_keeps_runtime_safety_ownership_separate(root: Path) -> None:
    guard = load_module(
        root / "scripts/provider_patches/hls_master_audio_preserver_v1.py",
        "hls_master_audio_preserver_v1",
    )
    base = (
        'async function preserveMaster(body){'
        'if(!/#EXT-X-STREAM-INF/i.test(body))return;'
        '}\n'
        'module.exports={getStreams:async()=>[{title:"Purstream 1080p Dual Audio",'
        'name:"Purstream",url:"https://cdn.test/master.m3u8",type:"hls",language:"fr"}]};\n'
    )
    patched = guard.apply(base, context={"provider_id": "purstream"})
    assert patched == guard.apply(patched, context={"provider_id": "purstream"})
    assert "NUVIO_HLS_MASTER_AUDIO_PRESERVER_V1" in patched
    assert "#EXT-X-MEDIA" in patched
    # Core V15 gives runtime/native media safety to runtime_capability_media_safety_v4.
    # The HLS adapter must not resurrect the historical platform fingerprint wrapper.
    assert "followRedirects" not in patched
    assert "NUVIO_GLOBAL_RUNTIME_MEDIA_SAFETY_V1" not in patched
    assert 'if(typeof g.__native_fetch==="function")return true' not in patched


def test_embed_cookie_and_header_inheritance(root: Path) -> None:
    enrichment = load_module(
        root / "scripts/provider_patches/global_media_enrichment_v1.py",
        "global_media_enrichment_v1",
    )
    base = 'module.exports={getStreams:async()=>[{title:"x",url:"https://player.example.com/watch"}]};\n'
    patched = enrichment.apply(base)
    assert patched == enrichment.apply(patched)
    assert "scoped-playback-context-v6-direct-safe-opaque-media" in patched
    assert 'typeof r.arrayBuffer==="function"' in patched
    assert 'typeof r.text==="function"' in patched

    # Deliberately expose text() but no arrayBuffer(): this matches the pinned
    # NuvioTV QuickJS fetch Response and prevents a Desktop-only assumption from
    # creeping back into the common site -> player -> media enrichment layer.
    harness = r'''
const fs=require('fs'),vm=require('vm');
const code=fs.readFileSync('provider.js','utf8');
function resp(url,status,ct,body,setCookie){return {ok:status>=200&&status<300,status,url,headers:{get:(n)=>{n=n.toLowerCase();if(n==='content-type')return ct;if(n==='set-cookie')return setCookie||null;return null;}},text:async()=>body};}
(async()=>{
 let requests=[];
 const ctx={console,URL,TextDecoder,Uint8Array,ArrayBuffer,setTimeout,clearTimeout,module:{exports:{}},exports:{}};ctx.globalThis=ctx;
 ctx.fetch=async (url,opt={})=>{
   requests.push({url,headers:Object.assign({},opt.headers||{})});
   if(url==='https://player.example.com/watch') return resp(url,200,'text/html','<script>var file="https://cdn.example.com/master.m3u8"</script>','token=abc; Domain=.example.com; Path=/; Secure');
   if(url==='https://cdn.example.com/master.m3u8') return resp(url,200,'application/vnd.apple.mpegurl','#EXTM3U\n#EXTINF:600,\nseg.ts\n#EXTINF:600,\nseg2.ts\n');
   return resp(url,404,'text/plain','no');
 };
 vm.createContext(ctx);vm.runInContext(code,ctx);
 const rows=await ctx.module.exports.getStreams('1','movie');
 const direct=rows.find(r=>r.url==='https://cdn.example.com/master.m3u8');
 console.log(JSON.stringify({rows,direct,requests}));
})();
'''
    result = run_node(patched, harness)
    direct = result["direct"]
    assert direct, result
    headers = direct["headers"]
    assert headers["Cookie"] == "token=abc", headers
    assert headers["Referer"] == "https://player.example.com/watch", headers
    assert headers["Origin"] == "https://player.example.com", headers
    assert "User-Agent" not in headers, headers
    child = next(x for x in result["requests"] if x["url"] == "https://cdn.example.com/master.m3u8")
    assert child["headers"].get("Cookie") == "token=abc", child


def test_cookie_scope_does_not_leak(root: Path) -> None:
    enrichment = load_module(
        root / "scripts/provider_patches/global_media_enrichment_v1.py",
        "global_media_enrichment_v1_scope",
    )
    patched = enrichment.apply(
        'module.exports={getStreams:async()=>[{title:"x",url:"https://player.example.com/watch"}]};\n'
    )
    harness = r'''
const fs=require('fs'),vm=require('vm');const code=fs.readFileSync('provider.js','utf8');
function resp(url,status,ct,body,setCookie){return{ok:status>=200&&status<300,status,url,headers:{get:n=>n.toLowerCase()==='content-type'?ct:n.toLowerCase()==='set-cookie'?(setCookie||null):null},text:async()=>body}}
(async()=>{let childHeaders={};const ctx={console,URL,TextDecoder,Uint8Array,ArrayBuffer,setTimeout,clearTimeout,module:{exports:{}},exports:{}};ctx.globalThis=ctx;ctx.fetch=async(url,opt={})=>{if(url.includes('player.example.com'))return resp(url,200,'text/html','<a href="https://cdn.other.net/master.m3u8">x</a>','hostonly=secret; Path=/; Secure');if(url.includes('cdn.other.net')){childHeaders=opt.headers||{};return resp(url,200,'application/vnd.apple.mpegurl','#EXTM3U\n#EXTINF:600,\na.ts\n#EXTINF:600,\nb.ts\n')}return resp(url,404,'text/plain','')};vm.createContext(ctx);vm.runInContext(code,ctx);const rows=await ctx.module.exports.getStreams();const direct=rows.find(r=>String(r.url).includes('cdn.other.net'));console.log(JSON.stringify({direct,childHeaders}));})();
'''
    result = run_node(patched, harness)
    assert "Cookie" not in (result["direct"].get("headers") or {}), result
    assert "Cookie" not in result["childHeaders"], result


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    test_hls_hook_keeps_runtime_safety_ownership_separate(root)
    test_embed_cookie_and_header_inheritance(root)
    test_cookie_scope_does_not_leak(root)
    print("playback context compatibility tests passed")


if __name__ == "__main__":
    main()
