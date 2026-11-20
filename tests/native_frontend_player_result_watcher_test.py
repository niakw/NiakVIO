#!/usr/bin/env python3
"""Native frontend screenshot phase must be attached to the actual player result.

The old wildcard FIELD_NATIVE_PLAYER* fired on _ENTRY before the player was
ready. It produced a misleading "player-result" image of the login/splash UI
even though the final reader event was emitted much later. A ready-state
screenshot is only evidence when captured *after* the exact terminal marker.
"""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
WATCHER = ROOT / "scripts/watch_native_device_frontend.sh"
code = WATCHER.read_text(encoding="utf-8")
assert '*"FIELD_NATIVE_PLAYER "*) capture_once "player-result"' in code
assert "*FIELD_NATIVE_PLAYER*) capture_once" not in code


def observed(events: list[str]) -> list[str]:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        bin_dir = root / "bin"
        bin_dir.mkdir()
        adb = bin_dir / "adb"
        adb.write_text(
            '#!/usr/bin/env bash\n'
            'set -euo pipefail\n'
            'test "$1" = "logcat"\n'
            'printf "%s\\n" "$NIAKVIO_FAKE_LOGCAT"\n',
            encoding="utf-8",
        )
        adb.chmod(0o755)
        capture = root / "capture.sh"
        capture.write_text(
            '#!/usr/bin/env bash\n'
            'set -euo pipefail\n'
            'printf "%s\\n" "$2" >> "$3/observed.txt"\n',
            encoding="utf-8",
        )
        capture.chmod(0o755)
        env = os.environ.copy()
        env["PATH"] = str(bin_dir) + os.pathsep + env.get("PATH", "")
        env["NIAKVIO_FAKE_LOGCAT"] = "\n".join(events)
        result = subprocess.run(
            ["bash", str(WATCHER), "tv", str(root), str(capture)],
            env=env, capture_output=True, text=True, timeout=8,
        )
        assert result.returncode == 0, (result.stdout, result.stderr)
        out = root / "observed.txt"
        return out.read_text(encoding="utf-8").splitlines() if out.exists() else []


entry = "I/NiakvioCorpus: FIELD_NATIVE_PLAYER_ENTRY client=tv index=0 entry=nuvio-production-player"
begin = "I/NiakvioCorpus: FIELD_NATIVE_PLAYER_BEGIN client=tv index=0"
actual = "I/NiakvioCorpus: FIELD_NATIVE_PLAYER client=tv index=0 state=ready engine=nuvio-tv-production"
fail = "I/NiakvioCorpus: FIELD_NATIVE_PLAYER client=tv index=0 state=error engine=nuvio-tv-production"
assert observed([entry]) == [], "player entry is not a terminal screenshot"
assert observed([begin]) == ["player-start"], "begin is not a result"
assert observed([actual]) == ["player-result"], "only a terminal field permits result"
assert observed([entry, begin, actual]) == ["player-start", "player-result"]
visible = "I/NiakvioCorpus: FIELD_NATIVE_PLAYER_VISUAL_READY client=tv video_width=864 video_height=488 proof_authority=false"
assert observed([visible]) == ["player-visible"]
assert observed([entry, begin, visible, actual]) == ["player-start", "player-visible", "player-result"]
assert observed([entry, fail]) == ["player-result"], "failed player still needs a terminal screenshot"
assert observed([entry, begin, entry, begin, actual, actual]) == [
    "player-start", "player-result"
], "one screenshot per actual phase"
print("Native frontend watcher exact PLAYER vs ENTRY/BEGIN screenshot timing contract passed")
