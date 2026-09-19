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
        f"FIELD_NATIVE_TRANSPORT client={client} fixture={fixture} provider64={b64(provider)} index=0 "
        f"state=ok kind=hls status=200 content_type64={b64('application/vnd.apple.mpegurl')} "
        f"extm3u=true duration_seconds={seconds} host64={b64('media.example')} media_hint64={b64('fixture-media')}"
    )


def player(client: str, fixture: str, provider: str, state: str, *, status: int = 0, stage: str = 'none', seconds: float = 0) -> str:
    return (
        f"FIELD_NATIVE_PLAYER client={client} fixture={fixture} provider64={b64(provider)} index=0 "
        f"state={state} engine=media3 http_status={status} failure_stage={stage} duration_seconds={seconds} "
        f"host64={b64('media.example')} error_class64={b64('PlaybackException' if state == 'error' else '')} "
        f"error_code64={b64('ERROR_CODE_IO_BAD_HTTP_STATUS' if status else '')} "
        f"exception_chain64={b64('InvalidResponseCodeException' if status else '')} response_header_names64={b64('content-type,date' if status else '')}"
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

    # Reader evidence must survive the cross-device summary with the exact causal
    # class while remaining sanitized. Two 403s become a repeated reader signal.
    for fixture in ("sinners-2025", "interstellar"):
        tv += [
            result("tv", fixture, "MOVIESDRIVE", 1),
            player("tv", fixture, "MOVIESDRIVE", "error", status=403, stage="http_access"),
        ]
    tv += [
        result("tv", "sinners-2025", "PURSTREAM", 1),
        player("tv", "sinners-2025", "PURSTREAM", "ready", seconds=137 * 60),
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
    assert data["schemaVersion"] >= 3, data
    signals = data["engineSignals"]
    streamzo_gap = next(
        row for row in signals["repeatedPlatformGaps"]
        if row["provider"].casefold() == "streamzo" and row["targetClient"] == "tv"
    )
    assert streamzo_gap["occurrences"] == 2, streamzo_gap
    assert streamzo_gap["capability"] == "mixed_embed_resolver", streamzo_gap

    capability_gap = next(
        row for row in data["capabilitySignals"]["platformGaps"]
        if row["capability"] == "mixed_embed_resolver"
    )
    assert capability_gap["occurrences"] >= 2, capability_gap
    assert "streamzo" in [p.casefold() for p in capability_gap["providers"]], capability_gap

    inventory = {row["capability"]: row for row in data["capabilityInventory"]}
    assert "mixed_embed_resolver" in inventory, inventory
    assert "streamzo" in [p.casefold() for p in inventory["mixed_embed_resolver"]["providers"]], inventory

    topcartoons = next(
        row for row in signals["repeatedContradictions"]
        if row["provider"].casefold() == "topcartoons"
    )
    assert topcartoons["occurrences"] >= 2, topcartoons
    assert data["contradictions"] >= 2, data

    assert data["nativeReaderObserved"] == 3, data
    assert data["nativeReaderHealthy"] == 1, data
    assert data["nativeReaderFailures"] == 2, data
    assert data["readerFailureClasses"]["playback_http_access"] == 2, data
    moviesdrive = next(row for row in data["providerReaderFailures"] if row["provider"] == "moviesdrive")
    assert moviesdrive["occurrences"] == 2, moviesdrive
    repeated_reader = next(row for row in signals["repeatedReaderFailures"] if row["provider"] == "moviesdrive")
    assert repeated_reader["failureClass"] == "playback_http_access", repeated_reader
    assert repeated_reader["occurrences"] == 2, repeated_reader
    assert data["readerPrivacy"].startswith("Sanitized only"), data["readerPrivacy"]

    assert "FIELD_NATIVE_ENGINE_SIGNAL" in proc.stdout, proc.stdout
    assert "FIELD_NATIVE_CAPABILITY_SIGNAL" in proc.stdout, proc.stdout
    assert "FIELD_NATIVE_PLAYER_SUMMARY" in proc.stdout, proc.stdout

print("native corpus suite summary tests passed")