#!/usr/bin/env python3
"""End-to-end contract for both live Nuvio TV provider invocation conventions."""
from __future__ import annotations
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "scripts" / "nuvio_tv_probe_v2.cjs"
FIXTURE = json.dumps({"tmdbId":"46296","mediaType":"tv","season":0,"episode":1,"title":"Spartacus"})
STREAM = "{url:'http://127.0.0.1:1/video.mp4',title:'Spartacus S00E01'}"

def test_provider(script: str, expected_first: str, expected_count: int) -> None:
    with tempfile.TemporaryDirectory(prefix="nuvio-tv-invoke-") as directory:
        path = Path(directory) / "mock-provider.cjs"
        path.write_text(script, encoding="utf-8")
        proc = subprocess.run(["node", str(PROBE), str(path), FIXTURE, "{}"], cwd=ROOT,
                              capture_output=True, text=True, timeout=12, check=False)
        lines = [line for line in proc.stdout.splitlines() if line.startswith("{")]
        assert lines, f"Probe did not report JSON: {proc.stderr[:900]}"
        result = json.loads(lines[-1])
        assert result["raw_stream_count"] == expected_count, result
        assert result.get("runtime_error") is None, result
        attempts = result.get("invocation_diagnostics") or []
        assert attempts and attempts[0]["name"] == expected_first, attempts
        assert attempts[-1]["count"] == expected_count, attempts

test_provider(
    "function native(arg){return arg&&typeof arg==='object'&&arg.season===0?["
    + STREAM + "]:[]}\nmodule.exports={getStreams:async function(){return native.apply(this,arguments)}};\n",
    "positional_with_settings", 1,
)
test_provider(
    "module.exports={getStreams:async function(tmdbId,mediaType,season,episode){"
    "return typeof tmdbId==='string'&&season===0?[" + STREAM + "]:[]}};\n",
    "positional_with_settings", 1,
)
print("FIELD_NUVIO_TV_PROBE_INVOCATION_CONTRACT positional=true object_fallback=true season_zero_preserved=true")
