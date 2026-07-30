#!/usr/bin/env python3
"""Regression tests for targeted, evidence-gated stream hardening."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from apply_provider_overrides import apply_overrides

LEGACY_MARKERS = (
    b"NUVIO_GLOBAL_STREAM_OUTPUT_GUARD_V1",
    b"NUVIO_GLOBAL_STREAM_OUTPUT_GUARD_V2",
    b"NUVIO_GLOBAL_STREAM_OUTPUT_GUARD_V3",
)
TARGETED = b"NUVIO_STREAM_OUTPUT_RECOVERY_V1"

# Discovery must not wrap every provider. It also removes a previously published
# blanket guard so the next deep can restore app compatibility.
source = b'module.exports={getStreams:function(){return Promise.resolve([{name:"720p VO",url:"https://cdn.example/movie.mp4"}])}};'
discovery, records = apply_overrides("synthetic", source)
assert all(marker not in discovery for marker in LEGACY_MARKERS)
assert TARGETED not in discovery
assert not any(row.get("type") == "patch_profile" for row in records)

legacy = source + b'\n/* NUVIO_GLOBAL_STREAM_OUTPUT_GUARD_V3 */\n;(function(){throw new Error("legacy")})();'
cleaned, clean_records = apply_overrides("synthetic", legacy)
assert all(marker not in cleaned for marker in LEGACY_MARKERS)
assert cleaned.rstrip().endswith(b'};')
assert any(row.get("type") == "global_stream_output_guard" for row in clean_records)

# The same provider can receive the reusable output profile after a matching
# runtime failure. The profile remains Promise-chain-only and preserves the
# provider contract.
patched, profile_records = apply_overrides(
    "synthetic",
    source,
    phase="runtime",
    profile_names=["stream_output_recovery"],
)
assert TARGETED in patched
assert any(row.get("profile") == "stream_output_recovery" for row in profile_records)
profile_text = patched.decode()
guard = profile_text[profile_text.index("NUVIO_STREAM_OUTPUT_RECOVERY_V1"):]
assert "async function" not in guard
assert "await " not in guard
with tempfile.TemporaryDirectory() as td:
    provider = Path(td) / "provider.js"
    provider.write_bytes(patched)
    subprocess.run(["node", "--check", str(provider)], check=True)
    script = f'''const p=require({json.dumps(str(provider))}); Promise.resolve(p.getStreams()).then(x=>console.log(JSON.stringify(x)));'''
    streams = json.loads(subprocess.check_output(["node", "-e", script], text=True).strip())
assert len(streams) == 1
assert streams[0]["quality"] == "720p"
assert streams[0]["language"] == "VO"
assert streams[0]["headers"]["Range"] == "bytes=0-"

# Every published provider is cleanable without blindly injecting a wrapper.
manifest_paths = [ROOT / "manifest.json", ROOT / "vf" / "manifest.json", ROOT / "vo" / "manifest.json", ROOT / "vostfr" / "manifest.json"]
referenced: dict[str, str] = {}
for manifest_path in manifest_paths:
    if not manifest_path.exists():
        continue
    payload = json.loads(manifest_path.read_text())
    for item in payload.get("scrapers", []):
        filename = item.get("filename") or item.get("url") or ""
        if "providers/" not in filename:
            continue
        relative = filename[filename.index("providers/"):].split("?", 1)[0]
        referenced[relative] = str(item.get("id") or Path(relative).stem).casefold()
assert referenced
for relative, provider_id in sorted(referenced.items()):
    provider_path = ROOT / relative
    output, _ = apply_overrides(provider_id, provider_path.read_bytes())
    assert all(marker not in output for marker in LEGACY_MARKERS), relative

print(f"targeted stream output recovery test passed ({len(referenced)} referenced providers cleanable)")
