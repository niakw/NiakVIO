#!/usr/bin/env python3
"""The historical presentation fallback migration is a semantic floor, not a rewriter."""

from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts" / "provider_patches" / "global_stream_presentation_v1.py"
MIGRATION = ROOT / "scripts" / "harden_stream_presentation_metadata_fallbacks.py"

before = TARGET.read_bytes()

spec = importlib.util.spec_from_file_location("presentation_metadata_migration", MIGRATION)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

assert module.main() == 0
after = TARGET.read_bytes()
assert after == before, (
    "committed Stream Presentation must already satisfy the metadata fallback "
    "floor; validation may not rewrite current Core bytes"
)

text = after.decode("utf-8")
assert "function cleanProviderLabel(v)" in text
assert "function providerName(r){var raw=cleanProviderLabel(r&&r.name)" in text
assert "function mediaLine(meta,q)" in text
assert "meta&&meaningful(meta.title)" in text
assert "meaningful(q&&q.title)" in text
assert "Unknown" not in text or 'parts.push("Unknown")' not in text
assert "Inconnue" not in text or 'parts.push("Inconnue")' not in text

print("stream presentation metadata migration fixed-point contract passed")
