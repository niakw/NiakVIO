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
hls_runtime_apply = load_apply("scripts/provider_patches/hls_runtime_integrity_v1.py")
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

# Recovery/enrichment must stay inside the final runtime safety guard even when
# patches are reapplied in a different transaction. Otherwise a deterministic
# rematerialization can silently change runtime behavior without changing the
# provider implementation itself.
safety_first = hls_apply(
    base,
    options={"default_user_agent":"UA-STREAMZO"},
    context={"provider_id":"streamzo"},
)
ordered = media_apply(safety_first, options={"default_user_agent":"UA-STREAMZO"})
assert ordered.index("NUVIO_GLOBAL_MEDIA_ENRICHMENT_V1") < ordered.index("NUVIO_GLOBAL_RUNTIME_MEDIA_SAFETY_V1")
assert media_apply(ordered, options={"default_user_agent":"UA-STREAMZO"}) == ordered
changed_context = media_apply(ordered, options={"default_user_agent":"UA-STREAMZO-2"})
assert changed_context.index("NUVIO_GLOBAL_MEDIA_ENRICHMENT_V1") < changed_context.index("NUVIO_GLOBAL_RUNTIME_MEDIA_SAFETY_V1")
assert '"defaultUserAgent":"UA-STREAMZO-2"' in changed_context


# Canonical global playback order is enrichment -> final safety -> final HLS
# graph validation. The HLS layer is intentionally outermost: it must validate
# the final rows after player/embed recovery has attached scoped playback
# context and after the shared safety layer has normalized them. Reapplication
# in any patch order must converge to this one byte-stable representation.
canonical = media_apply(base, options={"default_user_agent":"UA-STREAMZO"})
canonical = hls_apply(canonical, options={"default_user_agent":"UA-STREAMZO"}, context={"provider_id":"streamzo"})
canonical = hls_runtime_apply(canonical, options={"probe_all_urls": True, "fail_closed_unknown": False})
# hls_apply is the final ordering normalizer when all three layers exist.
canonical = hls_apply(canonical, options={"default_user_agent":"UA-STREAMZO"}, context={"provider_id":"streamzo"})
media_pos = canonical.index("NUVIO_GLOBAL_MEDIA_ENRICHMENT_V1")
safety_pos = canonical.index("NUVIO_GLOBAL_RUNTIME_MEDIA_SAFETY_V1")
hls_pos = canonical.index("NUVIO_HLS_RUNTIME_INTEGRITY_V1")
assert media_pos < safety_pos < hls_pos, (media_pos, safety_pos, hls_pos)
canonical_again = hls_runtime_apply(canonical, options={"probe_all_urls": True, "fail_closed_unknown": False})
canonical_again = media_apply(canonical_again, options={"default_user_agent":"UA-STREAMZO"})
canonical_again = hls_apply(canonical_again, options={"default_user_agent":"UA-STREAMZO"}, context={"provider_id":"streamzo"})
assert canonical_again == canonical

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
