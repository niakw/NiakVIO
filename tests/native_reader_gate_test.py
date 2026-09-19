#!/usr/bin/env python3
from __future__ import annotations

import base64
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT / 'scripts/gate_native_reader_result.cjs'


def b64(value: str) -> str:
    return base64.urlsafe_b64encode(value.encode()).decode().rstrip('=')


def player(state: str, status: int = 0, stage: str = 'none', duration: float = 0.0, index: int = 0) -> str:
    return (
        'FIELD_NATIVE_PLAYER client=tv fixture=sinners-2025 '
        f'provider64={b64("MOVIESDRIVE")} index={index} state={state} engine=media3 '
        f'http_status={status} failure_stage={stage} duration_seconds={duration} '
        f'host64={b64("media.example")} error_class64={b64("PlaybackException" if state == "error" else "")} '
        f'error_code64={b64("ERROR_CODE_IO_BAD_HTTP_STATUS" if status else "")} '
        f'exception_chain64={b64("InvalidResponseCodeException" if status else "")} '
        f'response_header_names64={b64("content-type,date" if status else "")}'
    )


def run(lines: list[str]):
    with tempfile.TemporaryDirectory() as tmp:
        log = Path(tmp) / 'tv-native-corpus-sinners-2025.log'
        log.write_text('\n'.join(lines) + '\n', encoding='utf-8')
        return subprocess.run(['node', str(GATE), str(log)], cwd=ROOT, text=True, capture_output=True)


ok = run([player('ready', duration=137 * 60, index=0), player('ended', duration=137 * 60, index=1)])
assert ok.returncode == 0, (ok.stdout, ok.stderr)
assert 'state=passed' in ok.stdout

for line, expected in (
    (player('error', status=403, stage='http_access'), 'playback_http_access'),
    (player('short_media', stage='duration_identity', duration=20), 'short_media'),
    (player('timeout', stage='timeout'), 'playback_timeout'),
):
    failed = run([player('ready', duration=137 * 60), line])
    assert failed.returncode == 1, (failed.stdout, failed.stderr)
    assert expected in failed.stdout, failed.stdout
    assert 'state=failed' in failed.stdout

missing = run(['FIELD_NATIVE_RESULT client=tv fixture=sinners-2025 provider64=' + b64('MOVIESDRIVE') + ' enabled=true duration_ms=10 count=3'])
assert missing.returncode == 2, (missing.stdout, missing.stderr)
assert 'missing_native_reader_evidence' in missing.stderr

print('native reader strict gate tests passed')
