#!/usr/bin/env python3
from __future__ import annotations

import base64
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/summarize_native_corpus_suite.cjs"


def b64(value: str) -> str:
    return base64.urlsafe_b64encode(value.encode()).decode().rstrip("=") or "AA"


def result(client: str, fixture: str, provider: str, count: int, duration: int = 1200) -> str:
    return (
        f"FIELD_NATIVE_RESULT client={client} fixture={fixture} provider64={b64(provider)} "
        f"enabled=true duration_ms={duration} count={count}"
    )


def row(client: str, fixture: str, provider: str, title: str, hint: str) -> str:
    return (
        f"FIELD_NATIVE_ROW client={client} fixture={fixture} provider64={b64(provider)} index=0 "
        f"title64={b64(title)} name64={b64(provider)} quality64={b64('HD')} language64={b64('fr')} "
        f"type64={b64('hls')} host64={b64('media.example')} media_hint64={b64(hint)}"
    )


def transport(client: str, fixture: str, provider: str, seconds: float) -> str:
    return (
        f"FIELD_NATIVE_TRANSPORT client={client} fixture={fixture} provider64={b64(provider)} "
        f"state=ok kind=hls status=200 content_type64={b64('application/vnd.apple.mpegurl')} "
        f"extm3u=true duration_seconds={seconds} host64={b64('media.example')} media_hint64={b64('fixture-media')}"
    )


with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    desktop = []
    tv = []

    # Two independent Desktop-positive / TV-empty observations must be grouped
    # into one repeated platform-gap signal for StreamZo.
    for fixture, title, seconds in (
        ("mon-ninja-et-moi-3", "StreamZo - Mon ninja et moi 3", 88 * 60),
        ("interstellar", "StreamZo - Interstellar", 169 * 60),
    ):
        desktop += [
            result("desktop", fixture, "streamzo", 1),
            row("desktop", fixture, "streamzo", title, title),
            transport("desktop", fixture, "streamzo", seconds),
        ]
        tv += [result("tv", fixture, "streamzo", 0)]

    # The same clearly wrong short cartoon returned for two long-form fixtures
    # must become a repeated contradiction, even if the transport itself is HLS.
    for fixture in ("breaking-bad-s01e01", "revenant-s01e01"):
        desktop += [
            result("desktop", fixture, "topcartoons", 1, duration=35000),
            row("desktop", fixture, "topcartoons", "TopCartoons - Tiny Cartoon", "tiny-cartoon-episode"),
            transport("desktop", fixture, "topcartoons", 7 * 60),
        ]

    (root / "desktop-native-corpus-synthetic.log").write_text("\n".join(desktop) + "\n")
    (root / "tv-native-corpus-synthetic.log").write_text("\n".join(tv) + "\n")
    output = root / "summary.json"
    proc = subprocess.run(
        ["node", str(SCRIPT), "--dir", str(root), "--output", str(output)],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0:
        raise AssertionError(proc.stdout + "\n" + proc.stderr)
    data = json.loads(output.read_text())
    signals = data["engineSignals"]
    streamzo_gap = next(
        row for row in signals["repeatedPlatformGaps"]
        if row["provider"].casefold() == "streamzo" and row["targetClient"] == "tv"
    )
    assert streamzo_gap["occurrences"] == 2, streamzo_gap
    topcartoons = next(
        row for row in signals["repeatedContradictions"]
        if row["provider"].casefold() == "topcartoons"
    )
    assert topcartoons["occurrences"] >= 2, topcartoons
    assert data["contradictions"] >= 2, data
    assert "FIELD_NATIVE_ENGINE_SIGNAL" in proc.stdout, proc.stdout

print("native corpus suite summary tests passed")
