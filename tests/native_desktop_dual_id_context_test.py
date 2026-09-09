#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "augment_native_desktop_dual_id_context.py"
spec = importlib.util.spec_from_file_location("dual_id_context", MODULE_PATH)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

source = '''package test\n\nfun execute() {\n                evaluate<Any?>(polyfillCode)\n\n                val wrappedCode = """\n                    var module = { exports: {} };\n                """.trimIndent()\n}\n'''

with tempfile.TemporaryDirectory() as td:
    path = Path(td) / "PluginRuntime.kt"
    path.write_text(source, encoding="utf-8")
    changed = mod.augment(path)
    assert changed is True
    text = path.read_text(encoding="utf-8")
    assert text.count(mod.MARKER) == 1
    assert 'System.getenv("NIAKVIO_LAB_IMDB_ID")' in text
    assert '"tmdbId" to JsonPrimitive(tmdbId)' in text
    assert '"imdbId" to JsonPrimitive(labImdbId)' in text
    assert '"tmdbMetadata" to JsonObject(' in text
    assert '"external_ids" to JsonObject(' in text
    assert 'mapOf("imdb_id" to JsonPrimitive(labImdbId))' in text
    assert '"imdb_id" to JsonPrimitive(labImdbId)' in text
    assert 'globalThis.__nuvioMediaContext' in text
    assert "TMDB_API_KEY" not in text
    assert "TMDB_ACCESS_TOKEN" not in text
    before = text
    changed_again = mod.augment(path)
    assert changed_again is False
    assert path.read_text(encoding="utf-8") == before

print("native Desktop dual-ID context contract passed: canonical_tmdb_metadata=true")
