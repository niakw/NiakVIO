#!/usr/bin/env python3
"""NuvioTV probe proof authority matches the official four-argument runtime ABI."""
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "scripts" / "nuvio_tv_probe_v2.cjs"
FIXTURE = json.dumps({"tmdbId":"46296","mediaType":"tv","season":0,"episode":1,"title":"Spartacus"})
STREAM = "{url:'http://127.0.0.1:1/video.mp4',title:'Spartacus S00E01'}"


def run_provider(script: str) -> dict:
    with tempfile.TemporaryDirectory(prefix="nuvio-tv-invoke-") as directory:
        path = Path(directory) / "mock-provider.cjs"
        path.write_text(script, encoding="utf-8")
        proc = subprocess.run(
            ["node", str(PROBE), str(path), FIXTURE, "{}"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=12,
            check=False,
        )
        lines = [line for line in proc.stdout.splitlines() if line.startswith("{")]
        assert lines, f"Probe did not report JSON: {proc.stderr[:900]}"
        return json.loads(lines[-1])


# This is the exact NuvioTV call surface from PluginRuntime.kt:
# getStreams(tmdbId, mediaType, season, episode). Season zero must survive.
positional = run_provider(
    "module.exports={getStreams:async function(tmdbId,mediaType,season,episode){"
    "return typeof tmdbId==='string'&&mediaType==='tv'&&season===0?["
    + STREAM + "]:[]}};\n"
)
assert positional["raw_stream_count"] == 1, positional
assert positional.get("runtime_error") is None, positional
assert positional.get("invocation_authoritative") is True, positional
positional_attempts = positional.get("invocation_diagnostics") or []
assert positional_attempts[0]["name"] == "nuvio_tv_positional", positional_attempts
assert positional_attempts[0]["authoritative"] is True, positional_attempts
assert positional_attempts[0]["count"] == 1, positional_attempts

# Object-style ProviderBase compatibility may remain useful as diagnostic
# evidence, but official NuvioTV never invokes this shape. It must not be able
# to turn a TV result into compatibility/playback proof.
object_only = run_provider(
    "module.exports={getStreams:async function(arg){"
    "return arg&&typeof arg==='object'&&arg.season===0?["
    + STREAM + "]:[]}};\n"
)
assert object_only["raw_stream_count"] == 1, object_only
assert object_only.get("runtime_error") is None, object_only
assert object_only.get("invocation_authoritative") is False, object_only
object_attempts = object_only.get("invocation_diagnostics") or []
assert object_attempts[0]["name"] == "nuvio_tv_positional", object_attempts
assert object_attempts[0]["authoritative"] is True, object_attempts
assert object_attempts[0]["count"] == 0, object_attempts
assert any(
    row.get("name") == "diagnostic_object"
    and row.get("authoritative") is False
    and row.get("count") == 1
    for row in object_attempts
), object_attempts

print(
    "FIELD_NUVIO_TV_PROBE_INVOCATION_CONTRACT "
    "positional_authority=true diagnostic_object_non_authoritative=true season_zero_preserved=true"
)
