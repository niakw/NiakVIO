#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "augment_native_desktop_runtime_diagnostics.py"

fixture = """class DesktopProbe {
    private fun trapRuntimeErrors(code: String): String = code
    private fun b64(value: Any?): String = ""
    fun execute() {
        val rows = PluginRepository.executeScraper(loadedScraper, tmdbId, requestMediaType, season, episode).getOrThrow()
    }
}
"""

with tempfile.TemporaryDirectory() as tmp:
    target = Path(tmp) / "DesktopProbe.kt"
    target.write_text(fixture, encoding="utf-8")
    proc = subprocess.run(
        ["python3", str(SCRIPT), "--source", str(target)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=20,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    generated = target.read_text(encoding="utf-8")

assert "NIAKVIO_NATIVE_RUNTIME_CONSOLE_CAPTURE_PRE" in generated
assert "NIAKVIO_NATIVE_RUNTIME_CONSOLE_CAPTURE_POST" in generated
assert 'return prelude + "\\n" + code + "\\n" + postlude' in generated
assert generated.index("val prelude =") < generated.index("val postlude =")
assert 'capture("fetch-start"' in generated
assert 'originalFetch: (typeof fetch === "function") ? fetch' in generated
assert 'try { fetch = diagnosticFetch; } catch (_) {}' in generated
assert 'try { fetch = state.originalFetch; } catch (_) {}' in generated
assert "__NIAKVIO_RUNTIME_DIAG_STATE__" in generated
assert "diagnostic_nonempty" in generated
assert 'private fun captureRuntimeConsole(code: String): String = code + """' not in generated

print("native Desktop runtime diagnostics order contract passed")
