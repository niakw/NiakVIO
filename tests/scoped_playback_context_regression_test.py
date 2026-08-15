#!/usr/bin/env python3
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
assert sopts["scripts/provider_patches/hls_runtime_integrity_v1.py"]["fail_closed_unknown"] is False

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


# Integration contract: global media enrichment must receive provider-scoped
# options. This is what lets StreamZo retain its proven browser context without
# synthesizing the same headers for unrelated providers.
import sys
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('apply_provider_overrides_scoped_test', ROOT/'scripts/apply_provider_overrides.py')
assert spec and spec.loader
apply_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(apply_mod)

captured = []
def capture_patch(text, provider_id, patch_script, options, profile_name):
    captured.append((provider_id, patch_script, dict(options)))
    return text + f"\n/* capture:{provider_id}:{patch_script} */\n"
apply_mod._apply_patch_script = capture_patch

apply_mod.apply_overrides('streamzo', b'module.exports={getStreams:async()=>[]};\n', phase='discovery')
streamzo_media = [opts for pid,path,opts in captured if pid == 'streamzo' and path.endswith('global_media_enrichment_v1.py')]
assert streamzo_media, captured
assert streamzo_media[-1].get('default_user_agent','').startswith('Mozilla/5.0'), streamzo_media[-1]

captured.clear()
apply_mod.apply_overrides('cineby', b'module.exports={getStreams:async()=>[]};\n', phase='discovery')
ordinary_media = [opts for pid,path,opts in captured if pid == 'cineby' and path.endswith('global_media_enrichment_v1.py')]
assert ordinary_media, captured
assert not ordinary_media[-1].get('default_user_agent'), ordinary_media[-1]
# media policy must propagate provider-scoped options
