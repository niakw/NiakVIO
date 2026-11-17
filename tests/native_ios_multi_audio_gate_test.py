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
WORKFLOW = (ROOT / ".github/workflows/native-mobile-ios-reader.yml").read_text(encoding="utf-8")
RELEASE = (ROOT / ".github/workflows/release-candidate-validation.yml").read_text(encoding="utf-8")
ANALYZER = (ROOT / "scripts/analyze_native_ios_results.py").read_text(encoding="utf-8")

assert "httpGetTextWithHeaders(row.url, row.headers.orEmpty())" in PREPARE
assert "masterAudioTrackCount" in PREPARE
assert "getAudioTrackCount()" in PREPARE
assert PREPARE.index("val player = probeProductionPlayer(row, playerTimeoutMs)") < PREPARE.index(
    "hlsMasterAudioTrackCount(row)"
)
assert "gate_native_ios_multi_audio.py" in SUITE
assert 'MULTI_AUDIO_STATUS=${PIPESTATUS[0]}' in SUITE
assert "certify_multi_audio:" in WORKFLOW
assert "--require-witness" in WORKFLOW
assert "inputs.certify_multi_audio" in WORKFLOW
assert "native-mobile-ios-reader.yml -f 'inputs[mode]=full' -F 'inputs[certify_multi_audio]=true'" in RELEASE
assert '"multi_audio_player_collapsed"' in ANALYZER
assert '"client_runtime" if multi_audio_collapsed else ""' in ANALYZER
assert '"blocking": multi_audio_collapsed' in ANALYZER

def run(rows: list[dict], *, require_witness: bool = False) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as tmp:
        log = Path(tmp) / "ios.log"
        log.write_text(
            "\n".join("FIELD_NATIVE_IOS_PLAYER " + json.dumps(row) for row in rows) + "\n",
            encoding="utf-8",
        )
        command = ["python3", str(GATE), "--log", str(log)]
        if require_witness:
            command.append("--require-witness")
        return subprocess.run(
            command,
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

strict_missing = run([
    {
        "fixture": "interstellar",
        "provider": "example",
        "state": "ready",
        "masterAudioTrackCount": 1,
        "audioTrackCount": 1,
    }
], require_witness=True)
assert strict_missing.returncode == 3, (strict_missing.stdout, strict_missing.stderr)
assert "status=unproven" in strict_missing.stdout
assert "require_witness=true" in strict_missing.stdout

strict_preserved = run([
    {
        "fixture": "interstellar",
        "provider": "example",
        "state": "ready",
        "masterAudioTrackCount": 2,
        "audioTrackCount": 2,
    }
], require_witness=True)
assert strict_preserved.returncode == 0, (strict_preserved.stdout, strict_preserved.stderr)

print("native iOS multi-audio gate contract passed")
