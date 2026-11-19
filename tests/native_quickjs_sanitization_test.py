#!/usr/bin/env python3
"""TV QuickJS diagnoses are generated from transient logcat without secrets."""
from __future__ import annotations
import importlib.util
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/sanitize_native_plugin_console.py"
spec = importlib.util.spec_from_file_location("quickjs_sanitizer", SCRIPT)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

P = "french-manga"
FIXTURE = "jujutsu-kaisen-s01e01"
lines = [
    "D/Plugin:repo:FRENCH-MANGA( 5294): Calling getStreams with tmdbId=95479 type=anime s=1 e=1",
    "D/Plugin:repo:FRENCH-MANGA( 5294): getStreams returned: 0 streams",
    "E/Plugin:repo:FRENCH-MANGA( 5294): getStreams error: ReferenceError: secret=value https://private.example/?token=SECRET",
    "E/Plugin:repo:FRENCH-MANGA( 5294): getStreams error: NetworkError URL https://private.example/?Authorization=SECRET",
    "D/Plugin:other( 5294): Calling getStreams with tmdbId=95479 type=anime",
    "D/Plugin:repo:FRENCH-MANGA( 5294): unrelated console output https://secret.example",
]
expected = ["call", "result", "error", "error", None, None]
observed = [mod.extract_line(line, P, FIXTURE) for line in lines]
assert [x["phase"] if x else None for x in observed] == expected, observed
assert observed[0]["requestType"] == "anime"
assert observed[1]["count"] == "0"
assert observed[2]["category"] == "reference_error"
assert observed[3]["category"] == "network_error"

def run(payload: str) -> str:
    child = subprocess.run(
        [sys.executable, str(SCRIPT), "--provider", P, "--fixture", FIXTURE, "--client", "tv"],
        input=payload, text=True, capture_output=True, timeout=5,
    )
    assert child.returncode == 0, child.stderr
    return child.stdout

wire = run("\n".join(lines) + "\n")
assert wire.count("FIELD_NATIVE_QUICKJS_DIAGNOSTIC client=tv") == 4
assert "events=4 raw_content_logged=false proof_authority=false" in wire
assert "category=reference_error" in wire
for forbidden in ("https://", "SECRET", "token=", "Authorization", "95479", "private.example"):
    assert forbidden not in wire, forbidden
for invalid in ("FRENCH MANGA", "../french-manga", "french-manga?token=secret"):
    child = subprocess.run(
        [sys.executable, str(SCRIPT), "--provider", invalid,
         "--fixture", FIXTURE, "--client", "tv"],
        input="",
        text=True, capture_output=True, timeout=5,
    )
    assert child.returncode != 0, invalid

empty = run("")
assert "events=0" in empty and "FIELD_NATIVE_QUICKJS_DIAGNOSTIC client=tv" not in empty
limit = run((lines[1] + "\n") * 105)
assert limit.count("FIELD_NATIVE_QUICKJS_DIAGNOSTIC client=tv") == 100
runner = (ROOT / "scripts/run_native_corpus_tv_suite.sh").read_text()
assert 'sanitize_native_plugin_console.py' in runner
assert 'adb logcat -d -v brief' in runner
assert '>> "$LOG"' in runner
assert 'raw_content_logged=false' in runner
print("Native QuickJS console sanitizer strips all raw media URLs and messages")
