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


def playback(
    client: str,
    fixture: str,
    provider: str,
    *,
    state: str,
    engine: str,
    repair_class: str,
    exo_name: str,
    mpv_state: str = "not_needed",
) -> list[str]:
    attempt = (
        f"FIELD_NATIVE_PLAYBACK client={client} fixture={fixture} provider64={b64(provider)} index=0 "
        f"state={state} engine={engine} repair_class={repair_class} source_status=206 signature=matroska_ebml ranges=true "
        f"content_type64={b64('video/x-matroska')} final_host64={b64('media.example')} "
        f"exo_state={'ready' if engine == 'exo' and state == 'ready' else 'error'} exo_code={0 if exo_name == 'READY' else 3003} "
        f"exo_name={exo_name} exo_cause64={b64('UnrecognizedInputFormatException')} retry_mime64={b64('video/x-matroska')} "
        f"mpv_state={mpv_state} mpv_name={'MPV_READY' if mpv_state == 'ready' else ''} mpv_cause64={b64('')}"
    )
    provider_state = (
        f"FIELD_NATIVE_PLAYBACK_PROVIDER client={client} fixture={fixture} provider64={b64(provider)} "
        f"state={'ready' if state == 'ready' else 'unplayable'}"
    )
    return [attempt, provider_state]


with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    desktop = []
    tv = []

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

    for fixture in ("breaking-bad-s01e01", "revenant-s01e01"):
        desktop += [
            result("desktop", fixture, "topcartoons", 1, duration=35000),
            row("desktop", fixture, "topcartoons", "TopCartoons - Tiny Cartoon", "tiny-cartoon-episode"),
            transport("desktop", fixture, "topcartoons", 7 * 60),
        ]

    # Reader evidence is stronger than a successful HTTP transport. The same
    # Media3 3003 failure on two works must become a repeated repair signal.
    for fixture in ("sinners", "interstellar"):
        tv += [
            result("tv", fixture, "goated", 1),
            row("tv", fixture, "goated", f"GOATED - {fixture}", fixture),
            transport("tv", fixture, "goated", 120 * 60),
            *playback(
                "tv", fixture, "goated",
                state="error", engine="none",
                repair_class="player_container_unsupported",
                exo_name="ERROR_CODE_PARSING_CONTAINER_UNSUPPORTED",
                mpv_state="timeout",
            ),
        ]

    # If Exo fails but MPV opens the same source, the provider is usable through
    # auto-failover but remains an engine-compatibility repair target.
    tv += [
        result("tv", "sinners", "cineby", 1),
        row("tv", "sinners", "cineby", "Cineby - Sinners", "sinners"),
        transport("tv", "sinners", "cineby", 138 * 60),
        *playback(
            "tv", "sinners", "cineby",
            state="ready", engine="mpv",
            repair_class="player_engine_compatibility_gap",
            exo_name="ERROR_CODE_PARSING_CONTAINER_UNSUPPORTED",
            mpv_state="ready",
        ),
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
    assert streamzo_gap["capability"] == "html_scraper", streamzo_gap

    capability_gap = next(
        row for row in data["capabilitySignals"]["platformGaps"]
        if row["capability"] == "html_scraper"
    )
    assert capability_gap["occurrences"] >= 2, capability_gap
    assert "streamzo" in [p.casefold() for p in capability_gap["providers"]], capability_gap

    inventory = {row["capability"]: row for row in data["capabilityInventory"]}
    assert "html_scraper" in inventory, inventory
    assert "streamzo" in [p.casefold() for p in inventory["html_scraper"]["providers"]], inventory

    topcartoons = next(
        row for row in signals["repeatedContradictions"]
        if row["provider"].casefold() == "topcartoons"
    )
    assert topcartoons["occurrences"] >= 2, topcartoons
    assert data["contradictions"] >= 2, data

    player_signal = next(
        row for row in signals["repeatedPlaybackFailures"]
        if row["provider"].casefold() == "goated" and row["repairClass"] == "player_container_unsupported"
    )
    assert player_signal["occurrences"] == 2, player_signal
    assert "ERROR_CODE_PARSING_CONTAINER_UNSUPPORTED" in player_signal["exoCodeNames"], player_signal
    assert data["playbackFailures"] == 2, data
    assert data["exoContainerUnsupported"] == 2, data
    assert data["mpvOnly"] == 1, data

    goated = next(row for row in data["playerFeedback"]["providers"] if row["providerId"] == "goated")
    assert goated["failedAttempts"] == 2, goated
    assert goated["playbackReady"] is False, goated
    cineby = next(row for row in data["playerFeedback"]["providers"] if row["providerId"] == "cineby")
    assert cineby["mpvRecovered"] is True, cineby

    assert "FIELD_NATIVE_ENGINE_SIGNAL" in proc.stdout, proc.stdout
    assert "FIELD_NATIVE_CAPABILITY_SIGNAL" in proc.stdout, proc.stdout

print("native corpus suite summary tests passed")
