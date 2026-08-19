#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
module_path = ROOT / "scripts/prepare_native_reader_acceptance.py"
spec = importlib.util.spec_from_file_location("prepare_native_reader_acceptance", module_path)
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)


def source(client: str) -> str:
    return f'''package example\n\nimport android.util.Log\nimport androidx.test.platform.app.InstrumentationRegistry\nimport org.junit.Test\n\nclass Sample {{\n    private fun b64(v: Any?) = ""\n    private fun hostOnly(v: String) = ""\n    private fun probeTransport(url: String, headers: Map<String,String>?) = TODO()\n\n    @Test\n    fun run() {{\n        val fixtureSlug = "sinners-2025"\n        val provider = object {{ val id = "MOVIESDRIVE" }}\n        val rows = emptyList<dynamic>()\n                rows.take(3).forEachIndexed {{ index, row ->\n                    emit("FIELD_NATIVE_ROW client={client} fixture=$fixtureSlug provider64=${{b64(provider.id)}} index=$index")\n                }}\n                rows.firstOrNull()?.let {{ row ->\n                    val probe = probeTransport(row.url, row.headers)\n                    emit("FIELD_NATIVE_TRANSPORT client={client} fixture=$fixtureSlug provider64=${{b64(provider.id)}} state=${{probe.state}} kind=${{probe.kind}} status=${{probe.status}} content_type64=${{b64(probe.contentType)}} extm3u=${{probe.extm3u}} duration_seconds=${{probe.durationSeconds ?: 0.0}} host64=${{b64(probe.host)}} media_hint64=${{b64(probe.mediaHint)}}")\n                }}\n    }}\n    private fun emit(v: String) {{}}\n}}\n'''


out = mod.exhaustive_reader_source(source("tv"), "tv", 137)
assert "rows.take(" not in out
assert out.count("rows.forEachIndexed") >= 2
assert "PlayerPlaybackNetworking.createDataSourceFactory(context, headers)" in out
assert out.index("val reader = probeNativePlayer") < out.index("val transport = probeTransport")

selected = mod.select_providers("manifest.json", "sinners-2025", "fixture")
ids = [str(row["id"]).casefold() for row in selected]
assert ids == ["moviesdrive", "moviesmod", "movieshunt", "4khdhub"], ids
assert "4khdhubnew" not in ids

b64 = lambda value: __import__("base64").urlsafe_b64encode(value.encode()).decode().rstrip("=")
with tempfile.TemporaryDirectory() as tmp:
    log = Path(tmp) / "reader.log"
    lines = [
        "FIELD_NATIVE_CORPUS_BEGIN client=tv fixture=sinners-2025 title64=x providers=1",
        f"FIELD_NATIVE_RESULT client=tv fixture=sinners-2025 provider64={b64('MOVIESDRIVE')} enabled=true duration_ms=1 count=9",
    ]
    for index in range(3):
        lines.append(f"FIELD_NATIVE_PLAYER client=tv fixture=sinners-2025 provider64={b64('MOVIESDRIVE')} index={index} state=error")
    log.write_text("\n".join(lines) + "\n", encoding="utf-8")
    failed = subprocess.run(["node", str(ROOT / "scripts/gate_native_reader_coverage.cjs"), str(log)], cwd=ROOT, text=True, capture_output=True)
    assert failed.returncode == 1, failed.stdout + failed.stderr
    assert "returned=9 played=3" in failed.stdout

    for index in range(3, 9):
        lines.append(f"FIELD_NATIVE_PLAYER client=tv fixture=sinners-2025 provider64={b64('MOVIESDRIVE')} index={index} state=error")
    log.write_text("\n".join(lines) + "\n", encoding="utf-8")
    passed = subprocess.run(["node", str(ROOT / "scripts/gate_native_reader_coverage.cjs"), str(log)], cwd=ROOT, text=True, capture_output=True)
    assert passed.returncode == 0, passed.stdout + passed.stderr
    assert "returned=9 played=9" in passed.stdout

print("exhaustive native reader acceptance tests passed")
