#!/usr/bin/env python3
from __future__ import annotations

import base64
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT / "scripts/gate_native_stream_extraction.cjs"
PROVIDERS = ("cineby", "VIDEASY", "PURSTREAM")


def b64(value: str) -> str:
    return base64.urlsafe_b64encode(value.encode()).decode().rstrip("=")


def result(provider: str, count: int) -> str:
    return (
        "FIELD_NATIVE_RESULT client=desktop fixture=sinners-2025 "
        f"provider64={b64(provider)} enabled=true duration_ms=10 count={count}"
    )


def sentinel_row(provider: str) -> str:
    marker = "__NIAKVIO_RUNTIME_ERROR__"
    return (
        "FIELD_NATIVE_ROW client=desktop fixture=sinners-2025 "
        f"provider64={b64(provider)} index=0 title64={b64(marker)} name64={b64(marker)} "
        f"quality64={b64('')} language64={b64('')} type64={b64(marker)}"
    )


def run(lines: list[str]) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as raw:
        log = Path(raw) / "native.log"
        log.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return subprocess.run(
            [
                "node",
                str(GATE),
                "--client",
                "desktop",
                "--fixture",
                "sinners-2025",
                "--providers",
                ",".join(PROVIDERS),
                str(log),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )


healthy = run([result("cineby", 2), result("VIDEASY", 0), result("PURSTREAM", 0)])
assert healthy.returncode == 0, healthy.stdout + healthy.stderr
assert "state=passed" in healthy.stdout
assert "positive=1" in healthy.stdout

isolated_runtime = run([
    result("cineby", 1),
    sentinel_row("cineby"),
    result("VIDEASY", 2),
    result("PURSTREAM", 0),
])
assert isolated_runtime.returncode == 0, isolated_runtime.stdout + isolated_runtime.stderr
assert "runtime_errors=1" in isolated_runtime.stdout
assert "positive=1" in isolated_runtime.stdout

all_empty = run([result("cineby", 0), result("VIDEASY", 0), result("PURSTREAM", 0)])
assert all_empty.returncode == 1
assert "reason=no_visible_streams" in all_empty.stderr

systematic_runtime = run([
    result("cineby", 1), sentinel_row("cineby"),
    result("VIDEASY", 1), sentinel_row("VIDEASY"),
    result("PURSTREAM", 1), sentinel_row("PURSTREAM"),
])
assert systematic_runtime.returncode == 1
assert "reason=systematic_runtime_error" in systematic_runtime.stderr
assert "reason=no_visible_streams" in systematic_runtime.stderr

missing = run([result("cineby", 1), result("VIDEASY", 0)])
assert missing.returncode == 1
assert "reason=missing_provider_evidence" in missing.stderr

print("native stream extraction gate passed: real-positive required, runtime sentinel excluded, complete canary evidence required")
