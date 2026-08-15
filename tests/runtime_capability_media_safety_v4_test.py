#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / "scripts/provider_patches/runtime_capability_media_safety_v4.py"

# The native budget layers, synchronous-target traversal and final runtime
# capability guard form one engine stack. Keep their focused regression tests
# mandatory anywhere the v4 regression test is run (including permanent npm CI).
for companion in (
    "tests/native_catalogue_recovery_budget_test.py",
    "tests/native_hls_integrity_budget_test.py",
    "tests/native_sync_fetch_target_order_test.py",
):
    result = subprocess.run(
        [sys.executable, str(ROOT / companion)],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr

spec = importlib.util.spec_from_file_location("runtime_capability_media_safety_v4", PATCH)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

BASE = "module.exports={getStreams:async()=>[{name:'x',url:'https://media.example/master.m3u8',type:'hls'}]};\n"


def patched(provider_id: str, source: str = BASE) -> str:
    return module.apply(source, context={"provider_id": provider_id})


def run_node(source: str, fetch_impl: str, expression: str, prelude: str = "") -> object:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        provider = root / "provider.cjs"
        runner = root / "runner.cjs"
        provider.write_text(source, encoding="utf-8")
        runner.write_text(
            prelude + "\nglobal.fetch=" + fetch_impl + ";\n" +
            "const p=require(" + json.dumps(str(provider)) + ");\n" + expression + "\n",
            encoding="utf-8",
        )
        result = subprocess.run(["node", str(runner)], text=True, capture_output=True, check=False)
        assert result.returncode == 0, result.stdout + result.stderr
        return json.loads(result.stdout.strip())


streamzo = patched("streamzo")
assert streamzo.count("NUVIO_GLOBAL_RUNTIME_MEDIA_SAFETY_V1:") == 1
assert '"implementationRevision":"field-safety-v4-runtime-capability"' in streamzo

# Any old published wrapper is replaced, never stacked.
legacy = streamzo.replace('"implementationRevision":"field-safety-v4-runtime-capability"', '"implementationRevision":"field-safety-v2"')
upgraded = patched("streamzo", legacy)
assert upgraded.count("NUVIO_GLOBAL_RUNTIME_MEDIA_SAFETY_V1:") == 1
assert '"implementationRevision":"field-safety-v4-runtime-capability"' in upgraded
assert '"implementationRevision":"field-safety-v2"' not in upgraded
assert patched("streamzo", upgraded) == upgraded

# Every official Nuvio native QuickJS host exposes __native_fetch. Because that
# bridge is synchronous in Desktop, Mobile and TV, the safety layer must not add
# a post-result media probe on any of those clients.
for user_agent in ("NuvioDesktop macOS", "NuvioMobile Android", "NuvioTV Android TV"):
    value = run_node(
        streamzo,
        "async function(){global.__fetchCalls++;throw new Error('must not probe from native safety layer')}",
        "p.getStreams('1215638','movie',null,null).then(v=>console.log(JSON.stringify({rows:v.length,calls:global.__fetchCalls}))).catch(e=>{console.error(e);process.exit(1)})",
        "global.__fetchCalls=0;global.__native_fetch=function(){};global.navigator={userAgent:" + json.dumps(user_agent) + "};",
    )
    assert value == {"rows": 1, "calls": 0}, (user_agent, value)

# Native TV still rejects obvious embeds statically without touching fetch.
tv_bad = patched("streamzo", "module.exports={getStreams:async()=>[{url:'https://host.test/embed/player'}]};\n")
value = run_node(
    tv_bad,
    "async function(){global.__fetchCalls++;throw new Error('must reject statically')}",
    "p.getStreams('1215638','movie',null,null).then(v=>console.log(JSON.stringify({rows:v.length,calls:global.__fetchCalls}))).catch(e=>{console.error(e);process.exit(1)})",
    "global.__fetchCalls=0;global.__native_fetch=function(){};global.navigator={userAgent:'NuvioTV Android TV'};",
)
assert value == {"rows": 0, "calls": 0}, value

# Non-native/web-like runtime keeps bounded remote validation.
forbidden = r"""async function(url){global.__fetchCalls++;return {ok:false,status:403,url:String(url),text:async()=>'',headers:{get:()=> 'text/plain'}}}"""
value = run_node(
    patched("moviebox", "module.exports={getStreams:async()=>[{url:'https://media.example/video.mp4',type:'mp4'}]};\n"),
    forbidden,
    "p.getStreams('1215638','movie',null,null).then(v=>console.log(JSON.stringify({rows:v.length,calls:global.__fetchCalls}))).catch(e=>{console.error(e);process.exit(1)})",
    "global.__fetchCalls=0;global.navigator={userAgent:'web-like-test'};",
)
assert value["rows"] == 0 and value["calls"] >= 1, value

print("runtime capability media safety v4 tests passed")
