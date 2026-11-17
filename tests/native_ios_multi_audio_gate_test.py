#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT / "scripts/gate_native_ios_multi_audio.py"
PREPARE = (ROOT / "scripts/prepare_native_ios_reader_acceptance.py").read_text(encoding="utf-8")
SUITE = (ROOT / "scripts/run_native_corpus_ios_suite.sh").read_text(encoding="utf-8")
ANALYZER = (ROOT / "scripts/analyze_native_ios_results.py").read_text(encoding="utf-8")

assert "httpGetTextWithHeaders(row.url, row.headers.orEmpty())" in PREPARE
assert "masterAudioTrackCount" in PREPARE
assert "getAudioTrackCount()" in PREPARE
assert PREPARE.index("val player = probeProductionPlayer(row, playerTimeoutMs)") < PREPARE.index(
    "hlsMasterAudioTrackCount(row)"
)
assert "gate_native_ios_multi_audio.py" in SUITE
assert 'MULTI_AUDIO_STATUS=${PIPESTATUS[0]}' in SUITE
assert '"multi_audio_player_collapsed"' in ANALYZER
assert '"client_runtime" if multi_audio_collapsed else ""' in ANALYZER
assert '"blocking": multi_audio_collapsed' in ANALYZER

def run(rows: list[dict]) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as tmp:
        log = Path(tmp) / "ios.log"
        log.write_text(
            "\n".join("FIELD_NATIVE_IOS_PLAYER " + json.dumps(row) for row in rows) + "\n",
            encoding="utf-8",
        )
        return subprocess.run(
            ["python3", str(GATE), "--log", str(log)],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )

collapsed = run([
    {
        "fixture": "interstellar",
        "provider": "example",
        "state": "ready",
        "masterAudioTrackCount": 2,
        "audioTrackCount": 1,
    }
])
assert collapsed.returncode == 2, (collapsed.stdout, collapsed.stderr)
assert "status=fail" in collapsed.stdout
assert "master=2:player=1" in collapsed.stdout

preserved = run([
    {
        "fixture": "interstellar",
        "provider": "example",
        "state": "ready",
        "masterAudioTrackCount": 2,
        "audioTrackCount": 2,
    }
])
assert preserved.returncode == 0, (preserved.stdout, preserved.stderr)
assert "expected=1 verified=1 collapsed=0" in preserved.stdout

single = run([
    {
        "fixture": "interstellar",
        "provider": "example",
        "state": "ready",
        "masterAudioTrackCount": 1,
        "audioTrackCount": 1,
    }
])
assert single.returncode == 0, (single.stdout, single.stderr)
assert "expected=0 verified=0 collapsed=0" in single.stdout

print("native iOS multi-audio gate contract passed")
