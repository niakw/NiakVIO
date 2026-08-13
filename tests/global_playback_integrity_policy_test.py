#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

spec = importlib.util.spec_from_file_location(
    "apply_provider_overrides",
    ROOT / "scripts/apply_provider_overrides.py",
)
if not spec or not spec.loader:
    raise RuntimeError("cannot import apply_provider_overrides")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

cfg = json.loads((ROOT / "provider-overrides.json").read_text(encoding="utf-8"))
policy = cfg.get("playback_integrity_policy") or {}
assert policy.get("version") == 3
assert policy.get("enabled") is True
assert policy.get("provider_disabling_is_not_a_repair") is True
assert policy.get("global_discovery_hooks") == [
    "scripts/provider_patches/hls_master_audio_preserver_v1.py",
    "scripts/provider_patches/hls_runtime_integrity_v1.py",
]

# The global hooks must not be duplicated into today's provider script lists. A
# provider may only tighten their global options; newly discovered providers
# still receive the common protection automatically.
for provider_id, row in (cfg.get("provider_patches") or {}).items():
    if not isinstance(row, dict):
        continue
    scripts = row.get("patch_scripts") or []
    assert "scripts/provider_patches/hls_master_audio_preserver_v1.py" not in scripts, provider_id
    assert "scripts/provider_patches/hls_runtime_integrity_v1.py" not in scripts, provider_id
    options = row.get("patch_script_options") or {}
    hls_options = options.get("scripts/provider_patches/hls_runtime_integrity_v1.py")
    if hls_options is not None:
        assert isinstance(hls_options, dict), provider_id

streamzo_hls_options = cfg["provider_patches"]["streamzo"]["patch_script_options"][
    "scripts/provider_patches/hls_runtime_integrity_v1.py"
]
assert streamzo_hls_options["probe_all_urls"] is True
assert streamzo_hls_options["fail_closed_unknown"] is True

future = b'''\nasync function helper(t){let x=await fetch(t.url).then(r=>r.text());if(!/#EXT-X-STREAM-INF/i.test(x))return [{url:t.url,type:"hls"}];return []}\nglobalThis.getStreams=async function(){return [{url:"https://media.example/master.m3u8",type:"hls"}]};\n'''
patched, records = module.apply_overrides("future-provider-never-seen-before", future, phase="discovery")
text = patched.decode("utf-8")
assert "NUVIO_HLS_MASTER_AUDIO_PRESERVER_V1" in text
assert "NUVIO_HLS_RUNTIME_INTEGRITY_V1" in text
paths = {str(row.get("path")) for row in records if isinstance(row, dict)}
assert "scripts/provider_patches/hls_master_audio_preserver_v1.py" in paths
assert "scripts/provider_patches/hls_runtime_integrity_v1.py" in paths
assert any(row.get("scope") == "global_playback_integrity" for row in records if isinstance(row, dict))

# Runtime repair phase must not inject discovery wrappers.
runtime, runtime_records = module.apply_overrides("future-provider-never-seen-before", future, phase="runtime")
assert b"NUVIO_HLS_RUNTIME_INTEGRITY_V1" not in runtime
assert not any(row.get("scope") == "global_playback_integrity" for row in runtime_records if isinstance(row, dict))

health_cfg = json.loads((ROOT / "health-config.json").read_text(encoding="utf-8"))
for mode in ("availability", "retry", "deep"):
    assert health_cfg["modes"][mode]["probe_best_variant"] is True, mode
    assert health_cfg["modes"][mode]["probe_first_segment"] is True, mode

health_source = (ROOT / "scripts/health_check.mjs").read_text(encoding="utf-8")
for marker in (
    "const structurallyPlayable = variants.length > 0",
    "audioTracks.push({",
    "audio_manifest_reachable",
    "audio_segment_reachable",
    "master.audioTracks.length ? audioSegmentReachable === true",
):
    assert marker in health_source, marker

print("global playback integrity policy tests passed")
