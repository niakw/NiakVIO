#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one match, got {count}: {old[:120]!r}")
    p.write_text(text.replace(old, new, 1), encoding="utf-8")


hls = "scripts/provider_patches/hls_master_audio_preserver_v1.py"
replace_once(
    hls,
    'provider_id = str(context.get("provider_id") or "").strip().casefold()\n\n    output = text',
    'provider_id = str(context.get("provider_id") or "").strip().casefold()\n    cfg = dict(options or {})\n\n    output = text',
)
replace_once(
    hls,
    'if(!Object.keys(out).some(function(k){return k.toLowerCase()==="user-agent"}))out["User-Agent"]=DEFAULT_UA;',
    'if(c.defaultUserAgent&&!Object.keys(out).some(function(k){return k.toLowerCase()==="user-agent"}))out["User-Agent"]=c.defaultUserAgent;',
)
replace_once(
    hls,
    'if(!Object.keys(h).some(function(k){return k.toLowerCase()==="user-agent"})){h["User-Agent"]=DEFAULT_UA;has=true}',
    'if(c.defaultUserAgent&&!Object.keys(h).some(function(k){return k.toLowerCase()==="user-agent"})){h["User-Agent"]=c.defaultUserAgent;has=true}',
)
replace_once(
    hls,
    'if(c.strictPlayback||tv)return {keep:false,reason:result.reason||"unverified_media"};',
    'if(c.strictPlayback||c.failClosedUnknown)return {keep:false,reason:result.reason||"unverified_media"};',
)
replace_once(
    hls,
    '"strictPlayback": provider_id == "moviebox",\n        "tmdbKey":',
    '"strictPlayback": provider_id == "moviebox",\n        "failClosedUnknown": bool(cfg.get("fail_closed_unknown", False)),\n        "defaultUserAgent": str(cfg.get("default_user_agent") or ""),\n        "tmdbKey":',
)
replace_once(
    hls,
    '"implementationRevision": "platform-playback-context-v3",',
    '"implementationRevision": "scoped-playback-context-v4",',
)

media = "scripts/provider_patches/global_media_enrichment_v1.py"
replace_once(
    media,
    '"preserveOriginal": bool(cfg.get("preserve_original", True)),\n        "implementationRevision": "playback-context-v3",',
    '"preserveOriginal": bool(cfg.get("preserve_original", True)),\n        "defaultUserAgent": str(cfg.get("default_user_agent") or ""),\n        "implementationRevision": "scoped-playback-context-v4",',
)
replace_once(
    media,
    'if(!keyOf(out,"User-Agent"))setHeader(out,"User-Agent",DEFAULT_UA);',
    'if(c.defaultUserAgent&&!keyOf(out,"User-Agent"))setHeader(out,"User-Agent",c.defaultUserAgent);',
)

override_path = Path("provider-overrides.json")
config = json.loads(override_path.read_text(encoding="utf-8"))
streamzo_options = config["provider_patches"]["streamzo"].setdefault("patch_script_options", {})
ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
streamzo_options.setdefault("scripts/provider_patches/hls_master_audio_preserver_v1.py", {})[
    "default_user_agent"
] = ua
streamzo_options.setdefault("scripts/provider_patches/global_media_enrichment_v1.py", {})[
    "default_user_agent"
] = ua
override_path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

compat = "tests/playback_context_compat_test.py"
replace_once(
    compat,
    'assert desktop["headers"]["User-Agent"].startswith("Mozilla/5.0")\n    assert tv["headers"]["User-Agent"].startswith("Mozilla/5.0")',
    'assert not desktop.get("headers"), desktop\n    assert not tv.get("headers"), tv',
)
replace_once(compat, 'assert "playback-context-v3" in patched', 'assert "scoped-playback-context-v4" in patched')
replace_once(
    compat,
    'assert headers["User-Agent"].startswith("Mozilla/5.0"), headers',
    'assert "User-Agent" not in headers, headers',
)

regression = r'''#!/usr/bin/env python3
from __future__ import annotations
import importlib.util
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def load_apply(rel):
    path = ROOT / rel
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.apply

hls_apply = load_apply("scripts/provider_patches/hls_master_audio_preserver_v1.py")
media_apply = load_apply("scripts/provider_patches/global_media_enrichment_v1.py")
base = 'globalThis.getStreams=async function(){return [{url:"https://media.invalid/master.m3u8",type:"hls"}]};\n'
ordinary = hls_apply(base, options={}, context={"provider_id":"ordinary"})
assert "c.strictPlayback||c.failClosedUnknown" in ordinary
assert "c.strictPlayback||tv" not in ordinary
assert "c.defaultUserAgent&&" in ordinary
assert '"defaultUserAgent":""' in ordinary
assert '"failClosedUnknown":false' in ordinary
assert '"strictPlayback":true' in hls_apply(base, options={}, context={"provider_id":"moviebox"})
assert '"defaultUserAgent":"UA-STREAMZO"' in hls_apply(base, options={"default_user_agent":"UA-STREAMZO"}, context={"provider_id":"streamzo"})
enriched = media_apply(base, options={})
assert '"defaultUserAgent":""' in enriched
assert 'c.defaultUserAgent&&!keyOf(out,"User-Agent")' in enriched
assert '"defaultUserAgent":"UA-STREAMZO"' in media_apply(base, options={"default_user_agent":"UA-STREAMZO"})

cfg = json.loads((ROOT / "provider-overrides.json").read_text(encoding="utf-8"))
sopts = cfg["provider_patches"]["streamzo"]["patch_script_options"]
assert sopts["scripts/provider_patches/hls_master_audio_preserver_v1.py"]["default_user_agent"]
assert sopts["scripts/provider_patches/global_media_enrichment_v1.py"]["default_user_agent"]
assert sopts["scripts/provider_patches/hls_runtime_integrity_v1.py"]["fail_closed_unknown"] is True

runtime = ordinary + (
    "\nglobalThis.__NUVIO_TV_RUNTIME__=true;\n"
    'globalThis.fetch=async function(){throw new Error("bridge cannot reprobe")};\n'
    '(async()=>{var rows=await globalThis.getStreams({tmdbId:"1",mediaType:"movie"});console.log("COUNT="+rows.length)})().catch(e=>{console.error(e);process.exit(2)});\n'
)
with tempfile.NamedTemporaryFile("w", suffix=".cjs", delete=False, encoding="utf-8") as handle:
    handle.write(runtime)
    filename = handle.name
result = subprocess.run(["node", filename], capture_output=True, text=True, timeout=20)
Path(filename).unlink(missing_ok=True)
assert result.returncode == 0, result.stderr
assert "COUNT=1" in result.stdout, result.stdout
print("scoped playback context regression tests passed")
'''
Path("tests/scoped_playback_context_regression_test.py").write_text(regression, encoding="utf-8")
print("scoped playback-context migration staged")
