#!/usr/bin/env python3
from __future__ import annotations

import base64
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "analyze_native_corpus_results.cjs"


def b64(value: str) -> str:
    return base64.urlsafe_b64encode(value.encode()).decode().rstrip("=") or "AA"


def html_log(provider: str) -> str:
    return "\n".join(
        [
            f"FIELD_NATIVE_RESULT client=tv fixture=interstellar provider64={b64(provider)} enabled=true duration_ms=1200 count=1",
            (
                f"FIELD_NATIVE_ROW client=tv fixture=interstellar provider64={b64(provider)} index=0 "
                f"title64={b64(provider + ' - Interstellar')} name64={b64(provider)} "
                f"quality64={b64('HD')} language64={b64('')} type64={b64('embed')} "
                f"host64={b64('player.example')} media_hint64={b64('interstellar-player')}"
            ),
            (
                f"FIELD_NATIVE_TRANSPORT client=tv fixture=interstellar provider64={b64(provider)} "
                f"state=dead kind=html status=200 content_type64={b64('text/html')} extm3u=false "
                f"duration_seconds=0 host64={b64('player.example')} media_hint64={b64('interstellar-player')}"
            ),
        ]
    ) + "\n"


with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)

    # VidFast is explicitly an iframe_player. A reachable embed page is its
    # intended terminal contract and must not be misclassified as dead media.
    vidfast_log = root / "tv-native-corpus-vidfast.log"
    vidfast_log.write_text(html_log("vidfast"), encoding="utf-8")
    vidfast = subprocess.run(
        ["node", str(SCRIPT), "interstellar", str(vidfast_log)],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    assert vidfast.returncode == 0, vidfast.stdout + "\n" + vidfast.stderr
    assert "FIELD_NATIVE_EXPECTED_EMBED" in vidfast.stdout, vidfast.stdout
    assert '"transportExpectedEmbeds":1' in vidfast.stdout, vidfast.stdout
    assert '"transportFailures":0' in vidfast.stdout, vidfast.stdout

    # StreamZo is a normal html_scraper whose repaired contract is
    # site -> player -> final media. Returning only HTML must remain blocking,
    # especially on Android TV.
    streamzo_log = root / "tv-native-corpus-streamzo.log"
    streamzo_log.write_text(html_log("streamzo"), encoding="utf-8")
    streamzo = subprocess.run(
        ["node", str(SCRIPT), "interstellar", str(streamzo_log)],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    assert streamzo.returncode != 0, streamzo.stdout
    assert "FIELD_NATIVE_TRANSPORT_FAILURE" in streamzo.stdout, streamzo.stdout
    assert "FIELD_NATIVE_EXPECTED_EMBED" not in streamzo.stdout, streamzo.stdout
    assert '"transportFailures":1' in streamzo.stdout, streamzo.stdout

print("native corpus transport capability tests passed")
